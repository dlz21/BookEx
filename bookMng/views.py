from django.http import HttpResponse
from django.shortcuts import render
from .models import MainMenu
from .forms import BookForm

# Create your views here.
def index(request):
    return render(
        request,
        'bookMng/displaybooks.html',
        {
                'item_list': MainMenu.objects.all(),
        })

def postbook(request):
    form = BookForm()

    return render(request, 'bookMng/postbook.html', {
        'form': form,
        'item_list': MainMenu.objects.all(),
    })