# PatternFly integration plan

> **Archived — feature complete.** Closed on November 23, 2026 per maintainer
> confirmation. The plan, status notes, and checkboxes below are historical
> snapshots retained unchanged; they are not an active backlog or evidence
> that outstanding checks were rerun at closure. See [archive notes](README.md).

Status: build/static foundation partially complete; shared shell and PF6
login/post-book prototype verified. November 8, 2026 review of the last four
commits confirms registration markup migration and partial book-list/detail
migration; broader page migration and acceptance verification remain pending.

## Goal and scope

Adopt PatternFly throughout the Book Exchange application while retaining Django
templates, Python views, authentication, forms, private messaging, and database
ownership. Use PatternFly 6 HTML/CSS components and native controls for the
current migration. The installed core package replaced Elements; future custom
components require a separate compatibility proof before adoption.

Full adoption means a consistent application shell and all existing public
application pages, including empty, error, and success states. It does not mean
adding every component in the PatternFly catalog. Django's built-in `/admin/`
interface is outside this feature. Existing auth URLs without application-owned
templates are not new feature requirements; adding password-reset/change flows
is deferred unless needed to preserve an existing supported journey.

The roadmap also includes a navigation bar, comments, ratings, and favorites
lists. The navigation bar belongs to this migration's shared shell. Comments,
ratings, and favorites are planned follow-up features: this migration establishes
reusable patterns for them; their models, routes, and user journeys are not yet
part of its acceptance scope.

Acceptance criteria are tracked in [criteria.md](criteria.md). Check off criteria
only after recording the associated implementation or verification evidence.

## Current architecture and findings

- `bookEx/settings.py` configures Django templates in `bookEx/templates` and
  static discovery in `bookEx/static`; `STATIC_ROOT=BASE_DIR / "staticfiles"`
  collects deployment output separately. `STATIC_URL="/static/"` is absolute.
- `bookEx/templates/base.html` owns the banner, navigation, content, footer, and
  authentication controls. It loads `dist/main.css` and `dist/main.js` once via
  static tags; JavaScript uses a module script. Nested-request rendering verified
  absolute bundle URLs.
- `bookMng/` owns book models, views, URLs, and `BookForm`; registration uses
  Django's `UserCreationForm` and login uses Django authentication views.
- The thirteen templates in scope are `base.html`, nine `bookMng/*.html`
  templates (including inbox, compose, and thread), and three
  `registration/*.html` templates, listed below. The mark-read action has no
  separate template; its redirect and feedback are also in scope.
- Private messaging already has `MessageThread`/`PrivateMessage` models, migration
  `0003`, and login-protected inbox, compose, thread/reply, and mark-read views.
  Compose/reply use native POST fields rather than Django form classes. Preserve
  participant authorization, recipient selection, message order, and read state.
- Legacy stylesheets have been consolidated into `frontend/src/main.css` and
  removed from source static files. The legacy design still exists in that bundle;
  presentation tables, inline styles, and image-only actions still need migration.
- `frontend/` now contains strict TypeScript configuration, an npm lockfile, Node
  version file, build/watch scripts, and generated output in `bookEx/static/dist/`.
  `src/main.ts` imports selected PF6 CSS and progressively focuses error summaries.
  `bookMng/tests.py` has six server regression cases and two opt-in browser cases.
- Login and post-book now use core 6.7.0 cards/alerts and shared native-field markup
  in `includes/form_fields.html`. Passwords, CSRF, `next`, and multipart upload
  remain owned by Django; the prototype works with JavaScript disabled.
- Book links use relative URLs in places. Book image paths are derived in views
  and resolved as static assets; inspect actual image storage before changing
  that behavior. The existing delete view mutates data on GET and lacks an
  ownership check; replacing its action must include a protected POST flow.

## Reviewed route and state inventory (November 7, 2026)

This is a source inventory, not a completed browser or end-to-end baseline.
Routes come from `bookMng/urls.py` and `bookEx/urls.py`; access and state behavior
come from `bookMng/views.py`, the models, and the templates.

| Route / URL name                                                   | Current access and states to preserve or verify                                                                                                                                    |
|--------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `/` / `index`                                                      | Public home; database-backed navigation and auth controls                                                                                                                          |
| `/postbook` / `postbook`                                           | Login required; blank/invalid multipart form, upload, success query flag                                                                                                           |
| `/displaybooks` / `displaybooks`                                   | Login required; populated/empty listing; empty feedback currently absent                                                                                                           |
| `/book_detail/<book_id>` / `book_detail`                           | Public detail and image; missing book currently raises an uncaught model exception                                                                                                 |
| `/mybooks` / `mybooks`                                             | Owner-filtered listing; no login decorator; anonymous access needs a baseline check                                                                                                |
| `/book_delete/<book_id>` / `book_delete`                           | Currently unprotected deletion including GET; replace with protected POST and confirmation                                                                                         |
| `/register` / `register`; `/register/success` / `register-success` | Public registration, validation errors, success page                                                                                                                               |
| `/login/` / `login`; `/logout/` / `logout`                         | Django auth; invalid/valid login and `next`; logout uses a CSRF-protected POST                                                                                                     |
| `/inbox/` / `inbox`                                                | Login required, GET only; own conversations, latest preview, timestamp, unread count, empty inbox                                                                                  |
| `/compose/` / `compose_message`                                    | Login required, GET/POST; optional `?user_id=` preselection, recipient list excluding self, send, missing recipient, blank/whitespace body, self-send rejection, unknown recipient |
| `/thread/<thread_id>/` / `thread_detail`                           | Login required, GET/POST; participants only (404 otherwise), ordered messages, empty thread, reply, blank reply, success; GET marks incoming unread messages read                  |
| `/thread/<thread_id>/mark-read/` / `mark_thread_read`              | Login required, POST only, participants only; incoming messages marked read, feedback and redirect; GET must return 405 for authenticated users                                    |

Other built-in auth routes remain subject to the scope exclusion above; `/admin/`
is excluded. Messaging here means existing server-rendered private conversations;
WebSockets, polling, live notifications, attachments, and new chat features are
not required.

Read-only local database inspection found six menu records: Home, Post Book,
Display Books, My Books, Compose Message, and Inbox. The last two store relative
`compose/` and `inbox/` links. Preserve the menu entries while resolving known
application destinations to named URLs, including on thread routes and invalid
compose responses. Do not assume local database records exist in a clean checkout.

Image inspection found `Book.picture.upload_to='bookEx/static/uploads'`, no
`MEDIA_ROOT`/`MEDIA_URL`, and views slicing `picture.url[14:]` for static lookup.
Both local book records reference existing files. The existing
`bookEx/static/uploads/InitialD10.jpeg` is an available baseline image fixture;
its current derived static path is `uploads/InitialD10.jpeg`. Automated upload
checks must still use isolated temporary storage and data.

Known baseline defects to cover during migration:

- `mark_thread_read` redirects to `messagingbox:thread_detail`, but no such URL
  namespace is registered. Direct URL reversal reproduces `NoReverseMatch`;
  the action updates read state before this redirect fails.
- Messaging views enqueue Django success/error messages, but no current template
  renders them. Add shared accessible feedback without double-rendering notices.
- Invalid compose renders omit `item_list` and discard the submitted message body.
  Blank replies redirect and also discard input. Define and verify useful error
  feedback and retain compose recipient/body values on validation failure.
- Relative menu links break navigation on nested routes. Existing book deletion
  remains unsafe, and missing-book/anonymous-my-books behavior needs baseline
  verification; these are not completed fixes.

Review evidence: all thirteen templates, URLconfs, views, forms, models, settings,
stylesheets, ignore rules, and the placeholder `bookMng/tests.py` were inspected.
`python manage.py check` passed with zero issues under Django 6.1. Read-only SQLite
inspection confirmed menu/image records and existing threads/messages; no messages
were sent or marked read. URL reversal confirmed all four messaging URL names and
the broken namespaced redirect. No browser journey, upload test, regression suite,
or frontend build has been run for this review.

## Target architecture

```text
bookEx/                         # Repository root
├── manage.py
├── bookMng/                    # Python models, views, forms, tests
├── bookEx/
│   ├── settings.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── includes/           # Navigation, fields, feedback, book-list markup
│   │   ├── bookMng/
│   │   └── registration/
│   └── static/
│       └── dist/              # Generated bundle, CSS, referenced assets
├── frontend/
│   ├── package.json
│   ├── package-lock.json
│   ├── .nvmrc                 # Supported Node LTS selected at implementation
│   ├── tsconfig.json          # Strict checking; esbuild emits browser output
│   ├── build.mjs              # Minimal Node/esbuild configuration
│   └── src/
│       ├── main.ts            # Typed component imports and UI setup
│       └── main.css           # Framework imports and small app overrides
├── staticfiles/               # collectstatic output; ignored
└── .ai/feat/pf/
    ├── pf.md
    └── criteria.md
```

Request flow: Django view -> template and shared includes -> browser loads local
bundled CSS/JS -> optional progressive enhancement. HTML forms submit to Django; the
frontend does not duplicate application state or validation rules.

Asset flow: `npm ci` in `frontend/` -> `npm run build` (typecheck, then bundle) ->
`bookEx/static/dist/` -> Django `collectstatic` -> configured static file server.
The Python deployment needs the built assets, not a running Node process.

## Technical decisions

1. **TypeScript and esbuild.** Use TypeScript for application frontend source,
   with `src/main.ts` as the entry point. Enable `strict`, `noEmit`, and
   `isolatedModules` in `tsconfig.json`, with DOM libraries and bundler-compatible
   module resolution. Align the TypeScript/esbuild browser targets. Node remains
   development/build tooling; retain `build.mjs` as minimal bundler configuration.
   React, a SPA, and a separate API remain outside this feature.
   `npm run typecheck` runs `tsc --noEmit`; `npm run build` must pass typechecking
   before bundling. esbuild strips types but does not check them. Provide
   `typecheck:watch` alongside bundle `watch` during development. Narrow nullable
   DOM queries and event targets, use package-provided component types, and avoid
   unchecked casts or blanket `any` declarations. Verify component declarations
   and CSS-import typing during the compatibility prototype; document narrow
   declaration shims only where required. Types do not replace runtime checks
   for external data or Django's server-side validation.
2. **Local, reproducible assets.** Use `@patternfly/patternfly` 6.7.0 core CSS,
   TypeScript, and esbuild. The user's install replaced the Elements package. Commit `package-lock.json`, pin
   selected direct dependency versions, and document Node/npm versions. Use
   `npm ci` for clean installations. No production CDN/import-map dependency.
3. **Compatibility gate before broad migration.** The prototype uses pinned
   core 6.7.0 CSS with its matching `pf-v6-*` HTML APIs. Selective imports cover
   variables, card, alert, form, form control, and button. Browser checks prove
   native password/file/submit behavior and consistent component styling at three
   widths. No Elements/core major mixing is introduced. Custom components remain
   optional; validate their versions, declarations, form association, and fallback
   behavior separately before adding them.
4. **One global entry point initially.** Import only components used by the app.
   Produce stable `main.js` and `main.css` filenames with no code splitting
   initially, plus locally emitted fonts/icons if required. Validate any asset
   references against the eventual static storage backend. Revisit splitting
   only if measured bundle size warrants it.
5. **Django owns integration.** Load assets once using `{% load static %}` and
   `{% static 'dist/main.js' %}` / `{% static 'dist/main.css' %}`. Use named Django
   URLs. Preserve CSRF, login `next`, bound form values, message recipient/body
   fields, field names, multipart encoding, uploads, errors, and Django validation.
6. **Native form semantics first.** Prototype custom-element form participation
   before adopting custom text inputs/buttons. The verified PF6 prototype uses
   native inputs, password/file inputs, and submit buttons with PF6 wrapper markup.
   Forms submit without JavaScript; only error-summary focus is enhanced. Avoid
   duplicate named hidden fields or click handlers that bypass native submission.
7. **Shared design patterns.** Centralize shell/navigation and field/help/error
   markup in small includes. Use documented tokens, CSS variables, and supported
   component styling hooks; do not reach into shadow DOM internals. Keep custom
   CSS limited to application layout, responsive behavior, and necessary branding.
8. **Safe output and actions.** Keep template autoescaping. Do not interpolate
   user content (including message bodies/previews and usernames) into executable
   JS or inject it through `innerHTML`. Change book deletion to CSRF-protected POST with login and ownership enforcement as part
   of the action migration. Keep other backend changes limited to integration
   needs or separately documented defects. Fix the messaging redirect, feedback,
   and invalid-compose context/value defects while preserving participant access
   and POST/CSRF protections.
9. **Generated output is not source.** Ignore `frontend/node_modules/`, generated
   bundles, and `staticfiles/`. Existing `dist/` ignore coverage must be verified.
   Never clean all of `bookEx/static/`; a rebuild may replace only its `dist/`.
10. **Deployment boundary.** Set `STATIC_ROOT` outside source static directories.
    Build before collecting static assets. Use the project's production static
    serving solution; Django's development server is not a production strategy.
    Document cache invalidation for stable bundle filenames on each release.

## Preparing for upcoming features

Build the shared shell and reusable patterns before migrating individual pages.
Extract includes where current pages already share markup; document extension
points for future features without building unused widgets or speculative models.

| Feature         | Preparation during PatternFly migration                                                                                                                               | Follow-up implementation                                                                                                                                        |
|-----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Navigation bar  | One responsive primary navigation bar with named links, active states, account actions, and keyboard-accessible mobile expansion; preserve existing menu destinations | Add new destinations when their routes exist                                                                                                                    |
| Comments        | Reuse messaging typography, author/time presentation, multiline text, textarea fields, and feedback patterns; keep private-message permissions separate               | Define comment target, visibility, edit/delete permissions, ordering, and any moderation requirements; add Django models/forms/views/tests                      |
| Ratings         | Document a native radio/select approach with explicit numeric labels and a textual summary; do not assume a dedicated Elements rating component exists                | Decide rating scale, eligibility, one-rating-per-user rules, editing, and aggregate display; enforce rules in Django and database constraints where appropriate |
| Favorites lists | Extract the common book-list markup, empty-state, and action patterns from current listings                                                                           | Decide single versus multiple lists and visibility; implement user-owned membership, duplicate prevention, add/remove POST actions, and tests                   |

For future ratings and favorites, begin with normal CSRF-protected Django forms.
Optional TypeScript-authored browser behavior may enhance those actions after the server-rendered behavior
works; Django remains authoritative for permissions, validation, and persistence.
Private conversations and public comments can share presentation conventions
without sharing authorization logic or being forced into one generic component.

Suggested delivery order: complete the migration and existing-journey checks,
then favorites, ratings, and comments as separately scoped features. That order
is provisional; product priorities may change it. Define each feature's rules
before selecting its schema or adding routes. Future feature controls and menu
links appear only when the corresponding functionality exists.

## Page and component mapping

| Template/surface                     | Planned PatternFly treatment                                                                                                                                           |
|--------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `base.html`                          | Consistent masthead, responsive primary navigation bar, main landmark, footer, active link, account controls; compatible HTML/CSS patterns and native navigation links |
| `bookMng/index.html`                 | Welcome content in a card with clear links to existing book journeys                                                                                                   |
| `bookMng/displaybooks.html`          | Accessible table or supported table component, linked book titles, readable prices/dates, empty state                                                                  |
| `bookMng/mybooks.html`               | Same table pattern, destructive action button with confirmation, empty state                                                                                           |
| `bookMng/book_detail.html`           | Card and semantic description list, image with useful alternative text, book metadata and website link                                                                 |
| `bookMng/postbook.html`              | Shared field pattern, help text, field/non-field errors, native upload, submit control, success alert                                                                  |
| `bookMng/book_delete.html`           | Consistent success alert and return action after protected deletion                                                                                                    |
| `bookMng/inbox.html`                 | Conversation cards/list with latest preview, author, timestamp, unread badge, compose action, and empty state                                                          |
| `bookMng/compose.html`               | Shared form styling for recipient select and message textarea, preselection, retained values, accessible validation feedback, CSRF, send and inbox actions             |
| `bookMng/thread.html`                | Semantic ordered conversation, sender/time, escaped multiline text, reply form, empty state, POST mark-read control, shared success/error feedback                     |
| `registration/login.html`            | Accessible form, password control, errors, registration link, preserved `next`                                                                                         |
| `registration/register.html`         | Same field pattern, password guidance, Django validation feedback                                                                                                      |
| `registration/register_success.html` | Success alert and login action                                                                                                                                         |

Current component choice: PF6 HTML/CSS card, alert, form, form control, and
button. Messaging can use semantic lists and native select/textarea with the same
core CSS. A dedicated chat component is not assumed. Future interactive Elements
remain conditional on a compatible styling/API proof; they are not required for
the current native prototype. A modal is optional if accessible server-rendered
confirmation is simpler; either must support keyboard operation.

## Phases

### 1. Foundation

Inventory routes and states; establish baseline journeys and image behavior.
Select compatible dependency versions and prove one component and one real
Django form. Add the isolated npm build, local static integration, shared shell,
and developer instructions. Exit when a clean build produces locally served
assets and the form prototype submits correctly.

### 2. Implementation

Build the navigation bar and reusable field, feedback, and book-list markup
first. Migrate all mapped pages, replace
legacy presentation styles, correct migrated links, and implement protected
deletion. Migrate inbox, compose, and conversation/reply/read controls, including
shared Django message feedback. Cover success, empty, validation-error, authenticated,
anonymous, and nonparticipant states. Exit when every page has a completed
component mapping and existing journeys work through the new interface.

### 3. Test/polish

Run focused Django and browser checks, validate build/collection from a clean
checkout, review accessibility and responsive layouts, and remove obsolete
styles/assets after confirming references. Record results against criteria.
Exit when all required criteria pass or any blocker is explicitly unresolved;
deferred enhancements do not substitute for required work.

### 4. Follow-up features and deferred work

Comments, ratings, and favorites lists are planned follow-up features, each with
its own acceptance criteria and Django regression coverage. Their implementation
does not block completion of this migration; preparation is covered by task 34.
The navigation bar is already required by task 11.

Other deferred work:

- SPA/API architecture, React, and custom web component development.
- Dark-mode switch, theme editor, advanced animation, and custom branding work.
- New search/filtering, sorting, pagination, or dashboard features.
- Realtime chat transport, polling, live notifications, message attachments, and
  other messaging features beyond the existing routes and behavior.
- Additional password-management screens and Django admin theming.
- Code splitting and advanced asset manifests unless measurements require them.
- A separate media-storage redesign and unrelated backend refactors. Existing
  image display and upload behavior must still pass the migration checks.

## Remaining tasks

Checked items have source/review evidence recorded above. Unchecked items remain
pending; partial tasks list completed subtasks explicitly. Execute foundation
before migration, then test/polish; messaging tasks 31–33 belong to implementation
and precede test/polish. Task 34 covers shared-pattern preparation during
implementation. Existing task numbers are retained for reference. Update this
plan with versions and verification evidence.

### Foundation tasks

1. [x] Inventory every template/route and its source-defined access/states, including
   messaging, login redirects, menu records, empty lists, and invalid forms.
   Evidence: reviewed route/state inventory above; runtime journeys remain task 2.
2. [ ] Capture baseline behavior for registration, login/logout, posting with an
   image, listing/detail, deletion, and inbox -> compose -> thread/reply -> mark-read.
   Include anonymous redirects, nonparticipant rejection, unread counts, invalid
   recipient/body, and self-send rejection. Identify existing failures separately.
3. [ ] Verify image upload/display through the migration.
   - [x] Inspect actual storage/references and identify an existing baseline image
     fixture (see image inspection above).
   - [x] Prove prototype upload persistence with isolated test data and temporary
     storage (`test_upload_and_success_with_isolated_storage`, both browser cases).
   - [ ] Verify listing/detail image display through the migration.
4. [ ] Select supported Node LTS/npm, core CSS, TypeScript, and esbuild versions.
   Current toolchain: Node 26.13.0 (`.nvmrc`), npm 11.20.0, TypeScript 7.0.2,
   esbuild 0.28.2, and pinned core 6.7.0. PF6 native compatibility is proven by
   task 9; Elements is no longer installed. Other direct package ranges still
   use `^`, so full exact pinning/toolchain alignment remains pending.
5. [x] Create `frontend/package.json`, lockfile, Node version file, `src/main.ts`,
   `src/main.css`, `tsconfig.json`, and `build.mjs`. Add `typecheck`,
   `typecheck:watch`, `build`, and `watch` scripts. Require strict typechecking
   before production bundling; document both watch processes for development.
6. [x] Configure deterministic `main.js`/`main.css` output and required asset
   loaders. Restrict cleanup to generated `bookEx/static/dist/` output.
7. [x] Add ignore rules for npm dependencies and collected output; verify generated
   assets are ignored while source and lockfiles remain tracked.
8. [x] Configure `STATIC_ROOT`, load local output with Django's static template tag,
   and verify no relative static URLs remain in the shared base.
   Evidence for tasks 5–8: committed frontend source/configuration; ignore checks;
   build and temporary-fixture watch/asset/cleanup checks; nested-request template
   rendering; `python manage.py check` and `collectstatic --noinput` (137 files).
9. [x] Render real PF6 cards/alerts on login and post-book; prototype native Django
   forms with errors, Enter-key submission, password input, and multipart upload.
   Decision: use core HTML/CSS plus native controls for this prototype, matching
   the user's replacement of Elements with core 6.7.0. Strict TypeScript checks
   CSS imports via a CSS-only declaration and nullable DOM access without `any`.
   Evidence: six Django regression cases and two isolated Chrome cases (with and
   without page JavaScript) passed. Component JS declarations/custom-element
   form association are inapplicable to this choice and require future proof if
   Elements is reintroduced. See prototype verification below.
10. [ ] Document and verify setup/build/watch/deployment workflows.
    - [x] Add [README.md](../../../README.md) covering Python/Node setup,
      build/typecheck and both watchers, Django startup, static integration,
      build-before-collectstatic release order, static serving, cache invalidation,
      and current deployment gaps (November 7, 2026).
    - [ ] Verify a fresh dependency installation and end-to-end production static
      serving after task 8; deployment instructions currently describe required
      configuration, not a completed deployment.

### Implementation tasks

11. [x] Build the shared shell: viewport metadata, skip link, masthead, account
    actions, responsive primary navigation bar, active state, content landmark,
    and footer. Use one shared set of destinations across desktop/mobile layouts;
    mobile expansion exposes its state and works with keyboard controls.
    Evidence (November 8, 2026): base shell, shared navigation/account includes,
    navigation context processor with empty-database defaults, PF6 masthead/nav
    imports, responsive toggle with no-JS fallback, current links, and dynamic-year
    footer. `npm run build` passed; all 18 Django/Chrome tests passed, including
    skip focus, toggle/Enter/Escape, resize focus, active routes, account CSRF/logout,
    and existing forms/uploads with JS enabled/disabled. Contracts are in README.
12. [ ] Extract reusable navigation and field/error/help includes. Preserve supplied
    `item_list` navigation and the auth pages' Home navigation without duplication;
    include Inbox/Compose and preserve navigation on invalid compose renders.
    Keep known route resolution and active-state logic in one shared location;
    do not render links to future features before their routes exist.
13. [ ] Migrate home to the shared page/card treatment and existing named URLs.
14. [ ] Migrate display-books and my-books to one accessible table pattern with
    headings, title links, consistent values, empty states, and narrow-screen handling.
    Share repeated book-list markup with explicit context for page-specific actions
    so a future favorites list can reuse it.
    - [x] Apply PF6 card/striped responsive tables, column headings, named detail
      links, and empty states to both lists (`24539a4`, `e35887b`, `8e6f8bb`).
      Both consume `frontend/src/book-list.css`, including the named PF table
      container. My Books now shows the posted date and a labeled Delete action.
    - [ ] Extract duplicated table markup into a shared include with explicit
      page/action context; verify My Books populated/empty and responsive states.
15. [ ] Migrate book detail to a card/description list; preserve image rendering,
    add alternative text, and render a usable, safely escaped website link.
    - [x] Add PF6 card/table markup and a book-specific document title, retaining
      the existing static image lookup (`8e6f8bb`).
    - [ ] Replace the table with the planned description list, correct the copied
      "My Books" heading, add image alt text, and make the website a safe usable
      link. Image rendering has source evidence only, not a browser display check.
16. [x] Migrate post-book from `form.as_table` to shared field markup. Preserve
    multipart POST, CSRF, field names, validation, bound values, upload, and success.
    Evidence: task 9 server/browser checks and shared `includes/form_fields.html`.
17. [x] Migrate login and registration using the shared form pattern; retain password
    help, field/non-field errors, CSRF, `next`, and normal keyboard submission.
    Evidence: login was migrated in task 9; `7524e17` migrates registration to
    `includes/form_fields.html`, PF6 card/form/button markup, and native POST.
    Source review confirms CSRF, the existing `next` field, Django-rendered
    password/help/error fields, and a native submit button. Registration-specific
    valid/invalid POST and browser journeys remain part of tasks 22/24/25.
18. [ ] Migrate registration-success and book-delete feedback to consistent alerts
    and useful return links; apply the same feedback pattern to post-book success.
19. [ ] Replace the image-only delete link with a labeled destructive action and
    accessible confirmation. Require authenticated ownership and CSRF-protected
    POST server-side; GET must not delete, and cancellation must change nothing.
    - [x] Replace the image with a PF6 danger/secondary Delete link and a
      book-specific accessible label (`8e6f8bb`).
    - [ ] Implement confirmation/cancellation and protected POST deletion. The
      link still uses a relative URL and the existing view still deletes on GET
      without login or ownership checks; visual migration does not complete this.
20. [ ] Replace migrated hardcoded/relative internal links with named URL tags.
    Verify actions work from nested routes and respect existing access rules.
    - [x] Both book lists now reverse `book_detail` and `postbook` by name.
    - [ ] Replace the remaining relative Delete URL as part of task 19.
21. [ ] Remove obsolete inline/presentation attributes and replace legacy styling
    once migrated. Retain only documented layout/branding overrides/assets.
    - [x] Remove separate `styles.css`, `table_format.css`, and `message_box.css`
      files/references; their styles are consolidated into `frontend/src/main.css`.
    - [ ] Replace the legacy styles themselves and presentation attributes with
      verified PatternFly patterns; consolidation alone is not full adoption.
      `7524e17` removes the already-commented legacy CSS from `main.css`; this
      file is imported by the build entry (not `main.ts`). This cleanup does not complete the
      remaining home, messaging, success, or delete template migrations.

### Messaging implementation tasks (before test/polish)

31. [x] Migrate inbox to shared conversation cards/list, unread badges, previews,
    timestamps, compose action, and populated/empty states. Preserve own-thread
    filtering and current sort order.
32. [x] Migrate compose and reply using shared native select/textarea/submit
    patterns, preserving `user_id`, `body`, CSRF, preselection, line breaks, and
    participant-only replies. Retain invalid compose values/navigation and display
    useful validation feedback, including blank replies and self-send rejection.
33. [x] Migrate thread content and mark-read action; render Django messages through
    a shared accessible alert include. Correct the unregistered redirect to the
    existing `thread_detail` URL name. Preserve automatic incoming-message read
    marking on thread GET, explicit protected POST mark-read, read timestamps,
    and nonparticipant 404s. Verify feedback appears once after redirects.

### Shared-pattern preparation

34. [ ] Document the actual shared navigation, fields, feedback, and book-list
    include names and context contracts after extraction. Map future comments,
    ratings, and favorites to these patterns, and record unresolved product rules
    from the roadmap above. Verify reuse across existing pages. Keep future
    models/routes/widgets out of this migration; record this handoff as A9 evidence.

### Test/polish tasks

22. [ ] Add focused Django regression coverage for valid/invalid forms, login
    redirects and `next`, image upload, page/empty-state rendering, and deletion
    ownership/POST/CSRF behavior. Include messaging auth/participant checks, compose
    recipient/body validation and retained values, reply ordering, unread/read
    timestamps, POST-only mark-read and its redirect, escaped message output,
    and feedback/navigation on error renders. Use isolated data/temporary uploads.
23. [ ] Run Django checks and the regression suite after implementation; record
    commands, outcomes, and acceptance-affecting defects.
    - [x] Baseline `python manage.py check`: zero issues, Django 6.1, November 7, 2026.
    - [ ] Complete post-migration checks and regression suite. The current suite
      has 16 server tests and two opt-in browser cases; it is no longer a
      placeholder, but registration/detail/deletion/messaging coverage is incomplete.
24. [ ] Add focused browser coverage for custom-element upgrade, real form
    submission, upload, feedback, and deletion confirmation/cancellation. Use a
    lightweight browser test setup with documented prerequisites. Include compose,
    reply, feedback, mark-read, and nested-thread navigation/static loading.
25. [ ] Exercise the full register -> login -> post -> list/detail -> my-books ->
    delete -> logout journey, plus invalid login/registration/post submissions.
    Use two participants and an outsider for inbox -> compose -> reply -> mark-read;
    verify unread transitions, invalid sends, and unauthorized thread access.
26. [ ] Check keyboard navigation, labels/errors, focus visibility/order, modal
    focus if used, table semantics, contrast, zoom, and 360/768/1280px layouts.
    Check long message bodies/usernames, multiline content, unread labels, and
    reply controls; textarea Enter must retain normal newline behavior.
27. [ ] Verify required content remains usable while JS loads; choose explicit
    fallback behavior for critical controls if loading fails. Avoid hiding the
    entire page while waiting for custom elements.
28. [ ] From clean dependencies run `npm ci`, `npm run typecheck`, `npm run build`,
    Django checks/tests,
    and `collectstatic --noinput`; inspect emitted fonts/icons and nested-route
    asset loading through the intended production static configuration. Verify
    that a temporary deliberate source type error makes typecheck/build fail;
    restore valid source and confirm both succeed.
29. [ ] Check browser console/network for component errors, duplicate registration,
    missing assets, or external CDN requests. Record bundle sizes; optimize only
    if a concrete issue is found.
30. [ ] Complete the criteria checklist with evidence, record justified native
    control/component choices, and document remaining deferred enhancements.


## Build/static verification before the prototype (November 7, 2026)

- `npm run build` passed strict typechecking and emitted `main.css` (4,034 bytes)
  and an empty `main.js`; application/component imports are still pending.
- A temporary fixture using the actual build/config verified font emission,
  stale-output cleanup without touching uploads, watch rebuilds/source maps,
  deliberate type errors failing typecheck/build, and a successful restored build.
  The application's source files were not changed by these fixture checks.
- `python manage.py check` passed with zero issues. Build followed by
  `python manage.py collectstatic --noinput` copied 137 files into `staticfiles/`.
  Collected bundles match source output; Django admin CSS is present.
- A rendered base template for `/thread/123/` uses `/static/dist/main.css` and
  `/static/dist/main.js` with a module script, without treating JS as CSS.
- `git check-ignore` confirmed dependencies, generated bundles, and collected
  output are ignored; `git ls-files frontend` confirmed source/config/lockfile
  are tracked. Production serving and fresh dependency installation are unverified.

Foundation tasks 1 and 5–9 are complete; tasks 3 and 10 have completed subtasks.
Tasks 2, 4 and the remaining parts of 3/10 still require work. Documentation
is written, but task 10 includes fresh setup and production verification.

## Task 9 prototype verification (November 7, 2026)

- Core `@patternfly/patternfly` 6.7.0 supplies documented `pf-v6-*` card, alert,
  form-control, form, and button CSS. Only selected component styles are imported.
  Existing legacy CSS remains for other pages; its removal is a later task.
- `/login/?next=/postbook` and `/postbook` exercise real Django forms and server
  errors. `includes/form_fields.html` accepts a bound `form`, renders labels,
  help text, per-field errors with Django's described-by IDs, and a summary.
  Native fields keep names, types, bound values, CSRF, password non-redisplay,
  and upload semantics. No hidden-field mirroring or submission interception.
- `npm run build` passed strict TypeScript including side-effect imports;
  `src/css.d.ts` declares only CSS modules. `main.ts` has a nullable typed DOM
  query to focus the error summary; there are no custom-element declarations to
  shim and no untyped JS application modules.
- `python manage.py test bookMng.tests.PatternFlyFormTests`: six cases passed,
  including `next`, validation/escaping, isolated upload persistence, and CSRF.
- `BOOKEX_BROWSER_TESTS=1 python manage.py test bookMng.tests.PatternFlyBrowserTests`:
  two Chrome cases passed, with and without page JavaScript. Actual native Enter
  submission, password input, invalid credentials, missing-upload errors, linked
  field feedback, retained values, file selection/send, success, PF card styling,
  and no page overflow at 360/768/1280px were verified. No runtime exceptions or
  missing static responses were observed. These are focused checks, not a full
  accessibility/production-server or application-wide acceptance review.
- Build output: `main.js` 758 bytes, `main.css` 414,497 bytes, plus four local
  background SVG assets. The variables file includes core theme tokens; no bundle
  budget has been set. Build followed by `collectstatic --noinput` succeeded;
  every emitted bundle/SVG matches its collected copy.
- Follow-up: removed `novalidate` from both prototype forms. Native required,
  URL, number/step, and upload constraints show browser feedback and block invalid
  POSTs. `:user-invalid` applies PF error-border variables only after interaction,
  clearing the client state when valid. Chrome checks verify POST blocking,
  focus/message state, validity changes, and deliberately bypass constraints once
  to retain server validation coverage; both JS-enabled/disabled cases passed.
- Run instructions/prerequisites are in README.md. Browser data, credentials,
  uploads, and Chrome profile are temporary; the local database is not used.

## Last-four-commit review (November 8, 2026)

Reviewed `24539a4` (responsive striped listing), `e35887b` (My Books),
`8e6f8bb` (book detail and labeled delete action), and `7524e17` (registration
and removal of commented CSS). Task 17 is complete at the implementation level;
tasks 14, 15, 19, 20, and 21 have the partial evidence recorded above. No other
whole task is completed by these four commits.

Verification run against HEAD:

- `npm run build` passed strict typechecking and bundling.
- `python manage.py check` passed with zero issues.
- `python manage.py test` passed 16 server cases and skipped the two opt-in
  browser cases (18 discovered).
- `BOOKEX_BROWSER_TESTS=1 python manage.py test bookMng.tests.PatternFlyBrowserTests`
  passed both Chrome cases. The sandbox initially blocked the live server's local
  socket; the successful run used approved execution outside the sandbox.
  Coverage includes existing login/post/upload/shell flows and Display Books
  stripes, long titles, responsive column labels, named detail-link paths, and
  no horizontal page overflow at 360/768/1280px, with page JS enabled/disabled.
  It does not visit registration, My Books, or book detail, follow the detail
  links, verify actual cover-image display, or exercise deletion.

Remaining review findings: deletion is still the known unsafe GET flow; book
detail incorrectly says "My Books", lacks image alternative text, and renders
the website as plain text. Both lists duplicate their table markup. The added
upload JPEG is an asset change, not proof of an isolated upload/display test.
Application code was not changed during this review.

## Official references

- [Elements installation and module loading](https://patternflyelements.org/get-started/)
- [Elements component catalog](https://patternflyelements.org/components/)
- [PatternFly HTML/CSS development](https://www.patternfly.org/get-started/develop/)
- [PF6 card HTML](https://www.patternfly.org/components/card/html/)
- [PF6 alert HTML](https://www.patternfly.org/components/alert/html/)
- [esbuild TypeScript support and typechecking boundary](https://esbuild.github.io/content-types/#typescript)
- [TypeScript noEmit with a separate bundler](https://www.typescriptlang.org/tsconfig/noEmit.html)

PatternFly references reviewed November 2, 2026; TypeScript/esbuild typechecking
guidance reviewed November 7, 2026. Recheck the selected release's documentation
during foundation; newer main-site examples may target a different major.

## Routing follow-up (November 7, 2026)

- `LOGIN_URL="login"` fixes default messaging redirects to the previously missing
  `/accounts/login/`. Anonymous users reach `/login/?next=...`, and sign-in returns
  an Inbox visitor to Inbox.
- My Books now requires login before filtering by user; authenticated ownership
  filtering is preserved.
- `MainMenu.get_absolute_url` reverses known application destinations and roots
  custom relative paths at Home. All nine book/messaging templates share
  `includes/sidebar_links.html`; existing menu data needs no migration or manual
  edits. Invalid compose responses also keep `item_list`.
- `MessagingLoginRedirectTests` and `NavigationRoutingTests` cover anonymous
  redirects, the login round-trip, own-book filtering, Compose/Inbox/Home/thread
  sidebar destinations, and both invalid-compose render paths. The full default
  suite passed twelve server cases and skipped two opt-in browser cases. Django
  checks pass; `makemigrations --check --dry-run` reports no schema changes.


## Messaging implementation verification (November 8, 2026)

Tasks 31–33 are implemented and verified. Inbox uses PF6 cards/list and unread
badges; compose/reply use native bound Django forms and the shared field include;
thread messages use an ordered list of cards with sender/time, escaped multiline
text, empty state, and protected mark-read action. `messaging.css` contains layout
and wrapping overrides; PF6 component CSS owns visuals. No custom elements needed.

- `ComposeMessageForm` preserves `user_id`/`body`, excludes self, supports GET
  preselection, and validates POST recipients/body. `ReplyForm` retains invalid
  reply input. Invalid forms render their errors once without queued duplicate
  notices. Unknown/malformed preselection returns 404; invalid POST recipients
  show actionable errors while retaining the body.
- `includes/message_form.html` accepts `form`, `action_url`, and `submit_label`,
  renders CSRF, and reuses `includes/form_fields.html`. Base renders
  `includes/feedback.html` once from Django `messages`, mapped to PF severity and
  status/alert roles. The README documents these contracts and extension points;
  task 34 still requires the shared book-list extraction and full feature handoff.
- The mark-read redirect now resolves `thread_detail`. Login, participant checks,
  POST/CSRF, read timestamps, thread GET incoming-only read marking, and existing
  inbox/message ordering are preserved. Invalid reply POST does not mark read.
- `bookMng/test_messaging.py` adds nine isolated server cases for inbox states,
  ordering/privacy, recipient/body validation, retained values, CSRF, safe output,
  send/reply, feedback consumption, participant rejection, and read transitions.
- Chrome covers native compose/send/reply/mark-read, feedback once after redirects,
  server errors/retained values, error focus, textarea Enter newline, unread
  transition, nested navigation/static loading, long usernames/messages and no
  overflow at 360/768/1280px, with JS enabled/disabled. No runtime exceptions or
  missing static responses occurred. Data/uploads/profiles are temporary.
- `npm run build` passed strict typechecking and bundling (CSS approximately
  599.4 KiB, JS 1.4 KiB, four local SVGs). Django checks, default server tests,
  and both opt-in Chrome cases passed. Full accessibility scanning, 200% zoom,
  complete application journeys, and production serving remain pending.

Navigation follow-up: the context processor now prepends canonical Home and
removes other entries resolving to its URL. Home appears first exactly once even
if database menu rows omit it, insert it last, or contain Home aliases; other
entries retain primary-key order. Server coverage checks omission, ordering,
deduplication, and shared auth-page navigation without modifying menu data.
