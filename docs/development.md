# Development

## Setup

Run the following from the repository root, where `manage.py` lives. The commands
assume Bash and a Python installation with virtual-environment support.

The previously documented verification toolchain was Python 3.14.6, Django 6.1,
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
(`/mybooks`), Compose Message (`/compose/`), and Inbox (`/inbox/`). The shared
navigation resolves known application destinations by URL name, including legacy
relative `compose/` and `inbox/` records. Custom relative paths are anchored at
Home. My Books and messaging require login; anonymous visitors use `/login/`
with a `next` destination preserved for after sign-in.

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
use local files rather than a runtime CDN. The frontend pins
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

Application overrides live in `frontend/src/main.css`; shared PatternFly styles
and page layouts are imported through the frontend entry points.

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


See [testing](testing.md) for checks and [deployment](deployment.md) for release instructions.
