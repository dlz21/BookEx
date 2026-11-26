# Task: Favorite List Feature

Status: complete
branch: feat/fave-list

## Goal
We want to be able to easily add a book to our favorite list. Most sites use a
clickable heart or star icon to be able to favorite or unfavorite an
item(book). The user should also have a view to see all their listed favorites.

## Relevant context
- Files: `bookMng/models.py`, `views.py`, `urls.py`, `context_processors.py`,
  `migrations/0004_favorite.py`, `test_favorites.py`, shared favorite templates,
  `bookEx/templates/bookMng/favorites.html`, and `frontend/tests/forms.mjs`.
- Stick to PF provided icons if one exists
- Add a favorites route and menu link
  - The view should be a table with image, title, author, and action to remove from the favorites
  - Other views that show book actions should have a toggle-able icon to add/remove the book to the favorites.
- MVP interpretation: Book has no author field. The table shows the existing
  seller instead, without adding speculative author metadata. Titles link to details;
  books are ordered by title then primary key, with no filters or sort controls.
- out of scope: Lets got with an MVP approach to this feature.
  - Stick to PF provided icons if one exists
  - The favorites view/route should be simple
    - Non/limited filtering or sorting

## Acceptance criteria
- [x] Views that list books along with actions should now have a toggle-able icon
  — shared PatternFly stars on search, Display Books, My Books, and detail;
  server tests verify both states and Chrome verifies native keyboard submission.
- [x] Toggle the icon to "favorited" should add a book to the users favorites
  — authenticated, CSRF-protected add; repeated submissions do not duplicate rows.
- [x] Toggling the icon off, should remove the book from the users favorites
  — removal affects only the signed-in user; browser checks reach the empty state.
- [x] The "favorites" route and Menu item should be well named
  — `/favorites/`, named `favorites`, with a menu link even for custom menus.
- [x] The "favorites" route should list the users favorite books.
  — private responsive table with image/fallback, title, seller, and removal.

## Verification
Verified November 23, 2026 (local time), on `feat/fave-list`:

- `python3 manage.py check` — passed, zero issues.
- `python3 manage.py makemigrations --check --dry-run` — passed, no missing migrations.
- `python3 manage.py test bookMng.test_favorites` — 14 passed. Includes privacy,
  authentication, CSRF, HTTP methods, idempotency, uniqueness/cascade constraints,
  escaping, image fallback, redirect validation, state across pages, custom menus,
  and constant query count (four queries for one or six favorites).
- `python3 manage.py test` — 49 server tests passed, two opt-in browser tests skipped.
- `npm --prefix frontend run build` — strict TypeScript check and bundle build passed.
- `BOOKEX_BROWSER_TESTS=1 python3 manage.py test bookMng.tests.PatternFlyBrowserTests`
  — both Chrome cases passed with JS enabled/disabled. Includes keyboard add/remove
  through search/detail/favorites, My Books state, preserved search URL, empty state,
  and no page overflow at 360/768/1280px. Ran outside the sandbox because the live
  server requires a local socket. No separate manual browser review performed.
- Coverage.py 7.17.5, installed only under `/tmp/bookex-favorites-coverage`:
  `PYTHONPATH=/tmp/bookex-favorites-coverage COVERAGE_FILE=/tmp/bookex-favorites.coverage python3 -m coverage run --branch --source=bookMng manage.py test bookMng.test_favorites`
  followed by the same environment with `python3 -m coverage json -o /tmp/bookex-favorites-coverage.json`.
  All 40 added executable lines in the modified production Python modules were
  exercised. The new `_with_favorite_state`, `favorites`, and `set_favorite`
  functions have 17/17 statements and 8/8 branches covered (100%). This exceeds
  the 80% feature target; it is not a claim of 100% application-wide coverage.
- `python3 manage.py migrate` — applied only the pending `bookMng.0004_favorite`
  migration locally; test databases also apply it successfully.
- `git diff --check` — passed.

## Handoff
[Short handoff](../handoffs/favorite-list.md).
