from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .models import Book, Favorite, MainMenu


class FavoriteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = get_user_model().objects.create_user(username='alice')
        cls.bob = get_user_model().objects.create_user(username='bob')
        cls.book = Book.objects.create(name='Django & books', price='12.00',
                                      username=cls.alice, picture='')

    def setUp(self):
        self.client.force_login(self.alice)
        self.url = reverse('set_favorite', args=[self.book.pk])

    def test_add_remove_and_repeated_submissions_are_idempotent(self):
        for _ in range(2):
            response = self.client.post(self.url, {'action': 'add'})
            self.assertRedirects(response, reverse('favorites'))
            self.assertEqual(Favorite.objects.filter(user=self.alice, book=self.book).count(), 1)
        for _ in range(2):
            self.assertRedirects(self.client.post(self.url, {'action': 'remove'}), reverse('favorites'))
            self.assertFalse(Favorite.objects.exists())
        self.assertTrue(Book.objects.filter(pk=self.book.pk).exists())

    def test_favorites_are_private_and_removal_ignores_submitted_user(self):
        Favorite.objects.create(user=self.bob, book=self.book)
        self.assertContains(self.client.get(reverse('favorites')), 'No favorites yet')
        self.client.post(self.url, {'action': 'add', 'user': self.bob.pk})
        self.assertEqual(Favorite.objects.count(), 2)
        self.client.post(self.url, {'action': 'remove', 'user': self.bob.pk})
        self.assertEqual(list(Favorite.objects.values_list('user_id', flat=True)), [self.bob.pk])

    def test_anonymous_list_and_mutation_require_login(self):
        self.client.logout()
        for url in (reverse('favorites'), self.url):
            response = self.client.get(url) if url == reverse('favorites') else self.client.post(url, {'action': 'add'})
            self.assertRedirects(response, reverse('login') + '?next=' + url)
        self.assertFalse(Favorite.objects.exists())
        response = self.client.get(reverse('book_detail', args=[self.book.pk]))
        self.assertContains(response, 'Log in to favorite')
        self.assertNotContains(response, 'name="action"')

    def test_mutation_requires_post_and_csrf(self):
        for method in ('get', 'head', 'put', 'delete'):
            self.assertEqual(getattr(self.client, method)(self.url).status_code, 405)
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.alice)
        self.assertEqual(client.post(self.url, {'action': 'add'}).status_code, 403)
        client.get(reverse('book_detail', args=[self.book.pk]))
        response = client.post(self.url, {'action': 'add',
                                        'csrfmiddlewaretoken': client.cookies['csrftoken'].value})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Favorite.objects.filter(user=self.alice).exists())

    def test_invalid_action_and_missing_book_do_not_mutate(self):
        for action in (None, 'toggle', ''):
            self.assertEqual(self.client.post(self.url, {'action': action or ''}).status_code, 400)
        self.assertEqual(self.client.post(reverse('set_favorite', args=[999999]),
                                          {'action': 'add'}).status_code, 404)
        self.assertFalse(Favorite.objects.exists())

    def test_return_to_search_preserves_filters_and_page(self):
        destination = reverse('search_books') + '?q=Django%20%26%20books&sort=title&page=2'
        response = self.client.post(self.url, {'action': 'add', 'next': destination})
        self.assertRedirects(response, destination, fetch_redirect_response=False)

    def test_unsafe_redirects_fall_back_to_favorites(self):
        for destination in ('https://evil.example/', '//evil.example/', 'javascript:alert(1)',
                            'http://testserver/favorites/'):
            with self.subTest(destination=destination):
                response = self.client.post(self.url, {'action': 'add', 'next': destination}, secure=True)
                self.assertRedirects(response, reverse('favorites'))

    def test_database_prevents_duplicates_and_cascades_book_deletion(self):
        Favorite.objects.create(user=self.alice, book=self.book)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Favorite.objects.create(user=self.alice, book=self.book)
        self.book.delete()
        self.assertFalse(Favorite.objects.exists())

    def test_user_deletion_cascades_favorites(self):
        Favorite.objects.create(user=self.bob, book=self.book)
        self.bob.delete()
        self.assertFalse(Favorite.objects.exists())
        self.assertTrue(Book.objects.filter(pk=self.book.pk).exists())

    def test_table_lists_only_current_users_books_with_escaped_titles_and_fallbacks(self):
        self.book.name = '<script>book</script>'
        self.book.save()
        Favorite.objects.create(user=self.alice, book=self.book)
        hidden = Book.objects.create(name='Private favorite', price=1, picture='')
        Favorite.objects.create(user=self.bob, book=hidden)
        response = self.client.get(reverse('favorites'))
        self.assertEqual(list(response.context['books']), [self.book])
        for text in ('<th class="pf-v6-c-table__th" scope="col">Seller</th>',
                     'No cover available', '&lt;script&gt;book&lt;/script&gt;', 'alice',
                     reverse('book_detail', args=[self.book.pk]), 'aria-pressed="true"'):
            self.assertContains(response, text)
        self.assertNotContains(response, '<script>book</script>')
        self.assertNotContains(response, 'Private favorite')
        self.client.post(self.url, {'action': 'remove'})
        self.assertContains(self.client.get(reverse('favorites')), 'No favorites yet')

    @override_settings(STATIC_URL='/assets/')
    def test_cover_and_missing_seller_and_title_order(self):
        self.book.picture = 'bookEx/static/uploads/cover.jpg'
        self.book.save()
        first = Book.objects.create(name='A book', price=1, picture='')
        for book in (self.book, first):
            Favorite.objects.create(user=self.alice, book=book)
        response = self.client.get(reverse('favorites'))
        self.assertEqual(list(response.context['books']), [first, self.book])
        self.assertContains(response, 'src="/assets/uploads/cover.jpg"')
        self.assertContains(response, 'Unavailable')

    def test_buttons_reflect_current_users_state_on_all_book_pages(self):
        pages = (reverse('displaybooks'), reverse('mybooks'),
                 reverse('book_detail', args=[self.book.pk]), reverse('search_books') + '?q=Django')
        Favorite.objects.create(user=self.bob, book=self.book)
        for favorite in (False, True):
            if favorite:
                self.client.post(self.url, {'action': 'add'})
            for url in pages:
                with self.subTest(url=url, favorite=favorite):
                    response = self.client.get(url)
                    self.assertContains(response, f'action="{self.url}"')
                    self.assertContains(response, f'aria-pressed="{str(favorite).lower()}"')
                    self.assertContains(response, 'name="action" value="remove"' if favorite else 'name="action" value="add"')
                    self.assertContains(response, 'csrfmiddlewaretoken')
                    self.assertContains(response, 'class="pf-v6-svg"')

    def test_menu_includes_favorites_once_with_custom_and_legacy_records(self):
        for setup in ('default', 'custom', 'legacy'):
            if setup == 'custom':
                MainMenu.objects.create(item='Help', link='help/')
            if setup == 'legacy':
                MainMenu.objects.create(item='Saved books', link='favorites/')
            response = self.client.get(reverse('favorites'))
            self.assertContains(response, 'href="/favorites/" aria-current="page"', count=1)

    def test_list_query_count_does_not_grow_per_book(self):
        Favorite.objects.create(user=self.alice, book=self.book)
        with self.assertNumQueries(4):
            self.client.get(reverse('favorites'))
        for i in range(5):
            book = Book.objects.create(name=f'Book {i}', price=1, picture='', username=self.bob)
            Favorite.objects.create(user=self.alice, book=book)
        with self.assertNumQueries(4):
            self.client.get(reverse('favorites'))
