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
