# PatternFly success criteria

> **Archived — feature complete.** Closed on November 23, 2026 per maintainer
> confirmation. The plan, status notes, and checkboxes below are historical
> snapshots retained unchanged; they are not an active backlog or evidence
> that outstanding checks were rerun at closure. See [archive notes](README.md).

Status: build/static foundation partially verified November 7, 2026;
PF6 login/post-book prototype verified; remaining pages pending. Source plan: [pf.md](pf.md).

Check an item only when it is implemented and verified. Record evidence using
file paths, test names/results, build output, or a concise browser-review record.
All required items must pass to complete the feature. Deferred items in the plan
are excluded. Full application coverage includes every application-owned page
in the plan; Django admin and new password-management screens are excluded.
The navigation bar is required now. Comments, ratings, and favorites are planned
follow-up features; their implementation is excluded from this migration, while
shared-pattern preparation is required by A9.

## Clean architecture and integration

- [ ] **A1 — Django remains the application layer.** Views, models, authentication,
  validation, and persistence stay in Python; templates render the interface.
  No duplicate frontend business rules, SPA, or new API is introduced.
- [ ] **A2 — Clear source boundaries.** Frontend source/build configuration lives
  in `frontend/`; generated assets live in `bookEx/static/dist/`; template includes
  own shared navigation and field rendering. Generated output is not hand-edited.
- [ ] **A3 — Compatible versions.** Exact core CSS/toolchain versions and supported
  HTML/CSS APIs are documented, pinned, and proven together. Core 6.7.0 is pinned
  and the native prototype is proven; remaining toolchain ranges still need exact
  pinning. Any future Elements integration requires a separate compatibility proof.
  No unsupported mixing of PatternFly majors remains.
- [ ] **A4 — Centralized integration.** The base template loads local CSS/JS once
  through Django static tags. Internal application links use named URLs; nested
  routes load the same working assets.
- [ ] **A5 — Maintainable styling.** Shared tokens, supported hooks, and reusable
  patterns replace legacy page-specific presentation. Custom overrides have a
  clear layout/branding purpose; no shadow DOM internals are patched.
- [ ] **A6 — Django form contract preserved.** CSRF, field names, password fields,
  bound values, help text, field/non-field errors, login `next`, multipart upload,
  Enter-key submission, and server validation work through the new controls.
  Messaging retains `user_id`/`body`, recipient preselection, invalid compose
  values, and native textarea newline behavior.
- [ ] **A7 — Safe destructive action.** Deletion requires authenticated ownership
  and CSRF-protected POST. GET cannot delete; confirmation can be cancelled;
  unauthorized deletion is rejected without removing data.
- [ ] **A8 — Safe rendering.** User-controlled book/account/form/message values stay escaped
  and are not injected into executable code or unsafe HTML.

- [ ] **A9 — Shared patterns support planned growth.** Existing pages reuse
  navigation, field/error, feedback, and book-list patterns. Include names and
  required context are documented, along with extension points and unresolved
  product rules for comments, ratings, and favorites. Future features keep
  validation/permissions/persistence in Django. No placeholder routes, dead menu
  links, speculative models, or unused feature widgets are needed for acceptance.

## Build system and delivery

- [ ] **B1 — Reproducible install.** A clean checkout supports `npm ci` in
  `frontend/` with the documented Node/npm versions and committed lockfile.
  TypeScript is a pinned development dependency; application frontend source
  uses `.ts` files and a documented strict `tsconfig.json`.
- [ ] **B2 — Working scripts.** `npm run typecheck` runs `tsc --noEmit` with
  strict checking. `npm run build` checks types before esbuild produces the
  documented JS/CSS and dependent assets. A deliberate source type error fails
  typecheck/build, and both pass after restoration. `npm run watch` rebuilds
  bundles and `npm run typecheck:watch` reports type errors during development;
  both workflows are documented. Production builds leave no stale output and
  do not delete source static files. DOM/event and component typing uses narrowing
  and supported declarations; any narrow declaration shims are documented.
- [ ] **B3 — Dependency hygiene.** Only used component styles and any proven
  future Elements are imported; no complete catalog import, runtime CDN, or
  duplicate component registration is required.
  Bundle sizes are recorded for review.
- [x] **B4 — Repository hygiene.** Source/configuration/lockfiles are tracked;
  `node_modules`, generated bundles, and `collectstatic` output are ignored.
- [x] **B5 — Static collection.** `STATIC_ROOT` is separate from source static
  paths. Build followed by `collectstatic --noinput` succeeds and collects all
  required JS, CSS, fonts, and icons.
- [ ] **B6 — Deployable output.** Under the intended production static serving
  configuration, nested routes resolve assets without errors. Build/cache
  invalidation and deployment order are documented. Node is not required to run
  Django after the build artifacts have been delivered.
- [ ] **B7 — Developer instructions.** Setup, typecheck/build/watch, Django startup, checks,
  browser-test prerequisites, and deployment commands are documented and verified.

## Full application use of PatternFly

- [x] **P1 — Shared shell.** Masthead, navigation, account controls, content, and
  footer share the chosen PatternFly treatment across all pages, with a responsive
  primary navigation bar, active links, and a skip link. Desktop/mobile navigation
  uses the same destinations; mobile expansion has accessible state and keyboard
  operation. Existing menu destinations and account actions remain available.
  Evidence (November 8, 2026): shared base/navigation/account includes and shell
  CSS/TypeScript; `npm run build` and all 18 Django/Chrome cases passed. Coverage
  includes auth pages, database/default menus, query-independent current links,
  thread Inbox state, skip-link focus, mobile Enter/Escape/resize, CSRF logout,
  and forms/uploads at 360/768/1280px with JavaScript enabled/disabled. Broader
  content accessibility and zoom checks remain tracked under V4.
- [ ] **P2 — Home.** `bookMng/index.html` uses the shared shell/card treatment and
  working links into existing book journeys.
- [ ] **P3 — Listings.** `displaybooks.html` and `mybooks.html` use one consistent
  accessible table pattern with working detail links and meaningful empty states.
- [ ] **P4 — Detail.** `book_detail.html` presents book metadata, image/alternative
  text, and website link using a consistent card and semantic content structure.
- [x] **P5 — Posting.** `postbook.html` uses the shared form pattern, styled upload
  and submit controls, actionable errors, and consistent success feedback.
- [ ] **P6 — Authentication.** `login.html` and `register.html` use the same form,
  help, error, and action patterns while retaining Django authentication behavior.
- [ ] **P7 — Success pages.** `register_success.html` and `book_delete.html` use
  consistent alerts and useful follow-up links.
- [ ] **P8 — Complete component mapping.** Every surface in the plan is migrated.
  Supported PF6 native markup covers current interactions; future Elements
  require a compatibility proof. Native-control decisions are documented. Unrelated
  catalog components are not required for acceptance.
- [ ] **P9 — Legacy presentation removed.** Old stylesheet references, presentation
  tables used for forms/detail layout, inline branding styles, and image-only
  delete controls are removed or explicitly justified by a remaining use. This includes
  `message_box.css` and its page-specific button/card/bubble styling.

- [x] **P10 — Inbox.** `inbox.html` uses shared cards/list and badges for own
  conversations, latest previews, timestamps, unread counts, compose links, and
  meaningful empty states.
- [x] **P11 — Compose and conversation.** `compose.html` and `thread.html` use
  consistent recipient/message/reply controls, ordered messages with sender/time,
  escaped multiline text, empty states, mark-read POST action, and accessible
  success/error alerts. Compose validation retains recipient/body and navigation;
  feedback survives redirects and appears once.

## Verification and polish

- [ ] **V1 — Functional regression.** Django checks and focused regression tests
  pass for pages, valid/invalid forms, auth redirects, uploads, and protected
  deletion. Messaging checks cover login redirects, participant authorization,
  recipient/body validation, self-send rejection, reply order, unread/read
  timestamps, automatic read on GET, explicit POST-only mark-read, its corrected
  redirect, and safe output. Tests use isolated data/uploads and do not depend on `db.sqlite3`.
- [ ] **V2 — Browser behavior.** Focused browser checks pass for component upgrade,
  native/custom form participation, upload, feedback, and deletion confirmation.
  The complete register/login/post/list/detail/my-books/delete/logout journey works,
  as does inbox/compose/thread/reply/mark-read with two participants and an outsider.
- [ ] **V3 — Accessibility.** Manual keyboard review and an accessibility scan show
  no unresolved serious/critical issues on migrated pages. Labels, linked errors,
  table headings, landmarks, contrast, focus visibility, and confirmation focus
  behavior are checked; automated scanning does not replace manual review.
- [ ] **V4 — Responsive content.** At 360, 768, and 1280px and 200% zoom, navigation,
  forms, long titles, and actions remain usable. Wide tables use intentional
  accessible scrolling or responsive layout without clipping critical content.
  Long messages/usernames, multiline content, recipient selection, unread labels,
  and reply controls remain usable at the same sizes and zoom.
- [ ] **V5 — Loading and runtime.** Critical content is readable during module
  loading; essential actions have documented fallback behavior. Migrated journeys
  have no uncaught component errors, duplicate registrations, missing assets, or
  unexpected CDN requests.
- [ ] **V6 — Evidence and closure.** Each criterion has recorded implementation or
  validation evidence. Existing defects affecting a required criterion are
  resolved before completion; optional enhancements remain clearly deferred.

## Evidence record

Baseline review on November 7, 2026 covered all thirteen templates, routes,
views/models/forms/settings/styles and read-only local menu/image records; see
[the inventory and defects in pf.md](pf.md#reviewed-route-and-state-inventory-november-7-2026).
`python manage.py check` passed (Django 6.1, zero issues). Direct URL reversal
confirmed four messaging names and reproduced `NoReverseMatch` for the current
`messagingbox:thread_detail` redirect. These are baseline evidence, not completed
page-migration criteria. Build/static foundation checks below are now complete;
PF6 login/post-book integration and focused server/browser checks are now
verified as recorded below; broader application and production verification remain
pending.

| Criteria | Evidence / command / review | Result | Date |
| --- | --- | --- | --- |
| A1–A9 | Pending | Pending | — |
| B1, B3, B6 | Core 6.7.0 pinned, selected CSS imports verified; fresh install, remaining pins, final bundle review and production serving remain | Partial | 2026-11-07 |
| B2 partial | Actual build/config tested in a temporary fixture: build/watch, source maps, font emission, cleanup isolation, type-error rejection and restored build | Script behavior and native DOM/CSS typing passed; no custom component declarations are needed | 2026-11-07 |
| B4 | `git ls-files frontend`; `git check-ignore -v` for dependencies, bundles, and collected output | Passed | 2026-11-07 |
| B5 | `STATIC_ROOT` separate from source paths; build then `collectstatic --noinput`; 137 files, matching bundles and admin CSS verified | Passed for current assets; repeat when component fonts/icons are added | 2026-11-07 |
| P5 | PF6 post-book form, shared fields/errors, native file/submit, success alert; isolated Django and Chrome upload checks | Passed | 2026-11-07 |
| P1–P4, P6–P11 | Login portion of P6 implemented; registration and other page work remain | Pending | — |
| V1–V6 | Pending | Pending | — |
| Baseline only (V1 partial) | `python manage.py check`; source and read-only data inventory; messaging URL reversal | Check passed; redirect defect confirmed; migration verification pending | 2026-11-07 |
| B7 partial | `README.md`: setup/build/watch/deployment and browser prerequisites documented; six server and two opt-in Chrome cases passed | Fresh setup and production serving remain unverified | 2026-11-07 |
| A4 partial | Base template renders absolute CSS URL and module-script URL for a nested request; JS stylesheet tag corrected | Static integration passed; named internal links and browser serving still pending | 2026-11-07 |
| Task 9 / A3,A6,P6 partial | Core 6.7.0 native cards/alerts/forms; CSS-only declaration, typed nullable DOM query; six Django cases and two Chrome cases (JS on/off) passed | Prototype complete; full migration criteria still require remaining forms/pages | 2026-11-07 |
| V2,V4,V5 partial | Chrome: Enter login/post, invalid forms and retained values, file upload, success, PF card style, no overflow at 360/768/1280; no runtime/static response errors | Focused prototype checks passed; full accessibility/application review remains | 2026-11-07 |
| B3 partial | Prototype bundles: JS 758 bytes, CSS 414,497 bytes, four local background SVGs; all emitted files match collected copies | Sizes recorded; final app bundle review remains | 2026-11-07 |
| A6,V2 partial update | Native constraints enabled on login/post-book; Chrome verifies required/URL/price-step/upload feedback blocks POST, field validity clears, and server rejection remains after an intentional bypass; JS on/off passed | Immediate browser feedback verified | 2026-11-07 |


Messaging update (November 8, 2026): P10/P11 are implemented and verified; see
[implementation evidence](pf.md#messaging-implementation-verification-november-8-2026).
Nine isolated messaging server cases and two expanded JS-on/off Chrome cases cover
inbox empty/populated/privacy/order/unread state, bound native compose/reply forms,
preselection/validation/retained input, escaped multiline output, participant-only
access, CSRF, read timestamps, corrected mark-read POST redirect, and feedback
consumption. Browser checks cover textarea Enter, linked errors/focus, nested
navigation/static loading and long content at 360/768/1280px. These provide partial
A6/A8/A9 and V1/V2/V4/V5 evidence; application-wide criteria, accessibility scanning,
200% zoom, and production static serving remain pending. README records form and
feedback include contracts. No comments/ratings/favorites models or routes added.
