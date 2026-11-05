# Posting setup

Two credentials, both of which only you can create, in `~/.config/carmodreview/`.
That directory is outside the repo, so nothing here can be committed by accident.

Nothing is uploaded until both are in place **and** the schedule is loaded.

---

## 1. YouTube

### 1a. Get the OAuth client (browser, ~6 minutes)

1. Go to <https://console.cloud.google.com/> and sign in as
   **officialcarmodreview@gmail.com** — the account that owns the channel. This
   matters: an OAuth client from a different Google account will authorise, then
   fail at upload with a permission error that does not say why.
2. Top bar → project dropdown → **New project**. Name it `carmodreview`, create.
   Make sure the new project is selected before the next step.
3. Left menu → **APIs & Services → Library**. Search `YouTube Data API v3`,
   open it, **Enable**.
4. Left menu → **APIs & Services → OAuth consent screen**.
   - User type **External**, create.
   - App name `Car Mod Review`, your email as support and developer contact.
     Everything else can stay blank. Save.
   - **Audience** → under *Test users*, **Add users**, add
     `officialcarmodreview@gmail.com`. Without this, authorisation is refused
     with `access_denied`.
5. Left menu → **APIs & Services → Credentials → Create credentials →
   OAuth client ID**.
   - Application type: **Desktop app**. Name it anything. Create.
   - **Download JSON**.
6. Save that file, with its downloaded name, to:

   ```
   ~/.config/carmodreview/youtube/client_secret.json
   ```

   ```bash
   mv ~/Downloads/client_secret_*.json \
      ~/.config/carmodreview/youtube/client_secret.json
   ```

### 1b. Authorise (one time, done together)

```bash
cd ~/carmodreview && .venv/bin/python upload.py --auth youtube
```

It opens a browser. Pick the channel's account, and click through the
"Google hasn't verified this app" warning via **Advanced → Go to Car Mod Review
(unsafe)**. That warning is expected for an unpublished app authorising its own
owner; it is not a sign anything is wrong.

The token is written to `~/.config/carmodreview/youtube/token.json` and refreshes
itself from then on.

**One caveat worth knowing now:** while the OAuth app stays in *Testing* mode,
Google expires refresh tokens after **7 days**. If uploads start failing after a
week, that is why — re-run `--auth youtube`. Publishing the consent screen (which
for a single-user upload app needs no review) stops the expiry.

### Quota

A video upload costs 1600 quota units against a default **10,000/day**. That is
six uploads a day, and the job does one. No action needed.

---

## 2. Instagram

The Graph API is genuinely fussier than YouTube's. Two hard requirements that
catch most people:

- The Instagram account must be **Business** (you've done this).
- It must be **connected to a Facebook Page**. A Business account with no Page
  cannot use the publishing API at all.

### 2a. Create the Meta app (~5 minutes)

1. Go to <https://developers.facebook.com/apps/> and sign in.
2. **Create app** → use case **Other** → type **Business**.
3. Name it `Car Mod Review`, attach it to a Business portfolio if prompted.
4. In the app dashboard, add the product **Instagram** → **API setup with
   Facebook login**.

### 2b. Link the Page to the Instagram account

1. Open the Instagram app → **Settings → Business tools and controls** (or
   *Account type and tools*) → **Sharing to other apps / linked accounts**.
2. Connect a Facebook Page. If you have no Page yet, create one — it can be an
   empty placeholder; it only exists to satisfy the API.

### 2c. Get the two values

Still in **Instagram → API setup with Facebook login**:

1. Under **Generate access tokens**, connect the Instagram account, grant
   `instagram_content_publish` and `instagram_basic`, and copy the token.
2. **Click "Exchange" next to it** to turn the 1-hour token into a
   **long-lived (60-day)** one. If you skip this, posting works today and fails
   tomorrow.
3. Above it, copy the **Instagram account ID** (a long number, not the @handle).

### 2d. Write the config file

```bash
cat > ~/.config/carmodreview/instagram.json <<'JSON'
{
  "ig_user_id": "PASTE_THE_NUMBER_HERE",
  "access_token": "PASTE_THE_LONG_LIVED_TOKEN_HERE"
}
JSON
chmod 600 ~/.config/carmodreview/instagram.json
```

**The 60-day expiry is real.** The token dies every two months and the daily job
will start failing. `upload.py` prints Instagram's own error when that happens.
Refreshing is one call:

```bash
curl -s "https://graph.facebook.com/v21.0/oauth/access_token?\
grant_type=fb_exchange_token&client_id=APP_ID&\
client_secret=APP_SECRET&fb_exchange_token=CURRENT_TOKEN"
```

Ask me and I'll wire a monthly reminder around it.

---

## 3. Supervised test post

Once 1 and 2 are done:

```bash
cd ~/carmodreview
.venv/bin/python upload.py --slugs tonneau-covers-explained
```

That posts **one** short to both platforms and stops. Check both, then load the
schedule:

```bash
cp com.carmodreview.daily-post.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.carmodreview.daily-post.plist
```

To stop it again: `launchctl unload ~/Library/LaunchAgents/com.carmodreview.daily-post.plist`

Logs land in `~/carmodreview/social/upload.log`.

---

## What the queue does

`social/queue.json` holds the eleven shorts, newest article first. The job posts
one per run, records it in `social/posted.json`, and moves on. When the queue
empties it logs `queue empty` and does nothing — it does not repeat itself.

To add a short: `python3 make_short.py <slug>`, then

```bash
python3 publish_social.py && git add -A && git commit -m "Publish <slug> short" && git push
```

The second half is not optional for Instagram — its API fetches the video from a
public URL, so the mp4 has to be live before it can be posted.

**If an article changes after its short was rendered**, the job skips that item
and tells you to re-render. That is deliberate: a queued video quoting a price
the page no longer shows is worse than a missed post.
