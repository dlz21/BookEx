# Book Exchange

A Django application with a TypeScript/esbuild frontend. Django owns routes,
authentication, validation, and persistence. Node is required to build frontend
assets; it is not required to run Django after those assets have been delivered.

## Current integration status

The frontend build works, but the PatternFly migration is still in progress:

- Login and post-book are the first PatternFly prototype: PF6 HTML/CSS cards,
  validation/success alerts, and native Django forms. Other pages still need migration.
- `frontend/src/main.ts` imports prototype CSS and focuses the rendered error
  summary. `frontend/src/main.css` retains legacy styling for remaining pages.
- `bookEx/templates/base.html` loads the generated CSS and JavaScript module.
- `STATIC_ROOT` is configured and static collection works. A production
  application/static server is still not configured.
- There is no Python dependency manifest yet. The setup below installs the
  currently used Django version; it does not lock transitive Python dependencies.

## Setup

Run the following from the repository root, where `manage.py` lives. The commands
assume Bash and a Python installation with virtual-environment support.

The local toolchain used to verify the build is Python 3.14.6, Django 6.1,
Node 26.13.0, and npm 11.20.0. `frontend/.nvmrc` records the Node version; frontend
dependencies are resolved by `frontend/package-lock.json`.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install "Django==6.1"
python manage.py migrate
```

If you use nvm, select the repository's Node version and install frontend
dependencies:

```bash
cd frontend
nvm install
nvm use
npm ci
npm run build
cd ..
```

Without nvm, install Node 26.13.0 through your preferred installer and run the
same `npm ci` and build commands in `frontend/`. Include development dependencies
when installing on a build machine: TypeScript and esbuild are build tools.
Use `npm ci` for an existing lockfile; use `npm install` when intentionally
changing dependencies, and commit the resulting manifest/lockfile changes.

Optionally create an administrator account:

```bash
python manage.py createsuperuser
```

Start Django and open <http://127.0.0.1:8000/>:

```bash
python manage.py runserver
```

A new database has no application menu records. After creating an administrator,
use `/admin/` to add `MainMenu` records as needed. Existing destinations include
Home (`/`), Post Book (`/postbook`), Display Books (`/displaybooks`), My Books
(`/mybooks`), Compose Message (`/compose/`), and Inbox (`/inbox/`). Use paths
starting with `/` so navigation also works from nested thread routes. Anonymous
access to My Books is a known baseline issue; use it while logged in.

## Build and source layout

Run frontend commands inside `frontend/`:

| Command | Purpose |
| --- | --- |
| `npm run typecheck` | Run strict TypeScript checking without emitting files |
| `npm run build` | Pass typechecking, then create minified browser JS/CSS |
| `npm run watch` | Rebuild browser bundles on changes, with source maps |
| `npm run typecheck:watch` | Continuously report TypeScript errors |

Edit `frontend/src/main.ts` for browser behavior and the prototype CSS entry;
edit `frontend/src/prototype.css` for the selected PatternFly component CSS imports
and prototype layout. `frontend/src/main.css` retains legacy styling. CSS-only
imports are declared in `src/css.d.ts`; strict side-effect-import checking is enabled.
`build.mjs` loads `main.ts` and `main.css` through an in-memory entry point. It emits:

```text
bookEx/static/dist/
├── main.js
├── main.css
└── assets/       # Referenced fonts/images, when present; hashed filenames
```

The build targets ES2022 browsers and emits an ES module. Imported fonts/images
use local files rather than a runtime CDN. The prototype pins
`@patternfly/patternfly` to 6.7.0 and uses matching `pf-v6-*` HTML/CSS APIs.
Elements was removed by the package change; no web components or React are
required. Do not add `pf-v5-*` Elements to this PF6 design without separately
proving compatibility.

Each build/watch startup removes only `bookEx/static/dist/`. Do not put source
files or uploads there. Existing `bookEx/static/uploads/` is outside that cleanup
boundary. Generated bundles, npm dependencies, and `staticfiles/` are ignored;
commit source, build configuration, `.nvmrc`, and the npm lockfile.

## Watch during development

Use three terminals. Start each at the repository root.

Terminal 1, with the Python environment activated:

```bash
source .venv/bin/activate
python manage.py runserver
```

Terminal 2:

```bash
cd frontend
npm run watch
```

Terminal 3:

```bash
cd frontend
npm run typecheck:watch
```

Watch bundling does not check types; keep the typecheck watcher running too.
Refresh the browser after a rebuild; browser live reload is not configured.
Stop watchers with Ctrl+C. Restart the bundler after changing `build.mjs`, and
run `npm run build` again before delivery to replace development output.

## Django static integration

The shared base template loads the bundles once in its `<head>`:

```django
{% load static %}
<link rel="stylesheet" href="{% static 'dist/main.css' %}">
<script type="module" src="{% static 'dist/main.js' %}"></script>
```

Legacy styling now lives in `frontend/src/main.css`; replacing it with verified
PatternFly patterns remains migration work.

The settings configure a collection destination separate from source static
files, with an absolute URL for a site served at the domain root:

```python
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
```

The three settings have different jobs:

| Setting | Value here | Purpose |
| --- | --- | --- |
| `STATICFILES_DIRS` | `[BASE_DIR / "bookEx" / "static"]` | Input: where Django finds project assets, including built bundles |
| `STATIC_ROOT` | `BASE_DIR / "staticfiles"` | Output: where `collectstatic` assembles a deployment copy of project and installed-app assets |
| `STATIC_URL` | `/static/` | Browser URL prefix; the production server maps this to collected files |

The asset flow is:

```text
frontend/src/ -> npm run build -> bookEx/static/dist/
                                      |
installed-app static assets -----------+-> collectstatic -> staticfiles/
                                                               |
                                                      production static server
                                                               |
                                                        /static/... URLs
```

`STATIC_ROOT` is needed for the filesystem-based production collection workflow.
Without it, `collectstatic` has no destination. During development, `runserver`
with `DEBUG=True` can discover source assets directly, which is why pages can
work before collection is configured. Setting `STATIC_ROOT` does not start a
static server or make production serving automatic.

Keep `STATIC_ROOT` separate from `STATICFILES_DIRS`; collection must not copy
output back into its inputs. Treat `staticfiles/` as generated, ignored output,
not a place to edit CSS or keep the only copy of uploads. After each frontend
build intended for deployment, refresh it from the repository root:

```bash
python manage.py collectstatic --noinput
```

This copies the generated bundles, Django admin assets, and other discovered
static files into one directory for the production server. For a subpath or CDN
deployment, choose the appropriate static URL and verify font/image references
under that URL. See Django's
[staticfiles reference](https://docs.djangoproject.com/en/6.0/ref/contrib/staticfiles/)
for collection behavior.

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

As of November 7, 2026, build/typecheck and Django checks pass. The six Django
regression tests cover login/`next`, invalid credentials, protected posting,
linked validation errors/escaping, CSRF rejection, and upload/success with isolated
storage. Two opt-in Chrome checks exercise actual native Enter-key submission,
password input, invalid forms, upload, responsive widths, and success with page
JavaScript enabled and disabled. These checks passed; the rest of the application
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
six server regression cases.

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

## Deployment

Deployment is a build step followed by static collection and application release.
The repository does not yet choose a hosting platform or production server.
Local static integration and collection are configured; production server and
settings configuration still need to be supplied for this procedure.

1. Install Python dependencies in the deployment environment and configure the
   production settings. Set `DEBUG=False`, appropriate `ALLOWED_HOSTS`, and a
   production secret key supplied outside source control. Configure persistent
   database/upload storage and HTTPS for the chosen host. Export
   `DJANGO_SETTINGS_MODULE` with the actual production settings module before
   running management commands; no production settings module is supplied yet.
2. Build from the release's lockfile on the build machine:

   ```bash
   cd frontend
   npm ci
   npm run build
   cd ..
   ```

3. From the root, using production settings and the Python environment, validate
   the release, apply its migrations, then collect its built assets:

   ```bash
   python manage.py check --deploy
   python manage.py test
   python manage.py migrate
   python manage.py collectstatic --noinput
   ```

   Resolve deployment-check warnings for the actual environment. `collectstatic`
   requires `STATIC_ROOT`; it does not build the frontend. Confirm that the
   collected directory contains `dist/main.js`, `dist/main.css`, and any referenced
   `dist/assets/` files.

4. Publish the complete collected static directory through the host's static
   server or configured static storage backend at `STATIC_URL`. Run Django through
   a production WSGI/ASGI server using `bookEx.wsgi:application` or
   `bookEx.asgi:application`. Choose and install a server supported by the host;
   Django's development `runserver` is not the production server.
5. Release application code and matching assets together, then check login,
   books, and messaging under production settings. Verify JS/CSS MIME types,
   module loading, fonts/images, and static requests from nested routes. Review
   browser console/network errors. Node and `node_modules` may stay on the build
   machine; deploy the Python application and collected assets.

The current upload implementation writes book images into
`bookEx/static/uploads/`. Preserve those files across releases and verify new
uploads remain visible under the production serving arrangement: a one-time
static collection does not publish subsequent uploads automatically. Persistent
upload serving needs to be resolved before deployment; the frontend build must
never delete uploaded files.

### Cache invalidation

`main.js` and `main.css` have stable filenames. Configure those URLs for cache
revalidation (for example, `Cache-Control: no-cache` with ETag/Last-Modified) and
purge any CDN copies on release. Avoid immutable caching of these entry files.
Hashed files under `dist/assets/` may use long-lived immutable caching; retain
previously referenced hashed assets while cached pages/bundles can still use them.
Publish each release as a matching set of code and static files and retain a
matching set for rollback. A manifest-based static backend is a separate change
that needs validation against emitted CSS/JS asset references.

### Troubleshooting

| Symptom | Check |
| --- | --- |
| Bundler cannot resolve `src/main.css` | The stylesheet must match the path in `build.mjs`; the current name is `main.css` |
| `tsc` or esbuild is missing | Run `npm ci` in `frontend/` with development dependencies included |
| Styles look unchanged | Rebuild, confirm `prototype.css` is imported, and inspect `/static/dist/main.css`; only login/post-book use PF6 markup so far |
| Build succeeds but the page looks unchanged | Load bundles in `base.html`, refresh, and inspect the network panel |
| Nested routes return asset 404s | Use Django static tags and verify the static URL/server mapping |
| `collectstatic` reports no filesystem path | Configure `STATIC_ROOT` in the settings used for that command |
| Watch output exists despite type errors | Bundle watch and typecheck watch are separate; production build checks types first |

See Django's [static deployment guide](https://docs.djangoproject.com/en/6.0/howto/static-files/deployment/)
and [deployment checklist](https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/)
for the collection/serving boundary and production settings requirements.
