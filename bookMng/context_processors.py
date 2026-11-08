from django.urls import reverse

from .models import MainMenu


def navigation(request):
    """One menu for every application page, including built-in auth views."""
    items = [
        {"label": item.item, "url": item.get_absolute_url()}
        for item in MainMenu.objects.order_by("pk")
    ]
    if not items:
        items = [
            {"label": label, "url": reverse(route)}
            for label, route in (
                ("Home", "index"),
                ("Post Book", "postbook"),
                ("Display Books", "displaybooks"),
                ("My Books", "mybooks"),
                ("Compose Message", "compose_message"),
                ("Inbox", "inbox"),
            )
        ]
    route = request.resolver_match.url_name if request.resolver_match else None
    for item in items:
        item["current"] = "page" if item["url"] == request.path else ""
        # A conversation belongs to Inbox, but Inbox isn't the current page.
        if route in ("thread_detail", "mark_thread_read") and item["url"] == reverse("inbox"):
            item["current"] = "true"
    return {"navigation_items": items}
