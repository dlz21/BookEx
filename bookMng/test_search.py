from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Book


class BookSearchTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.seller = get_user_model().objects.create_user(username='ReaderAlice')
        cls.django = Book.objects.create(
            name='Learning Django', price='25.00', username=cls.seller,
            picture='bookEx/static/uploads/django.jpeg',
        )
        cls.python = Book.objects.create(
            name='Python Basics', price='10.50', username=cls.seller, picture='',
        )
        Book.objects.create(name='Another book', price='3.00', picture='')

    def search(self, **params):
        return self.client.get(reverse('search_books'), params)

    def test_initial_blank_and_no_results_states(self):
        for query in ('', '   '):
            response = self.search(q=query)
            self.assertContains(response, 'Your next chapter starts here')
            self.assertEqual(response.context['page_obj'].paginator.count, 0)
        response = self.search(q='unmatched title')
        self.assertContains(response, 'No books found')
        self.assertContains(response, 'Clear search')

    def test_title_and_seller_matching_are_case_insensitive_and_trimmed(self):
        response = self.search(q='  DJANGO  ')
        self.assertEqual(list(response.context['books']), [self.django])
        self.assertEqual(response.context['query'], 'DJANGO')
        response = self.search(q='readeralice', sort='price_asc')
        self.assertEqual(list(response.context['books']), [self.python, self.django])
        self.assertContains(response, 'No cover available')
        self.assertContains(response, reverse('book_detail', args=[self.python.pk]))
        self.assertContains(response, '$10.50')

    @override_settings(STATIC_URL='/assets/')
    def test_legacy_cover_uses_configured_static_url(self):
        self.assertContains(self.search(q='Django'), 'src="/assets/uploads/django.jpeg"')

    @override_settings(MEDIA_URL='/media/')
    def test_other_cover_paths_use_storage_url(self):
        self.django.picture = 'covers/new-cover.jpg'
        self.django.save()
        self.assertContains(self.search(q='Django'), 'src="/media/covers/new-cover.jpg"')

    def test_sort_options_and_invalid_sort_fallback(self):
        for sort, expected in (
            ('price_asc', [self.python, self.django]),
            ('price_desc', [self.django, self.python]),
            ('title', [self.django, self.python]),
            ('newest', [self.python, self.django]),
            ('invalid', [self.python, self.django]),
        ):
            with self.subTest(sort=sort):
                self.assertEqual(list(self.search(q='ReaderAlice', sort=sort).context['books']), expected)

    def test_pagination_preserves_query_and_sort_and_handles_invalid_page(self):
        Book.objects.bulk_create([
            Book(name=f'Books & more {i:02}', price=i, picture='') for i in range(15)
        ])
        response = self.search(q='Books & more', sort='price_asc')
        self.assertEqual(len(response.context['books']), 12)
        self.assertContains(response, 'Showing 1–12')
        self.assertContains(response, 'q=Books%20%26%20more&amp;sort=price_asc&amp;page=2')
        response = self.search(q='Books & more', sort='price_asc', page=2)
        self.assertEqual(len(response.context['books']), 3)
        self.assertContains(response, 'Page 2 of 2')
        self.assertEqual(self.search(q='Books & more', page='bad').context['page_obj'].number, 1)
        self.assertEqual(self.search(q='Books & more', page='999').context['page_obj'].number, 2)

    def test_query_is_escaped(self):
        response = self.search(q='<script>alert("x")</script>')
        self.assertContains(response, '&lt;script&gt;')
        self.assertNotContains(response, '<script>alert(')

    def test_result_details_work_without_cover_and_missing_book_returns_404(self):
        response = self.client.get(reverse('book_detail', args=[self.python.pk]))
        self.assertContains(response, 'No cover available')
        self.assertContains(response, self.python.name)
        self.assertEqual(self.client.get(reverse('book_detail', args=[99999])).status_code, 404)

    def test_default_navigation_includes_search(self):
        self.assertContains(self.search(), 'href="/search/" aria-current="page">Search</a>')
