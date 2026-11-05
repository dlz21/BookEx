from django.contrib import admin
from .models import MainMenu
from .models import Book, MessageThread, PrivateMessage

admin.site.register(MainMenu)
admin.site.register(Book)

@admin.register(MessageThread)
class MessageThreadAdmin(admin.ModelAdmin):
    list_display = ("id", "user1", "user2", "created_at", "updated_at")
    search_fields = ("user1__username", "user2__username")


@admin.register(PrivateMessage)
class PrivateMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "thread", "sender", "recipient", "is_read", "created_at")
    search_fields = ("sender__username", "recipient__username", "body")
    list_filter = ("is_read", "created_at")