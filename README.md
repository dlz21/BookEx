# Book Exchange

A Django application with a TypeScript/esbuild frontend. Django owns routes,
authentication, validation, and persistence. Node is required to build frontend
assets; it is not required to run Django after those assets have been delivered.

## Current integration status

The frontend build works, but the PatternFly migration is still in progress:

- `frontend/src/main.ts` is currently empty, so the build produces empty
  bundles until imports are added.
- `bookEx/templates/base.html` does not yet load the generated bundles.
- `STATIC_ROOT` and a production application/static server are not configured.
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

Edit `frontend/src/main.ts` for explicit component imports and browser behavior;
edit `frontend/src/main.css` for framework CSS imports and application overrides.
`build.mjs` loads both sources through an in-memory entry point. It emits:

```text
bookEx/static/dist/
├── main.js
├── main.css
└── assets/       # Referenced fonts/images, when present; hashed filenames
```

The build targets ES2022 browsers and emits an ES module. Imported fonts/images
use local files rather than a runtime CDN. Choose compatible PatternFly Elements
and core CSS versions before adding imports; installation alone does not apply
PatternFly to templates.

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

These changes are still required; the snippets below document what to configure
and are not already present in the application.

Add the bundles once to the shared base template's `<head>`:

```django
{% load static %}
<link rel="stylesheet" href="{% static 'dist/main.css' %}">
<script type="module" src="{% static 'dist/main.js' %}"></script>
```

Keep required legacy styles during the incremental migration. Remove them when
their pages have been migrated and verified.

Set a collection destination separate from source static directories in the
settings used for deployment. For a site served at the domain root:

```python
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
```

Keep the existing `STATICFILES_DIRS` entry for `bookEx/static`. Do not add
`STATIC_ROOT` to `STATICFILES_DIRS`. For a subpath or CDN deployment, choose the
appropriate static URL and verify font/image references under that URL.

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

As of November 7, 2026, build/typecheck and Django checks pass. Django discovers
zero tests, so a successful test command does not demonstrate regression coverage.
Browser automation is not configured. Once static integration is added, manually
check book, authentication, and messaging journeys, keyboard/mobile behavior, and
asset requests from nested routes such as `/thread/<id>/`.

## Deployment

Deployment is a build step followed by static collection and application release.
The repository does not yet choose a hosting platform or production server.
Complete the static integration above before using this procedure.

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
| Bundles are zero bytes | Add actual imports/styles; current source files are empty |
| Build succeeds but the page looks unchanged | Load bundles in `base.html`, refresh, and inspect the network panel |
| Nested routes return asset 404s | Use Django static tags and verify the static URL/server mapping |
| `collectstatic` reports no filesystem path | Configure `STATIC_ROOT` in the settings used for that command |
| Watch output exists despite type errors | Bundle watch and typecheck watch are separate; production build checks types first |

See Django's [static deployment guide](https://docs.djangoproject.com/en/6.0/howto/static-files/deployment/)
and [deployment checklist](https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/)
for the collection/serving boundary and production settings requirements.
