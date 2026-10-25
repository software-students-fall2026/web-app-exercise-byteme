# Three detail/delete user stories

Implemented locally on the `Uuree` branch. No commit, push, pull request or GitHub issue was created.

## 1. Hide possible matches for claimed items

**User story:** As a student viewing a claimed item, I want to see that it has already been claimed so that I do not spend time checking unnecessary matches.

**Acceptance criteria**

- Claimed items show “This item has already been claimed.” instead of match cards.
- This applies to the detail page and the expanded matches page.
- Open items still match open posts of the opposite type with the same category and building.
- Items missing matching fields show the existing empty-state message.

**How it works:** `match_query()` in `app.py` returns a matching query only when the current item is open and has the required type, category and building. Both routes use this helper. The detail and matches templates show the claimed message.

**Files:** `app.py`, `templates/detail.html`, `templates/matches.html`.

## 2. Show five recent matches with View more

**User story:** As a student searching for an item, I want to preview five recent possible matches and view more when needed so that the detail page stays easy to browse.

**Acceptance criteria**

- The detail page displays at most five matches, newest first.
- View more appears only when more than five matches exist.
- The expanded page preserves the same opposite-type, open-status, category and building filters.
- It displays ten results per page with Previous and Next links as needed.
- Invalid page numbers show a friendly 400 response.

**How it works:** The detail route fetches six candidates and displays five; a sixth candidate triggers the link. The new `/items/<item_id>/matches` route skips earlier pages and fetches eleven candidates, displaying ten and using the extra result to determine whether Next should appear. Creation time and item ID provide a stable newest-first order. Results link to item details.

**Files:** `app.py`, `templates/detail.html`, new `templates/matches.html`, and new `templates/400.html` for invalid input.

## 3. Protect delete submissions

**User story:** As a post owner, I want delete submissions checked against my current session so that an unrelated website cannot submit a deletion form on my behalf.

**Acceptance criteria**

- Login and ownership are still required on the server.
- GET only shows confirmation, and Cancel returns to the item.
- Confirmation includes a random token tied to the current session.
- Missing or invalid tokens return 400 and leave the document unchanged.
- A valid owner submission deletes the document, redirects home and shows the existing success message.

**How it works:** `csrf_token()` creates a random token in Flask's signed session. `templates/delete.html` submits it as a hidden field. `require_csrf()` compares the submitted and saved tokens before `items.delete_one()` can run. A friendly `400.html` explains an expired or invalid form. This protection is scoped to the delete flow; other existing forms are unchanged. A valid `SECRET_KEY` is required, as it already was for login and flash messages.

**Files:** `app.py`, `templates/delete.html`, new `templates/400.html`.

## File inventory

Added:

- `templates/matches.html`: expanded matching results and pagination.
- `templates/400.html`: invalid form/page-number message.
- `tests/test_detail_delete.py`: focused Flask route tests using an in-memory database.
- `requirements-dev.txt`: pytest and mongomock, separate from production dependencies.
- `docs/detail-delete-user-stories.md`: this guide.

Modified:

- `app.py`: shared match query, preview limit, paginated route and delete token checks.
- `templates/detail.html`: claimed-state message and View more link.
- `templates/delete.html`: hidden session token.
- `README.md`: new page, guide link and test instructions.

The earlier quick-claim, contact, Undo, custom 403, deletion-result and return-navigation additions were removed. Existing edit/delete ownership checks and permanent deletion behavior remain in place.

## Verification

20 tests passed using Flask's test client and an in-memory MongoDB substitute. They cover both matching directions, claimed states, pagination, match filtering, missing fields, invalid IDs and pages, owner/non-owner/guest access, missing and invalid tokens, GET confirmation and successful deletion. Tests disable `.env` loading before importing the app and do not access the shared database.

Run from the repository with the environment activated:

```sh
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

The available in-app browser failed to attach to the local preview, so visual/mobile layout has not been verified. Actual templates are rendered by the route tests.
