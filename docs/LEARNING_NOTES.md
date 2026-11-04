# Learning Notes

Raw notes written after each build task. Source material for the teaching phase.

---

## Stage 1 — Repo cleanup (2026-11-04)

### What was built
- New `.gitignore`: secrets (`.env`, `.env.*`, `*.pem`, `credentials.json`, `client_secret*.json`, `token.json`), Python (`venv/`, `__pycache__/`), DB files (`*.db`, `*.db-journal`, `*.sqbpro`), frontend (`node_modules/`, `dist/`).
- Stopped tracking `venv/` (8,796 files) and `tnp_agent.sqbpro`.
- `requiremnets.txt` renamed to `requirements.txt` and rewritten as direct dependencies only.
- Git history rewritten with `git filter-repo` to remove `venv/`, `tnp_agent.db` and `tnp_agent.sqbpro` from every commit. Pack size went from 90.66 MiB to 80 KiB.
- The Google OAuth client was replaced and Gmail was reconnected.

### What went wrong (the incident)
- `tnp_agent.sqbpro` is a DB Browser project file. It saves your SQL tabs, so it saved a Google client secret, an access token and a refresh token in plain text. It was committed in the Stage 6 commit, to a **public** repo.
- `tnp_agent.db` was committed earlier (Stage 5) with 128 real email bodies. No tokens: the `token_json` column did not exist yet.
- `.gitignore` listed `.venv/` but the folder was named `venv/`. One character, 8,796 files.

### Why this order: rotate first, then rewrite
- Rewriting history does **not** un-leak a secret. Anyone could have cloned the repo, bots scan GitHub for keys, and forks keep old commits. So the secret had to be made useless first (rotation). The rewrite only stops further exposure.
- Rotation here: the old OAuth client was deleted (Google likely auto-disabled it after detecting the leak). A refresh token belongs to the client that issued it, so deleting the client killed the leaked tokens too. The stored DB token was dead as well, so Gmail was reconnected through `/connect-gmail`.

### Key concepts
- **Untrack vs ignore:** `.gitignore` only affects files git does not track yet. A tracked file stays tracked until `git rm --cached`.
- **`git rm --cached`:** removes the file from git's index, keeps it on disk.
- **Why untrack before `filter-repo`:** filter-repo ends with a hard reset. If `venv/` was still tracked, the reset would have deleted the real virtualenv from disk.
- **History rewrite cost:** every commit hash changes, so a force push is needed and any other clone must re-clone. filter-repo also removes the `origin` remote on purpose, to stop an accidental push.
- **Direct vs transitive dependencies:** the old file was a `pip freeze` (59 lines, every sub-dependency) yet still missed fastapi, uvicorn, sqlmodel, APScheduler, PyJWT and pywebpush. The new file lists only packages the code imports, pinned to tested versions. pip resolves the rest.
- **Testing a requirements file:** the only honest test is a fresh venv. The working venv hides missing entries because the package is already installed.
- **`redirect_uri_mismatch`:** Google compares the redirect URI in the request with the list saved on the OAuth client, character by character (http vs https, localhost vs 127.0.0.1, port, trailing slash).

### Other options considered
- **BFG Repo-Cleaner** instead of filter-repo: also works, needs Java. filter-repo is what the git docs recommend.
- **Keep the full freeze** for exact reproducibility: a lock tool (pip-tools, uv) is the clean way to get both a short input file and a full lock file. Not needed yet.

### Known limits / follow-ups
- The scan after the rewrite was pattern-based. A secret in an unusual format could still be missed.
- GitHub may keep old commits reachable by hash for a while (cached views, forks). Rotation is what actually protects us.
- `CLAUDE.md` and `CLAUDE_CODE_PROMPT.md` are not committed (personal notes, public repo).
- Cookie flags and POST `/refresh-token` moved to Stage 2, together with the other auth fixes.

---

## Stage 2a — Pipeline reliability (2026-11-04)

### What was built
- **Gmail pagination:** `list_message_ids` follows `nextPageToken`. Live check: 417 emails were waiting since the bookmark; the old code took the newest 100 only.
- **Oldest first + per-run cap (`MAX_EMAILS_PER_RUN = 50`):** fetch all IDs, process the oldest 50, rest next run.
- **First sync window:** a new user (no bookmark) gets `newer_than:30d`, not years of mail.
- **Quote stripping:** the reply header must be a whole line ending in `wrote:` (one wrapped line allowed).
- **Push:** `webpush` was outside the loop (only the last device got it; zero devices crashed). Now every device is tried in its own `try`; 404/410 deletes the subscription.
- **Pipeline:** `process_user` per user inside `try` (one broken user no longer stops the others). Notify errors are caught too.
- **Retry cap:** a crash writes an extraction row with status `error` and `retry_count + 1`; after 3 attempts it becomes `failed_error` and is not retried. No schema change: existing columns reused.
- **Timezones:** one helper module `backend/timeutils.py` (`as_utc`, `to_ist`). Push deadline now shows IST.
- **Recency check fixed:** compares aware UTC datetimes. Applies to both passes.
- **`classify_node`** now gets the subject.
- `echo=True` removed from the engine (it printed every query with values, including email bodies).
- First pytest suite: 19 tests in `tests/`. `pytest.ini` limits collection to `tests/` so the manual root scripts never run.

### Why this design
- **The bookmark bug (most important).** Bookmark = newest saved `received_at`. Gmail lists newest first. If a run saves only the newest N, the bookmark jumps past the older ones and the next query (`after:bookmark`) never sees them. Fix: process oldest first. Then the bookmark only moves forward over emails already saved, and a capped or crashed run resumes where it stopped.
- **Why save the email before the LLM call:** if the LLM crashes, the email is already in the DB, so pass "stuck emails" finds it. Saving after the LLM would lose it (the bookmark already moved).
- **Why stuck pass runs first:** otherwise an email that fails in the new-email pass is retried again in the same run, using two of its three attempts at once.
- **Why a recency window for notifications:** "notify only brand-new emails" needs a definition. 1 hour after `received_at` is it. Catch-up runs (like these 417) send no pushes.
- **Why `as_utc` treats naive as UTC:** SQLite has no timezone type and returns naive datetimes. We always store UTC, so naive means UTC. The old code compared naive with aware and crashed with `TypeError`.

### Edge cases and limits
- Scheduler down for more than 1 hour: those emails are saved but never notified. Intended trade-off.
- `retry_count` now means two things: validation retries (on success) and crash attempts (on failure). Documented, not ideal.
- A missing `summary` raises a Pydantic error before `validate_node`, so it counts as a crash attempt, not a validation retry.
- Dedup is still global on `gmail_message_id` (unique constraint), not per user. Fine for Gmail in practice; revisit with Postgres.
- `MAX_EMAILS_PER_RUN` and `INITIAL_SYNC_DAYS` are guesses, not measured.
- VAPID `sub` claim is still a placeholder email. Fix at deployment.

### Testing
- Fake Gmail service with paging; in-memory SQLite with `StaticPool`; fake LLM and fake `webpush`.
- Tests set fake env keys before importing the backend; `load_dotenv()` does not override existing variables, so the real `.env` is never used.

---

## Stage 2b — Auth and security (2026-11-04)

### What was built
- **Login identity from Google.** `/oauth/callback` used to trust the `state` query value as the user's email. Anyone could open `/connect-gmail?email=victim@...`, log in with their *own* Google account, and get a JWT for the victim (and overwrite the victim's Gmail token). Now the callback asks Gmail whose token it is (`users.getProfile` → `emailAddress`) and logs in that account. No scope change: `gmail.readonly` already allows `getProfile`.
- **Random OAuth `state`:** `secrets.token_urlsafe(32)` stored in an `oauth_state` cookie for 10 minutes; the callback compares with `secrets.compare_digest` and deletes the cookie. This blocks login CSRF (an attacker making your browser finish *their* login).
- **Signup:** the callback now uses `get_or_create_user`, so a new Google account gets a user row. In Google "testing" mode only listed test users can get through consent anyway.
- **JWT `type` claim:** access tokens say `"access"`, refresh tokens `"refresh"`; `verify_token(token, expected_type)` rejects the wrong one. Before, a stolen 30-day refresh token worked as an access token.
- **One cookie helper** (`set_cookie`): `httponly`, `samesite="lax"`, `path="/"`, `max_age` equal to the token lifetime, `secure` from `COOKIE_SECURE` env (off on localhost, on in production).
- **`/refresh-token` is POST.** GET must not change state (browsers, prefetchers and link previews fire GETs freely). Frontend dashboard updated.
- **`get_current_user` dependency** replaces the copied cookie → JWT → DB lookup in `/notices` and `/save-subscription`.
- Callback handles `?error=access_denied` (user pressed Cancel) with a clear 400 instead of a 422.

### Key concepts
- **`state` vs PKCE:** `state` ties the callback to the browser that started the login (CSRF). PKCE ties the token exchange to the client that started it (code interception). We use a confidential client with a secret, so PKCE is optional here; `state` is not.
- **SameSite=Lax:** cookies are sent on top-level GET navigation from other sites (so the Google redirect back to us still carries `oauth_state`), but not on cross-site POST/fetch. That is why state-changing routes must be POST.
- **httpOnly:** JS cannot read the cookie, so XSS cannot steal the token. XSS can still *use* it while the page is open.
- **Secure:** cookie only sent over HTTPS. Must be on in production, off on `http://localhost` or the browser drops the cookie.

### Limits
- Logout still does not exist (Stage 3). Tokens cannot be revoked server-side; a stolen refresh token works for 30 days.
- Old cookies issued before this change have no `type`, so they are rejected once. The user just logs in again.
- Production cookie setup depends on hosting: if the frontend and API end up on different sites, `SameSite=Lax` cookies are not sent on `fetch` and we would need same-site hosting or `SameSite=None; Secure`. Decide in Stage 7.
- `REDIRECT_URI` and CORS origin are still hard-coded to localhost (Stage 7).

---

## Stage 3 — Login polish (2026-11-04)

### What was built
- **`apiFetch` (`frontend/src/api.js`):** one wrapper for every API call. Sends cookies; on 401 calls `POST /refresh-token` once and retries once; a second 401 fires an `auth:expired` event and throws `AuthError`. Parallel 401s share one refresh (a module-level promise), so three requests failing together cause one refresh, not three.
- **Auth context:** `AuthProvider` calls `/me` on load. Status is `loading`, `in`, `out`, or `error` (server unreachable — not the same as logged out, so we show "Try again", not the login page).
- **`ProtectedRoute` + `AppLayout`:** every page except `/login` is protected. Header with email and Log out lives in one layout, not on each page.
- **Login page** with "Continue with Google" and a line on what access is requested. Callback now **redirects** to the app (`/` on success, `/login?error=denied|state` on failure) instead of showing JSON.
- **`/me`** returns email and name. **`POST /logout`** clears both cookies.
- **Push subscriptions upsert by `endpoint`.** Same device twice = one row (keys updated). If another user logs in on the same browser, the row moves to them.
- **Notifications:** auto-prompt once after first login (remembered in `localStorage`), banner on Home for each permission state: not asked (button), blocked (how to unblock), unsupported. If already granted, the subscription is re-sent on each Home visit so the backend stays in sync.
- Dead (404/410) subscriptions were already handled in Stage 2a.

### Why these designs
- **Why `endpoint` is the key:** a subscription belongs to one browser on one device. One user has many devices; one device can be used by different users over time. `user_id` alone would duplicate rows every time the user clicks Enable.
- **Why the event for "session over":** `apiFetch` is plain JS and cannot call React state. The event lets any page's failed request update the auth context in one place.
- **Why `subscription.toJSON()`:** it already gives `p256dh`/`auth` as base64url strings, the format pywebpush expects. The old manual ArrayBuffer → base64 code is gone.

### Logout and JWT: the honest limit
- Logout deletes the cookies in *this* browser. The tokens themselves stay valid until they expire (access 15 min, refresh 30 days). If someone copied the refresh token, logout does not stop them.
- Options: (1) **short expiry** only — simple, still a 30-day window; (2) **server-side blocklist** of revoked token IDs (`jti`) checked on every request — works, but every request now hits a store, losing the "stateless" benefit; (3) **refresh-token rotation**: store refresh tokens (hashed) in the DB, issue a new one on every refresh and invalidate the old one; logout deletes the row; reuse of an old token signals theft and kills the whole session.
- **Recommendation: (3) rotation**, when we move to Postgres. Access tokens stay stateless (fast), only the refresh path touches the DB (rare), and logout becomes real.

### Edge cases and limits
- Auto-prompt without a click: Chrome may show a quiet prompt; Firefox and Safari usually require a click. The banner button covers this.
- Once "denied", a site cannot ask again; only the user can change it in browser settings.
- If `/me` fails because the server is down, we show "Can't reach the server" rather than logging the user out.
- `API_URL` defaults to `http://localhost:8000`; set `VITE_API_URL` in production. `FRONTEND_URL` is still hard-coded in the backend (Stage 7).
- Clicking a push notification does nothing yet (no `notificationclick` handler in the service worker).

---

## Stage 4 — Modern UI rewrite (2026-11-04)

### What was built
- **Stack:** Tailwind CSS v4 (Vite plugin), shadcn/ui components (Radix based: button, badge, input, skeleton, dropdown-menu), lucide-react icons, framer-motion, TanStack Query, sonner toasts, Geist font (from npm, no font CDN).
- **Design tokens once** in `src/index.css`: colours (oklch), radius, font, category accents. `.dark` overrides the same names, so every component is theme-aware for free.
- **Theme:** dark first, toggle remembered in `localStorage`. A tiny inline script in `index.html` applies it before React loads (no white flash). `useTheme` is a `useSyncExternalStore` store so the toggle and the toast theme always agree.
- **Pages:** landing/login (hero, Google button, feature cards, preview stack), Home (greeting, 3 stat tiles, notification banner, action cards, upcoming deadlines), Dashboard (sticky toolbar with search, category chips, sort; card grid; Load more; skeletons; empty and error states), Chatbot placeholder ("coming soon").
- **Header:** glass, sticky, animated active pill (`layoutId`), user menu with logout. Phones get a bottom tab bar.
- **Backend for the UI:** `/notices` with `limit/offset/category/q/sort` returning `{items, has_more}`; `/stats` for the tiles.

### Why these designs
- **TanStack Query** instead of `useEffect` + `useState`: caching (Home and Dashboard share data), `useInfiniteQuery` for Load more, `keepPreviousData` so old cards stay while a new filter loads (no layout jump), retries skipped for `AuthError`.
- **`queryClient.clear()` on logout:** cached notices would otherwise be visible to the next person using the browser.
- **Offset paging, not cursor** (changed from the proposal): simple and works for both sort orders. Limit: if new notices arrive between pages, items can shift (one shown twice or skipped). Cursor (keyset) paging fixes that but needs a different cursor per sort order.
- **`has_more` via `limit + 1`:** ask for one extra row; if it exists there is another page. No separate COUNT query.
- **`safeLink`:** `apply_link` comes from the LLM reading email text, so it is untrusted. Only `http(s)` URLs become links (blocks `javascript:` links), with `rel="noopener noreferrer"`.
- **Server-side search/filter:** filtering only the loaded page would miss older notices.
- **Blur only on a few surfaces:** `backdrop-filter` on 24+ cards is expensive to paint. Grid cards use a plain translucent `surface`; header, toolbar and panels keep the glass blur.

### Checked (in Chrome)
- Desktop 1536 px: login, home, dashboard (search "siemens", Internship filter, Deadline sort, Load more 12 → 24), light mode, error screen when the backend was down.
- Phone 375 px (iframe): login rendered; home and dashboard have no horizontal page scroll; the filter-chip row scrolls sideways on purpose. Phone screenshots of home/dashboard could not be captured (browser timeouts under low memory), so they were checked by measurement, not by eye.

### Limits
- JS bundle is ~190 kB gzipped (framer-motion + Radix). Route-level code splitting would help.
- `deadlines_next_7_days` counts only verified notices; one deadline field per notice.
- Name comes from the email address, not Google's profile (no extra scope).
- Chatbot page is a placeholder until Stage 6.
