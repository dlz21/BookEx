# Project guidance

## Start here
- Book Exchange is a Django application with server-rendered templates and a
  TypeScript/esbuild frontend using PatternFly 6 HTML/CSS.
- Read the task and `git status --short` first; preserve unrelated local changes.
- Use [README.md](README.md) for setup and the documentation index.
- Read only documentation and code relevant to the task; search with `rg` before
  opening large files. Avoid bulk reads of dependencies, generated assets,
  uploads, databases, lockfiles, and archived plans unless the task needs them.

## Source map
- `bookMng/`: models, forms, views, application URLs, and Django tests.
- `bookEx/`: project settings/URLs and `templates/`, including shared includes.
- `frontend/src/`: TypeScript and CSS; `frontend/build.mjs`: asset bundling.
- `bookEx/static/dist/` and `staticfiles/`: generated output; rebuild to change.
- `bookEx/static/uploads/`: existing user uploads; preserve these files.
- `docs/`: focused reference docs; `.ai/`: task/handoff templates and archives.

## Implementation conventions
- Keep routing, permissions, validation, and persistence in Django. Follow nearby
  patterns and reuse template includes before creating another abstraction.
- Use named Django URLs and static tags. Preserve CSRF, autoescaping, bound form
  values/errors, login `next`, multipart uploads, and native form submission.
- Enforce authorization on the server; require authenticated ownership and
  CSRF-protected POST for destructive actions. Legacy behavior is not a precedent.
- Use matching `pf-v6-*` components and native controls. Preserve keyboard access,
  visible focus, labels, responsive layout, and essential behavior without JS.
- Keep changes scoped. Add dependencies or change build/configuration only when
  required by the task; explain the reason and update applicable lockfiles.
- Include migrations for model changes. Never commit credentials, local databases,
  dependency directories, generated bundles, or incidental test uploads.

## Verification
- Activate the project's Python environment before Django commands at repo root.
- Python behavior: `python manage.py check` and the relevant Django test module
  (for example, `python manage.py test bookMng.test_messaging`).
- Frontend/templates: `npm --prefix frontend run build` (includes typechecking),
  plus relevant Django tests. For browser interactions use the opt-in command in
  [docs/testing.md](docs/testing.md); report unavailable prerequisites honestly.
- Cross-cutting behavior: run `python manage.py test` before handoff.
- Documentation-only changes: check links, paths, commands, and `git diff --check`;
  application tests are unnecessary unless executable behavior changes.
- Add regression coverage for meaningful behavior changes. Record exact commands
  and results; distinguish passed, failed, skipped, and not run.

## Collaboration
- Use [.ai/task-template.md](.ai/task-template.md) for scoped work; small requests
  can use its fields directly in the prompt. See [docs/ai-workflow.md](docs/ai-workflow.md).
- Finish with a short handoff using [.ai/handoff-template.md](.ai/handoff-template.md):
  outcome/files, verification, and remaining work. Never claim unrun checks passed.
- Update relevant docs when contracts or commands change; link rather than copy.
- PatternFly migration is complete. `docs/archive/patternfly/` contains historical
  plans/evidence, not an active backlog; consult it only for historical questions.
