from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .models import MessageThread, PrivateMessage


class MessagingPageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = get_user_model().objects.create_user(username="alice")
        cls.bob = get_user_model().objects.create_user(username="bob")
        cls.outsider = get_user_model().objects.create_user(username="outsider")
        cls.thread = MessageThread.get_or_create_thread(cls.alice, cls.bob)

    def setUp(self):
        self.client.force_login(self.alice)

    def message(self, **kwargs):
        return PrivateMessage.objects.create(
            thread=self.thread, sender=self.bob, recipient=self.alice,
            body=kwargs.pop("body", "Hello Alice"), **kwargs,
        )

    def test_inbox_empty_then_private_unread_preview_in_updated_order(self):
        empty = self.client.get(reverse("inbox"))
        self.assertContains(empty, "No messages yet.")
        self.message(body="<script>unsafe</script>\nSecond line")
        hidden = MessageThread.get_or_create_thread(self.bob, self.outsider)
        PrivateMessage.objects.create(thread=hidden, sender=self.bob,
                                      recipient=self.outsider, body="Private outsider message")
        newer = MessageThread.get_or_create_thread(self.alice, self.outsider)
        MessageThread.objects.filter(pk=newer.pk).update(updated_at=timezone.now())
        response = self.client.get(reverse("inbox"))
        self.assertEqual([item["thread"].pk for item in response.context["thread_data"]],
                         [newer.pk, self.thread.pk])
        self.assertContains(response, "1 unread")
        self.assertContains(response, "&lt;script&gt;unsafe&lt;/script&gt;")
        self.assertNotContains(response, "Private outsider message")
        self.assertFalse(PrivateMessage.objects.get(thread=self.thread).is_read)
        self.client.force_login(get_user_model().objects.create_user(username="empty"))
        self.assertContains(self.client.get(reverse("inbox")), "No conversations yet")

    def test_compose_preselects_recipient_and_excludes_self(self):
        response = self.client.get(reverse("compose_message"), {"user_id": self.bob.pk})
        self.assertContains(response, f'value="{self.bob.pk}" selected')
        self.assertNotContains(response, f'<option value="{self.alice.pk}"')
        self.assertContains(response, 'name="user_id"')
        self.assertContains(response, 'name="body"')
        self.assertContains(response, "csrfmiddlewaretoken")
        self.assertEqual(self.client.get(reverse("compose_message"), {"user_id": 99999}).status_code, 404)
        self.assertEqual(self.client.get(reverse("compose_message"), {"user_id": "invalid"}).status_code, 404)
        response = self.client.get(reverse("compose_message"), {"user_id": self.alice.pk}, follow=True)
        self.assertContains(response, "You cannot send a message to yourself.", count=1)

    def test_invalid_compose_retains_values_errors_and_navigation(self):
        body = '<script>alert("x")</script>\nRetain me'
        for recipient in ("", str(self.alice.pk), "99999", "not-an-id"):
            with self.subTest(recipient=recipient):
                response = self.client.post(reverse("compose_message"), {"user_id": recipient, "body": body})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context["form"]["body"].value(), body)
                self.assertContains(response, 'data-form-errors')
                self.assertContains(response, 'aria-invalid="true"')
                self.assertContains(response, 'href="/inbox/"')
                self.assertContains(response, '&lt;script&gt;')
                self.assertNotContains(response, body)
        response = self.client.post(reverse("compose_message"), {"user_id": self.bob.pk, "body": " \n "})
        self.assertContains(response, f'value="{self.bob.pk}" selected')
        self.assertContains(response, "Message body cannot be empty.")
        self.assertFalse(PrivateMessage.objects.exists())

    def test_compose_sends_once_to_posted_recipient_and_feedback_is_consumed(self):
        response = self.client.post(reverse("compose_message") + f"?user_id={self.outsider.pk}",
                                    {"user_id": self.bob.pk, "body": "Hello\nBob"}, follow=True)
        self.assertRedirects(response, reverse("thread_detail", args=[self.thread.pk]))
        sent = PrivateMessage.objects.get()
        self.assertEqual((sent.sender, sent.recipient, sent.body), (self.alice, self.bob, "Hello\nBob"))
        self.assertContains(response, "Message sent to bob.", count=1)
        self.assertNotContains(self.client.get(response.request["PATH_INFO"]), "Message sent to bob.")
        sent.refresh_from_db()
        self.assertFalse(sent.is_read)  # Reading one's own send does not mark it read.

    def test_thread_orders_escapes_and_marks_only_incoming_read(self):
        first = self.message(body="<script>first</script>\nSecond line")
        outgoing = PrivateMessage.objects.create(thread=self.thread, sender=self.alice,
                                                 recipient=self.bob, body="Outgoing")
        response = self.client.get(reverse("thread_detail", args=[self.thread.pk]))
        self.assertEqual(list(response.context["thread_messages"]), [first, outgoing])
        self.assertContains(response, "&lt;script&gt;first&lt;/script&gt;\nSecond line")
        self.assertNotContains(response, "<script>first</script>")
        self.assertContains(response, 'datetime="')
        first.refresh_from_db()
        outgoing.refresh_from_db()
        self.assertTrue(first.is_read)
        self.assertIsNotNone(first.read_at)
        self.assertFalse(outgoing.is_read)
        read_at = first.read_at
        self.client.get(reverse("thread_detail", args=[self.thread.pk]))
        first.refresh_from_db()
        self.assertEqual(first.read_at, read_at)

    def test_empty_thread_and_invalid_reply_then_success(self):
        url = reverse("thread_detail", args=[self.thread.pk])
        self.assertContains(self.client.get(url), "No messages in this conversation yet.")
        incoming = self.message()
        response = self.client.post(url, {"body": " \n "})
        self.assertContains(response, "Message body cannot be empty.")
        self.assertEqual(response.context["form"]["body"].value(), " \n ")
        incoming.refresh_from_db()
        self.assertFalse(incoming.is_read)  # Invalid POST has no read side effect.
        response = self.client.post(url, {"body": "Reply\nwith two lines"}, follow=True)
        self.assertContains(response, "Message sent.", count=1)
        reply = PrivateMessage.objects.latest("pk")
        self.assertEqual((reply.sender, reply.recipient, reply.body),
                         (self.alice, self.bob, "Reply\nwith two lines"))

    def test_mark_read_post_redirect_timestamps_and_feedback_once(self):
        incoming = self.message()
        url = reverse("mark_thread_read", args=[self.thread.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        incoming.refresh_from_db()
        self.assertFalse(incoming.is_read)
        response = self.client.post(url, follow=True)
        self.assertRedirects(response, reverse("thread_detail", args=[self.thread.pk]))
        self.assertContains(response, "Thread marked as read.", count=1)
        incoming.refresh_from_db()
        self.assertTrue(incoming.is_read)
        self.assertIsNotNone(incoming.read_at)
        self.assertNotContains(self.client.get(reverse("thread_detail", args=[self.thread.pk])),
                              "Thread marked as read.")

    def test_outsider_rejected_for_thread_reply_and_mark_read(self):
        incoming = self.message()
        self.client.force_login(self.outsider)
        url = reverse("thread_detail", args=[self.thread.pk])
        for response in (self.client.get(url), self.client.post(url, {"body": "Attack"}),
                         self.client.post(reverse("mark_thread_read", args=[self.thread.pk]))):
            self.assertEqual(response.status_code, 404)
        incoming.refresh_from_db()
        self.assertFalse(incoming.is_read)
        self.assertEqual(PrivateMessage.objects.count(), 1)

    def test_messaging_posts_require_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.alice)
        for url in (reverse("compose_message"), reverse("thread_detail", args=[self.thread.pk]),
                    reverse("mark_thread_read", args=[self.thread.pk])):
            self.assertEqual(client.post(url, {"user_id": self.bob.pk, "body": "Rejected"}).status_code, 403)
        self.assertFalse(PrivateMessage.objects.exists())
