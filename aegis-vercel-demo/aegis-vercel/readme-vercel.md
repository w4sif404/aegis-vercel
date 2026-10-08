# Aegis Cyber Systems — Vercel Edition (University Demo)

Same training app as the local version, re-plumbed to run as a Vercel
serverless function. Read **"How state storage works"** below before your
session — it's the one thing that behaves differently from localhost.

## 1. Deploy

```bash
git init
git add .
git commit -m "Aegis university cyber demo - vercel"
git branch -M main
git remote add origin <YOUR_GITHUB_REPO_URL>
git push -u origin main
```

Then: **vercel.com → Add New → Project → Import** your repo → Deploy.
No framework config needed beyond the `vercel.json` already in this repo.

You'll get a URL like `https://aegis-demo-xyz.vercel.app`.

### Optional but recommended: Upstash Redis (free)

Vercel's filesystem is read-only except `/tmp`, and `/tmp` can be wiped
whenever your function cold-starts — meaning the "COMPROMISED" flag could
silently reset mid-demo if Vercel spins up a fresh instance. For a live
audience, remove that risk:

1. In the Vercel dashboard: **Storage → Create Database → Upstash Redis**
   (a few clicks, free tier is enough).
2. Vercel auto-injects `UPSTASH_REDIS_REST_URL` and
   `UPSTASH_REDIS_REST_TOKEN` as environment variables — `storage.py`
   already detects and uses them automatically. Redeploy after adding it.

If you skip this, the app still works fine for a solo presenter demo on
one browser — just do a practice run-through right before your session so
the function is "warm."

## 2. The live demo flow (OSINT → recon → exploit → deface → restore)

Use your deployed URL in place of `127.0.0.1:5000` throughout.

**Step 1 — Set the scene**
Open the homepage, point at the line:
> "NO ONE CAN HACK US."

**Step 2 — Passive recon**
Walk the juniors through discovery, one URL at a time:
- `/robots.txt` → reveals `/admin` and `/demo/` are "disallowed" (which is
  itself a clue, not a security control)
- `/sitemap.xml` → confirms the public page structure
- `/.well-known/security.txt` → a real-world convention attackers check
- `/api/docs` → shows a fake API version, teaches version fingerprinting

**Step 3 — Find the exposed console**
Navigate to `/admin`. Ask: *"Why does an unauthenticated visitor get a
content-deployment console?"* — that's the actual lesson, independent of
anything else that happens next.

**Step 4 — Exploit it**
On `/admin`:
1. Choose a `.html` or `.txt` file (any small text file works — content
   doesn't matter, only its presence does).
2. Type your headline into **"Headline text"** — this is where you type
   your own message live, e.g. `YOUR SITE HAS BEEN HACKED`.
3. Click **Deploy asset**.
4. Go back to `/` — the homepage now shows your headline, the glitch
   styling, and the Offensive Security Group logo as the attacker
   "signature," under the OFFENSIVE SECURITY GROUP — THE FEW stamp.

**Step 5 — Explain why, not just what**
This is the part that makes it a real lesson instead of a stunt:
- The uploaded file's *contents* are never executed or displayed — only
  its *existence* flips a flag. The actual flaw being demonstrated is
  **missing authentication/authorization** on a privileged endpoint, which
  is one of the most common real findings in web app pentests (compare to
  OWASP A01: Broken Access Control).
- Ask: *"What's missing here that a real admin panel would have?"* — lead
  them to: login + session checks, role checks, CSRF tokens, rate
  limiting, audit logging, and not exposing the endpoint's existence in
  `robots.txt`.

**Step 6 — Restore**
Visit `/demo/reset`, or click **Restore Original Website** on the defaced
page itself.

**Step 7 — Show the fix**
Point to the code comments in `app.py` around the `/admin` route and
contrast with a short list of what a secure version adds: authentication,
per-role authorization, CSRF protection, strict allow-listed file types,
MIME verification, randomized non-executable storage paths, and logging
that never includes secrets.

## 3. Safety notes (unchanged from the local version)

- The uploaded file is **never executed, served, or reflected** anywhere
  — the "headline" field is the only attacker-controlled text that
  reaches a page, and Flask/Jinja auto-escapes it, so even an intentionally
  nasty headline can't inject script.
- Nothing here reaches outside this one app: no shell access, no
  filesystem traversal, no reverse shells, no credential theft, no
  targeting of any domain other than this demo deployment.
- Because this will sit on the public internet, anyone who finds the URL
  before your session could technically deface it themselves — redeploy
  fresh right before class, or set a simple shared `DEMO_SECRET` and
  mention in your talk track that a real `/admin` would never be this
  open (that's the whole point).
