from django import forms
from django.forms import ModelForm
from .models import Book
from django.contrib.auth import get_user_model

class BookForm(ModelForm):
    class Meta:
        model = Book
        fields = ['name', 'web', 'price', 'picture']


class ReplyForm(forms.Form):
    body = forms.CharField(
        label="Message", widget=forms.Textarea(attrs={"rows": 6}),
        error_messages={"required": "Message body cannot be empty."},
    )


class ComposeMessageForm(ReplyForm):
    user_id = forms.ModelChoiceField(
        label="Recipient", queryset=get_user_model().objects.none(),
        empty_label="Select a user",
        error_messages={
            "required": "Please choose a recipient.",
            "invalid_choice": "Please choose an available recipient other than yourself.",
        },
    )
    field_order = ["user_id", "body"]

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["user_id"].queryset = (
            get_user_model().objects.exclude(pk=user.pk).order_by("username")
        )
