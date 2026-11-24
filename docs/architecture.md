# Architecture and shared UI

Django owns application behavior and renders templates; TypeScript adds browser
interactions and esbuild bundles local assets. The PatternFly 6 migration is
complete per maintainer confirmation; historical plans are [archived](archive/patternfly/README.md).

Source paths in this document are relative to the repository root.

## Shared shell

`base.html` includes `includes/navigation.html` and
`includes/account_actions.html` on every application page. Child templates supply
`content` and may override `title`; they no longer supply a sidebar block.

The `bookMng.context_processors.navigation` processor supplies `navigation_items`
with `label`, `url`, and `current` fields. Home is always first and appears once;
records resolving to the Home URL are replaced by that canonical entry. Other
`MainMenu` records retain primary key order. It resolves their existing named
destinations and supplies the six standard destinations when the menu table is
empty. Exact paths set `aria-current="page"`
independently of query parameters; a thread marks Inbox with `aria-current="true"`
as its containing section. Other links remain available without current-page styling.

Account actions use Django's `user` and `request` context. Visitors get Log in and
Register; signed-in users get their escaped username and a CSRF-protected logout
POST returning Home. Login links retain the current URL as `next`, except on
authentication pages. The footer uses the current year.

`frontend/src/shell.css` imports PF6 masthead/navigation component styles and owns
shared layout and focus styling. At widths up to 48rem, the masthead button toggles
the same navigation list using `aria-controls` and `aria-expanded`. Native button
keyboard behavior works, Escape returns focus to the toggle, and resizing preserves
visible focus. Without JavaScript the toggle stays hidden and navigation stays
expanded. The skip link becomes visible on focus and targets the main landmark.

Validation: `npm run build` and `BOOKEX_BROWSER_TESTS=1 python manage.py test`
passed on November 8, 2026 (16 server tests and two Chrome cases). Browser checks
cover skip-link focus, mobile expansion/Escape/resize, active links, logout, and
the existing form/upload journeys with and without JavaScript.

## Messaging patterns

Inbox uses PF6 conversation cards and unread badges; thread messages use an
ordered list of PF6 cards with sender names and machine-readable timestamps.
`frontend/src/messaging.css` adds page layout, wrapping, and preserved message
line breaks. All text stays Django-escaped, including usernames and message bodies.

`includes/message_form.html` takes a bound `form`, a named-route `action_url`,
and a `submit_label`. It supplies CSRF and delegates labels, help, error summaries,
and native controls to `includes/form_fields.html`. `ComposeMessageForm` keeps
the existing `user_id` and `body` field names; `ReplyForm` uses `body`. Recipients
exclude the current user. `?user_id=` preselects the recipient on GET; POST uses
the submitted recipient. Invalid submissions retain entered values and render
linked field errors. Textarea Enter inserts a newline; the submit button sends.
Forms and all messaging actions work without page JavaScript.

`includes/feedback.html` consumes Django `messages` once in the base template.
It maps severity to PF6 inline alerts, using `role="alert"` for errors/warnings
and `role="status"` for informational/success feedback. Form validation uses
the shared form error summary instead of enqueueing duplicate Django messages.
Thread GET marks only incoming unread messages read. The explicit CSRF-protected
mark-read POST redirects to the named `thread_detail` route. Thread GET/reply/read
remain participant-only; inbox remains scoped to the signed-in user's threads.

These field and feedback includes can support future comment forms; card
sender/time and multiline text patterns can support comment display. Future
comments must define their own permissions rather than reuse private-thread access.
Ratings and favorites still need their product rules and models/routes; no new
feature destinations or widgets are added here.

Messaging verification (November 8, 2026): nine isolated server cases in
`bookMng/test_messaging.py` cover empty/populated inbox, ordering, unread/read
timestamps, compose validation and preselection, retained input, escaped output,
send/reply, feedback consumption, participant authorization, and CSRF rejection.
Both opt-in Chrome cases additionally exercise inbox/compose/thread/reply/read,
textarea Enter, error focus, native controls, and long content at
360/768/1280px with JavaScript enabled and disabled. Full accessibility scanning,
200% zoom, and production static serving remain unverified.
