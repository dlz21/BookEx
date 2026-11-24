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
from django.db.models import BooleanField, Exists, OuterRef, Q, Value
from django.core.paginator import Paginator
from django.templatetags.static import static
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseBadRequest
from django.utils.http import url_has_allowed_host_and_scheme
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .models import Favorite, MessageThread, PrivateMessage

# Create your views here.
def index(request):
    return render(
        request,
      'bookMng/index.html',
      {
        'item_list': MainMenu.objects.all()
      }
    )

def about(request):
    return render(
        request,
        'bookMng/about.html',
        {
            'item_list': MainMenu.objects.all()
        }
    )

def _book_cover_url(book):
    if not book.picture:
        return ''
    # Legacy uploads live in static; other storage backends own their URLs.
    if book.picture.name.startswith('bookEx/static/'):
        return static(book.picture.name.removeprefix('bookEx/static/'))
    return book.picture.url


def _with_favorite_state(books, user):
    """Annotate the current user's state without a query for each book."""
    state = (
        Exists(Favorite.objects.filter(user=user, book_id=OuterRef('pk')))
        if user.is_authenticated else Value(False, output_field=BooleanField())
    )
    return books.annotate(is_favorited=state)


@login_required
@require_GET
def favorites(request):
    books = _with_favorite_state(
        Book.objects.filter(favorites__user=request.user).select_related('username').order_by('name', 'pk'),
        request.user,
    )
    for book in books:
        book.cover_url = _book_cover_url(book)
    return render(request, 'bookMng/favorites.html', {'books': books})


@login_required
@require_POST
def set_favorite(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    action = request.POST.get('action')
    if action == 'add':
        Favorite.objects.get_or_create(user=request.user, book=book)
    elif action == 'remove':
        Favorite.objects.filter(user=request.user, book=book).delete()
    else:
        return HttpResponseBadRequest('Choose add or remove.')

    destination = request.POST.get('next', '')
    if not url_has_allowed_host_and_scheme(
        destination, allowed_hosts={request.get_host()}, require_https=request.is_secure(),
    ):
        destination = reverse_lazy('favorites')
    return redirect(destination)


def search_books(request):
    query = request.GET.get('q', '').strip()
    sort_options = {
        'newest': ('-publishdate', '-pk'),
        'price_asc': ('price', 'pk'),
        'price_desc': ('-price', 'pk'),
        'title': ('name', 'pk'),
    }
    sort = request.GET.get('sort', 'newest')
    if sort not in sort_options:
        sort = 'newest'

    books = Book.objects.none()

    if query:
        books = Book.objects.select_related('username').filter(
            Q(name__icontains=query) |
            Q(username__username__icontains=query)
        ).order_by(*sort_options[sort])

    page = Paginator(_with_favorite_state(books, request.user), 12).get_page(request.GET.get('page'))
    for book in page.object_list:
        book.cover_url = _book_cover_url(book)

    return render(
        request,
        'bookMng/search.html',
        {
            'item_list': MainMenu.objects.all(),
            'books': page.object_list,
            'page_obj': page,
            'query': query,
            'sort': sort,
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
    books = _with_favorite_state(Book.objects.select_related('username'), request.user)
    return render(request,
        'bookMng/displaybooks.html',
        {
        'item_list': MainMenu.objects.all(),
        'books': books
    })

def book_detail(request, book_id):
    book = get_object_or_404(_with_favorite_state(Book.objects.all(), request.user), id=book_id)
    book.cover_url = _book_cover_url(book)

    return render(request,'bookMng/book_detail.html', {
        'item_list': MainMenu.objects.all(),
        'book': book
    })

@login_required
def mybooks(request):
    books = _with_favorite_state(Book.objects.filter(username=request.user), request.user)

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
