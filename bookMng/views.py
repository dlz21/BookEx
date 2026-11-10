from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView

from .models import MainMenu, Book
from .forms import BookForm, ComposeMessageForm, ReplyForm

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .models import MessageThread, PrivateMessage

# Create your views here.
def index(request):
    return render(
        request,
      'bookMng/index.html',
      {
        'item_list': MainMenu.objects.all()
      }
    )


@login_required(login_url=reverse_lazy('login'))
def postbook(request):
    submitted = False
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            #form.save()
            book = form.save(commit=False)
            try:
                book.username = request.user
            except Exception:
                pass
            book.save()

            return HttpResponseRedirect('/postbook?submitted=True')
    else:
        form = BookForm()
        if 'submitted' in request.GET:
            submitted = True

    return render(request,
                  'bookMng/postbook.html',
                  {
                      'form': form,
                      'item_list': MainMenu.objects.all(),
                      'submitted': submitted
                  })

@login_required(login_url=reverse_lazy('login'))
def displaybooks(request):
    books = Book.objects.all()
    for b in books:
        b.pic_path = b.picture.url[14:]
    return render(request,
        'bookMng/displaybooks.html',
        {
        'item_list': MainMenu.objects.all(),
        'books': books
    })

def book_detail(request, book_id):
    book = Book.objects.get(id=book_id)
    book.pic_path = book.picture.url[14:]

    return render(request,'bookMng/book_detail.html', {
        'item_list': MainMenu.objects.all(),
        'book': book
    })

@login_required
def mybooks(request):
    books = Book.objects.filter(username=request.user)

    for b in books:
        b.pic_path = b.picture.url[14:]

    return render(request,'bookMng/mybooks.html', {
        'item_list': MainMenu.objects.all(),
        'books': books
    })


def book_delete(request, book_id):
    book = Book.objects.get(id=book_id)
    book.delete()

    return render(request,'bookMng/book_delete.html', {
        'item_list': MainMenu.objects.all(),
    })


class Register(CreateView):
    template_name = 'registration/register.html'
    form_class = UserCreationForm
    success_url = reverse_lazy('register-success')

    def form_valid(self, form):
        form.save()
        return HttpResponseRedirect(self.success_url)


User = get_user_model()


@login_required
@require_GET
def inbox(request: HttpRequest) -> HttpResponse:
    threads = (
        MessageThread.objects
        .filter(Q(user1=request.user) | Q(user2=request.user))
        .prefetch_related("messages", "user1", "user2")
        .order_by("-updated_at")
    )

    thread_data = []
    for thread in threads:
        other_user = thread.other_user(request.user)
        latest_message = thread.latest_message()
        unread_count = thread.unread_count_for(request.user)
        thread_data.append(
            {
                "thread": thread,
                "other_user": other_user,
                "latest_message": latest_message,
                "unread_count": unread_count,
            }
        )

    context = {
        "thread_data": thread_data,
        'item_list': MainMenu.objects.all(),
    }
    return render(request, "bookMng/inbox.html", context)

@login_required
@require_http_methods(["GET", "POST"])
def thread_detail(request: HttpRequest, thread_id: int) -> HttpResponse:
    thread = get_object_or_404(
        MessageThread.objects.select_related("user1", "user2"),
        pk=thread_id,
    )

    if not thread.has_participant(request.user):
        raise Http404("Message thread not found.")

    form = ReplyForm(request.POST if request.method == "POST" else None)
    form.fields["body"].label = "Reply"
    if request.method == "POST" and form.is_valid():
        PrivateMessage.objects.create(
            thread=thread, sender=request.user,
            recipient=thread.other_user(request.user), body=form.cleaned_data["body"],
        )
        thread.save(update_fields=["updated_at"])
        messages.success(request, "Message sent.")
        return redirect("thread_detail", thread_id=thread.id)

    thread_messages = thread.messages.select_related("sender", "recipient").all()

    unread_messages = thread_messages.filter(recipient=request.user, is_read=False)
    if request.method == "GET":
        for msg in unread_messages:
            msg.mark_as_read()

    context = {
        "thread": thread,
        "other_user": thread.other_user(request.user),
        "thread_messages": thread_messages,
        "form": form,
        'item_list': MainMenu.objects.all(),
    }
    return render(request, "bookMng/thread.html", context)

@login_required
@require_http_methods(["GET", "POST"])
def compose_message(request: HttpRequest) -> HttpResponse:
    initial = {}
    if request.method == "GET" and request.GET.get("user_id"):
        try:
            selected_id = int(request.GET["user_id"])
        except ValueError:
            raise Http404("Recipient not found.")
        selected_user = get_object_or_404(User, pk=selected_id)
        if selected_user == request.user:
            messages.error(request, "You cannot send a message to yourself.")
            return redirect("inbox")
        initial["user_id"] = selected_user

    form = ComposeMessageForm(
        request.POST if request.method == "POST" else None,
        user=request.user, initial=initial,
    )
    if request.method == "POST" and form.is_valid():
        recipient = form.cleaned_data["user_id"]
        thread = MessageThread.get_or_create_thread(request.user, recipient)
        PrivateMessage.objects.create(
            thread=thread, sender=request.user, recipient=recipient,
            body=form.cleaned_data["body"],
        )
        thread.save(update_fields=["updated_at"])
        messages.success(request, f"Message sent to {recipient.username}.")
        return redirect("thread_detail", thread_id=thread.id)

    return render(request, "bookMng/compose.html", {
        "form": form, "item_list": MainMenu.objects.all(),
    })


@login_required
@require_POST
def mark_thread_read(request: HttpRequest, thread_id: int) -> HttpResponse:
    thread = get_object_or_404(MessageThread, pk=thread_id)

    if not thread.has_participant(request.user):
        raise Http404("Message thread not found.")

    unread_messages = thread.messages.filter(recipient=request.user, is_read=False)
    for msg in unread_messages:
        msg.mark_as_read()

    messages.success(request, "Thread marked as read.")
    return redirect("thread_detail", thread_id=thread.id)
