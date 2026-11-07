import os
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory
from unittest import skipUnless

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .models import Book, MainMenu, MessageThread


class MessagingLoginRedirectTests(TestCase):
    def test_anonymous_messaging_routes_redirect_to_existing_login(self):
        routes = (
            ("inbox", {}),
            ("compose_message", {}),
            ("thread_detail", {"thread_id": 1}),
            ("mark_thread_read", {"thread_id": 1}),
        )
        for name, kwargs in routes:
            with self.subTest(route=name):
                url = reverse(name, kwargs=kwargs)
                response = self.client.get(url)
                self.assertRedirects(response, reverse("login") + "?next=" + url)

    def test_login_returns_anonymous_inbox_visitor_to_inbox(self):
        get_user_model().objects.create_user(
            username="inbox-visitor", password="Test-password-293!"
        )
        response = self.client.get(reverse("inbox"), follow=True)
        self.assertContains(response, 'name="next" value="/inbox/"')
        response = self.client.post(reverse("login"), {
            "username": "inbox-visitor", "password": "Test-password-293!",
            "next": reverse("inbox"),
        }, follow=True)
        self.assertRedirects(response, reverse("inbox"))
        self.assertTemplateUsed(response, "bookMng/inbox.html")


class NavigationRoutingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username="menu-user")
        cls.other = get_user_model().objects.create_user(username="other-user")
        MainMenu.objects.create(item="Inbox", link="inbox/")
        MainMenu.objects.create(item="Compose Message", link="compose/")

    def assert_messaging_links(self, response):
        self.assertEqual(response.status_code, 200)
        for label, route in (("Inbox", "inbox"), ("Compose Message", "compose_message")):
            self.assertInHTML(
                f'<a href="{reverse(route)}">{label}</a>', response.content.decode()
            )

    def test_anonymous_mybooks_redirects_to_login(self):
        response = self.client.get(reverse("mybooks"))
        self.assertRedirects(response, reverse("login") + "?next=" + reverse("mybooks"))

    def test_authenticated_mybooks_only_lists_own_books(self):
        own = Book.objects.create(name="Own book", price="1.00", username=self.user,
                                  picture="bookEx/static/uploads/own.gif")
        Book.objects.create(name="Other book", price="2.00", username=self.other,
                            picture="bookEx/static/uploads/other.gif")
        self.client.force_login(self.user)
        response = self.client.get(reverse("mybooks"))
        self.assertQuerySetEqual(response.context["books"], [own])

    def test_sidebar_links_work_from_home_compose_inbox_and_thread(self):
        self.assert_messaging_links(self.client.get(reverse("index")))
        self.client.force_login(self.user)
        thread = MessageThread.get_or_create_thread(self.user, self.other)
        for url in (reverse("compose_message"), reverse("inbox"),
                    reverse("thread_detail", args=[thread.pk])):
            with self.subTest(url=url):
                self.assert_messaging_links(self.client.get(url))

    def test_invalid_compose_preserves_sidebar(self):
        self.client.force_login(self.user)
        for data in ({"body": "Missing recipient"}, {"user_id": self.other.pk, "body": ""}):
            with self.subTest(data=data):
                self.assert_messaging_links(self.client.post(reverse("compose_message"), data))


class PatternFlyFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="prototype", password="Test-password-293!"
        )

    def test_login_preserves_password_and_next(self):
        response = self.client.get(reverse("login"), {"next": reverse("postbook")})
        self.assertContains(response, 'class="pf-prototype pf-v6-c-card"')
        self.assertContains(response, 'type="password"')
        self.assertContains(response, 'name="next" value="/postbook"')
        response = self.client.post(reverse("login"), {
            "username": "prototype", "password": "Test-password-293!",
            "next": reverse("postbook"),
        })
        self.assertRedirects(response, reverse("postbook"))

    def test_invalid_login_keeps_username_but_not_password(self):
        response = self.client.post(reverse("login"), {
            "username": "prototype", "password": "wrong-password", "next": "/postbook",
        })
        self.assertContains(response, 'role="alert"')
        self.assertContains(response, 'value="prototype"')
        self.assertNotContains(response, 'value="wrong-password"')
        self.assertContains(response, 'name="next" value="/postbook"')

    def test_postbook_requires_login(self):
        response = self.client.get(reverse("postbook"))
        self.assertRedirects(response, reverse("login") + "?next=/postbook")

    def test_invalid_post_keeps_values_and_links_errors(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("postbook"), {
            "name": '<script>alert("book")</script>', "price": "not-a-price", "web": "invalid",
        })
        self.assertContains(response, 'enctype="multipart/form-data"')
        self.assertContains(response, 'aria-invalid="true"')
        self.assertContains(response, 'aria-describedby="id_price_error"')
        self.assertContains(response, 'id="id_price_error"')
        self.assertContains(response, 'href="#id_price"')
        self.assertContains(response, '&lt;script&gt;')
        self.assertNotContains(response, '<script>alert("book")</script>')
        self.assertEqual(Book.objects.count(), 0)

    def test_upload_and_success_with_isolated_storage(self):
        self.client.force_login(self.user)
        with TemporaryDirectory() as media, override_settings(MEDIA_ROOT=media):
            response = self.client.post(reverse("postbook"), {
                "name": "Prototype book", "price": "12.50", "web": "https://example.com/book",
                "picture": SimpleUploadedFile("cover.gif", b"GIF89a", content_type="image/gif"),
            })
            self.assertRedirects(response, reverse("postbook") + "?submitted=True")
            book = Book.objects.get()
            self.assertEqual(book.username, self.user)
            self.assertTrue(Path(book.picture.path).is_relative_to(Path(media)))
            self.assertEqual(Path(book.picture.path).read_bytes(), b"GIF89a")
            success = self.client.get(response.url)
            self.assertContains(success, 'class="pf-v6-c-alert pf-m-success pf-m-inline"')
            self.assertContains(success, "Book posted successfully!")

    def test_post_rejects_missing_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(client.post(reverse("postbook"), {"name": "Rejected"}).status_code, 403)
        self.assertFalse(Book.objects.exists())


@skipUnless(os.environ.get("BOOKEX_BROWSER_TESTS") == "1", "Set BOOKEX_BROWSER_TESTS=1 to run Chrome checks")
class PatternFlyBrowserTests(StaticLiveServerTestCase):
    def run_browser(self, javascript):
        chrome = os.environ.get("CHROME_BIN") or shutil.which("google-chrome") or shutil.which("chromium")
        self.assertTrue(chrome, "Install Chrome/Chromium or set CHROME_BIN")
        self.assertTrue(shutil.which("node"), "Node is required for browser checks")
        self.assertTrue((settings.BASE_DIR / "bookEx/static/dist/main.css").exists(), "Run npm run build first")
        get_user_model().objects.create_user(username="prototype", password="Test-password-293!")
        with TemporaryDirectory() as media, override_settings(MEDIA_ROOT=media):
            image = Path(media) / "browser-cover.gif"
            image.write_bytes(b"GIF89a")
            result = subprocess.run(
                ["node", str(settings.BASE_DIR / "frontend/tests/forms.mjs"),
                 chrome, self.live_server_url, str(image), "js" if javascript else "no-js"],
                capture_output=True, text=True, timeout=60,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            book = Book.objects.get()
            self.assertEqual(book.name, "Browser prototype")
            self.assertEqual(book.username.username, "prototype")
            self.assertTrue(Path(book.picture.path).is_relative_to(Path(media)))
            self.assertEqual(Path(book.picture.path).read_bytes(), b"GIF89a")

    def test_native_forms_with_javascript(self):
        self.run_browser(javascript=True)

    def test_native_forms_without_javascript(self):
        self.run_browser(javascript=False)
