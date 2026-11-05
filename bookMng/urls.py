from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('postbook', views.postbook, name='postbook'),
    path('displaybooks', views.displaybooks, name='displaybooks'),
    path('book_detail/<int:book_id>', views.book_detail, name='book_detail'),
    path('mybooks', views.mybooks, name='mybooks'),
    path('book_delete/<int:book_id>', views.book_delete, name='book_delete'),
    path("inbox/", views.inbox, name="inbox"),
    path("compose/", views.compose_message, name="compose_message"),
    path("thread/<int:thread_id>/", views.thread_detail, name="thread_detail"),
    path("thread/<int:thread_id>/mark-read/", views.mark_thread_read, name="mark_thread_read"),
]