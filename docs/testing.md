# Testing

Run commands from the stated working directory. The dated results below were
retained from the original README; they are historical evidence, not a fresh run
or a current test count. Consult the test files for present coverage.

## Checks

From `frontend/`:

```bash
npm run typecheck
npm run build
```

From the repository root, with the Python environment activated:

```bash
python manage.py check
python manage.py test
python manage.py findstatic dist/main.js dist/main.css --verbosity 2
```

As of November 8, 2026, build/typecheck and Django checks pass. Twenty-six Django
regression tests cover login/`next`, anonymous messaging/My Books redirects,
owner-filtered My Books, sidebar navigation from nested routes and invalid compose
responses, invalid credentials, protected posting, linked validation errors/escaping,
CSRF rejection, and upload/success with isolated storage. Two opt-in Chrome checks exercise actual native Enter-key submission,
password input, invalid forms, upload, responsive book tables, messaging, and success
with page JavaScript enabled and disabled. These checks passed; the rest of the application
still needs regression and accessibility coverage.

Build first, then run browser checks from the root:

```bash
BOOKEX_BROWSER_TESTS=1 python manage.py test bookMng.tests.PatternFlyBrowserTests
```

Prerequisites are Node and Chrome/Chromium. The test runner discovers
`google-chrome` or `chromium`; set `CHROME_BIN` to another executable path if
needed. It uses Django's temporary live server/database, temporary uploads, and
a temporary headless browser profile. Local sockets and browser execution must
be permitted. No Playwright dependency or running development server is required.
Default `python manage.py test` skips these two browser cases; it still runs the
26 server regression cases, including the messaging coverage described above.

To try the prototype manually, run Django and visit `/login/?next=/postbook`.
Submit empty fields to see native browser popovers such as “Please fill out this
field.” These checks use Django's rendered `required`, input type, and numeric
step attributes; they work without JavaScript and block the POST. The exact
message depends on the browser and its language. PatternFly error borders appear
for client-invalid fields after interaction and clear when their values are valid;
untouched controls stay neutral. See MDN's
[constraint-validation guide](https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Forms/Form_validation).

Next, submit filled-in but incorrect credentials to see Django's server-rendered
error alert. After login, try a malformed book URL, a price with more than two
decimal places, or an omitted file, then correct them and submit with Enter.
Django still validates every request: browser constraints can be bypassed and do
not replace authentication or server validation. Server-returned error messages
remain visible until the next response. Passwords are not echoed back on error;
browsers require reselecting a file after a failed POST. Browser tests cover both
native POST blocking and a deliberate client-validation bypass to verify server
errors, with page JavaScript enabled and disabled.

Static collection was also verified locally, including matching bundles and
Django admin CSS. Run `collectstatic` again after changes intended for deployment.
Production static-server configuration and full application journeys remain
unverified.
