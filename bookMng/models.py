from django.contrib.auth.models import User
from django.db import models

from django.conf import settings
from django.utils import timezone
from django.db import models

class MainMenu(models.Model):
    item = models.CharField(max_length=300, unique=True)
    link = models.CharField(max_length=300, unique=True)

    def __str__(self):
        return self.item

class Book(models.Model):
    name = models.CharField(max_length=200)
    web = models.URLField(max_length=300)
    price = models.DecimalField(decimal_places=2, max_digits=8)
    publishdate = models.DateField(auto_now=True)
    picture = models.FileField(upload_to='bookEx/static/uploads')
    pic_path = models.CharField(max_length=300, editable=False, blank=True)
    username = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE)


class MessageThread(models.Model):
    """
    A conversation between exactly two users.
    """
    user1 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="message_threads_as_user1",
    )
    user2 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="message_threads_as_user2",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user1", "user2"],
                name="unique_message_thread_pair",
            )
        ]

    def __str__(self) -> str:
        return f"Thread({self.user1} <-> {self.user2})"

    @staticmethod
    def normalize_users(user_a, user_b):
        """
        Ensure user ordering is stable so that a thread between two users
        always maps to the same unique database row.
        """
        if user_a.pk < user_b.pk:
            return user_a, user_b
        return user_b, user_a

    @classmethod
    def get_or_create_thread(cls, user_a, user_b):
        if user_a == user_b:
            raise ValueError("A user cannot create a thread with themselves.")

        user1, user2 = cls.normalize_users(user_a, user_b)
        thread, _ = cls.objects.get_or_create(user1=user1, user2=user2)
        return thread

    def participants(self):
        return [self.user1, self.user2]

    def other_user(self, current_user):
        if current_user == self.user1:
            return self.user2
        return self.user1

    def has_participant(self, user):
        return user == self.user1 or user == self.user2

    def latest_message(self):
        return self.messages.order_by("-created_at").first()

    def unread_count_for(self, user):
        return self.messages.filter(recipient=user, is_read=False).count()


class PrivateMessage(models.Model):
    thread = models.ForeignKey(
        MessageThread,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_private_messages",
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_private_messages",
    )
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"Message(from={self.sender}, to={self.recipient}, at={self.created_at})"

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=["is_read", "read_at"])