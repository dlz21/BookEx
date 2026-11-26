# Book Exchange

A Django application for listing, finding, and exchanging books, with private
messaging and a TypeScript/esbuild frontend using PatternFly 6.
Django owns routes, authentication, validation, and persistence. Node is needed
to build frontend assets; it is not needed to run Django once assets are built.

## Quick start

Run from the repository root. Python and Node/npm are required; see
[development setup](docs/development.md#setup) for toolchain details and nvm usage.
There is no Python dependency manifest yet; the Django version below follows the
existing setup instructions and does not lock transitive dependencies.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install "Django==6.1"
python manage.py migrate
npm --prefix frontend ci
npm --prefix frontend run build
python manage.py runserver
```

Open <http://127.0.0.1:8000/>. Register an account to use protected features.
Optionally run `python manage.py createsuperuser` to access `/admin/`.

## Project map

| Path | Purpose |
| --- | --- |
| `bookMng/` | Application models, forms, views, routes, and tests |
| `bookEx/templates/` | Django pages and shared template includes |
| `bookEx/settings.py` | Django project configuration |
| `frontend/src/` | TypeScript and CSS source |
| `docs/` | Development and project reference documentation |
| `.ai/` | Task and handoff templates |

## Documentation

- [Development](docs/development.md): setup, frontend builds, watch commands, and static assets.
- [Architecture](docs/architecture.md): shared navigation, forms, and messaging contracts.
- [Testing](docs/testing.md): Django checks, frontend builds, and opt-in browser tests.
- [Deployment](docs/deployment.md): release procedure, upload storage, caching, and troubleshooting.
- [AI collaboration](docs/ai-workflow.md): task templates, focused context, and short handoffs.
- [Agent guidance](AGENTS.md): repository conventions and verification expectations.
- [PatternFly archive](docs/archive/patternfly/README.md): completed migration history.

The PatternFly migration is complete. Production hosting/static serving and
persistent upload delivery still require deployment configuration; see the
deployment guide before releasing.
