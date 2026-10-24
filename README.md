# Daily Love Notes

A small, self-hosted love-note app: an orange envelope opens into a letter, a glowing particle heart, and a note for the day. Includes a sleepy tabby, gentle animations, an installable web app, and optional daily-note widgets.

Two accounts keep the surprise intact:

- **Owner:** browse, search and edit all 365 notes.
- **Reader:** read only the note selected by the server for today.

The public repository contains **placeholder notes only**, generic usernames and example domains. It includes no personal collection, live account data, passwords, setup links, session tokens, signing keys, or deployment history.

## Run your own copy

Requires Docker Compose and an HTTPS reverse proxy or tunnel of your choice.

```sh
cp .env.example .env
# Edit .env: your public HTTPS origin, usernames, timezone and start date.
docker compose up -d --build
docker compose logs love-notes
```

Point your proxy/tunnel to `http://localhost:8096`. `PUBLIC_ORIGIN` must be the exact public HTTPS origin, without a trailing slash. Do not expose the Python development HTTP endpoint directly to the internet. Authentication cookies are always Secure, so use HTTPS for the browser-facing deployment.

On its first start, the server prints **two private, one-time setup URLs**. Open each privately to choose that account's password. They expire after 24 hours and become invalid once used. Do not publish or share startup logs. There are no default passwords. Login with the usernames in `.env` after setup. Configure usernames before first start; changing them later creates additional accounts rather than renaming existing ones.

If an unused setup URL expires, run `docker compose exec love-notes python server.py --renew-setup` to issue fresh links for accounts that do not have passwords yet. This does not reset existing passwords.

The `notes-data` Docker volume stores password hashes, sessions and editable notes. Back it up privately; preserve it on updates. Never commit it. `docker compose down -v` deletes that volume, including accounts and edits.

## Make it yours

- Edit messages through the owner account. All 365 included messages are visibly marked example text.
- Alternatively, change `dist/notes.js` **before the first start** to seed your own array of 365 strings. That seed is not downloadable through the backend. Keep personal seed files out of public Git history.
- Edit the greetings and intro in `dist/index.html` / `dist/app.js` and the colors in `dist/style.css`.
- `START_DATE` is day 1; `APP_TIMEZONE` determines midnight. The collection repeats every 365 days, independent of leap years.
- The backend uses Python's standard library and SQLite. No frontend bundler or JavaScript runtime dependencies are needed.

## Phone installation

The manifest provides an orange heart app icon and standalone display. In Safari on iPhone/iPad, use Share → Add to Home Screen. In Chrome on Android, use Install app / Add to Home screen.

The service worker caches only the static shell, never API responses or private notes. Offline mode shows the shell and a connection message. Android and iOS control installation behavior and background widget refresh timing.

## Optional widgets

Both widget clients connect with a single-use pairing code created by a signed-in user. Codes expire after 15 minutes. Widget tokens can read only today's note, expire after a year, and can be revoked using Disconnect My Widgets. They cannot browse or edit the collection.

### Android

Source: `android-widget/`. Requires JDK 17+, Gradle 8.11.1, Android SDK 35 and Build Tools 35.0.0.

```sh
cd android-widget
# Install Gradle separately or generate a wrapper with your installed Gradle.
gradle assembleDebug lintDebug -PserverOrigin=https://notes.example.com
```

Replace the example origin with your own. For production distribution, configure your own application ID and release signing; never commit signing keys. The debug build is for direct personal testing, not app-store release. To offer a download from your deployment, copy the APK to `dist/love-widget.apk` and rebuild the web container.

Open the companion, enter a pairing code, then add its widget to your home screen. It stores its read-only token with Android Keystore encryption. Background refresh is requested every 30 minutes; use its refresh button for a manual update. Tap the note to open the web app.

### iPhone / iPad

Uses the free **Scriptable** helper app rather than a separately signed native iOS app. Change the `origin` at the top of `dist/love-widget.js` to your deployment, copy the script into Scriptable, run it once, and enter a pairing code. Add a medium Scriptable widget and select the script. Credentials are stored in Scriptable Keychain. Physical-phone testing is required for your deployment.

The home-screen section in the app includes pairing and installation instructions. The Android download is available only after you build and deploy your own APK.

## Checks

```sh
python -m unittest test_auth -v
python check_public.py
```

Tests use a temporary database and test-only passwords. They cover account setup, login/logout, owner/reader permissions, server-side note selection, persistent edits, stale-edit conflicts, CSRF, blocked source/seed files, widget pairing and revocation.

## Privacy and limitations

Setup links, passwords, SQLite files and widget tokens are deployment secrets. Keep them private. Login/setup attempts are rate limited; trust `CF-Connecting-IP` only when your reverse proxy controls that header. If you deploy without Cloudflare, configure the proxy to overwrite that header or remove it so rate limiting uses the actual peer address. Session cookies last seven days and logout revokes them. Updating a note does not guarantee an instant home-screen widget refresh; the phone schedules that work.

This is a small personal app, not a general-purpose identity provider. There is no email, public registration, password-reset email, or analytics. Review your own deployment and test on your devices before relying on it.

## License

MIT. The original app code and included icon artwork are covered by [LICENSE](LICENSE). Google Fonts are loaded from their service; third-party tools and fonts retain their own licenses.
