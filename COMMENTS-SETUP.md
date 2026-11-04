# Turning on comments

`build.py` already renders the comment section on every article. It stays
invisible until one value is filled in, so nothing is broken while you decide
or while you're setting it up.

The backend is **Waline**: free, open source, no ads, no tracking, and a reader
can post with just a name — no account, no sign-in. That last part is the
reason it was picked over giscus (GitHub login) or Disqus (ads).

## What you need to create

Two free accounts, both no credit card:

1. **Vercel** — https://vercel.com/signup (Hobby plan, $0)
2. **Neon** — https://neon.com (free tier: 1 GB, no time limit)

## Steps

1. Sign in to Vercel, then open the Waline deploy guide:
   https://waline.js.org/en/guide/deploy/vercel.html
   Click its blue **Deploy** button. That copies the Waline server template into
   a new Vercel project under your account.

2. In the Vercel dashboard for that new project, open **Storage → Create
   Database → Neon**, accept, and create the database. Vercel wires the
   connection string into the project automatically.

3. Redeploy the project once (Deployments → ⋯ → Redeploy) so it picks up the
   database. Visit the project URL. You should see a Waline welcome page
   telling you to register the first admin account.

4. **Register the admin account immediately.** The first account to sign up on a
   fresh Waline server becomes the administrator. Do this before you point the
   site at it, or a stranger can claim it.

5. Give it a real address. In Vercel: **Settings → Domains → Add**, and enter
   `comments.carmodreview.com`. Vercel will show a CNAME target. Add that CNAME
   at GoDaddy (same place the existing records live). DNS lags the panel by
   5–30 minutes; verify with:
   ```
   dig +short @ns47.domaincontrol.com comments.carmodreview.com
   ```

## Then tell me the URL

Paste the final address (e.g. `https://comments.carmodreview.com`) and I'll set
`WALINE_SERVER_URL` in `build.py`, rebuild, and push. All 27 article pages get
comments at once — 9 guides × 3 languages, each with its own thread.

## Editing comments

Admin panel: `https://<your-waline-url>/ui/register` to sign in, then
`/ui` for moderation. You can delete spam, ban IPs, and turn on email
notifications for new comments there.
