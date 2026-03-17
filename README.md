# Radius Morning Briefing Automation

Nightly automation that logs into Radius, downloads the daily session report,
generates an AI-powered summary email using Claude, and sends it to your team at 10 PM.

---

## Files

| File | What it does |
|------|-------------|
| `scrape.py` | Logs into Radius, downloads today's CSV |
| `parse.py` | Reads the CSV, computes all stats |
| `generate.py` | Calls Claude API for AI-written sections |
| `send.py` | Renders the HTML email and sends it |
| `main.py` | Runs the full pipeline end-to-end |
| `.github/workflows/nightly_briefing.yml` | GitHub Actions schedule |
| `requirements.txt` | Python dependencies |

---

## Setup Guide

### Step 1 — Create a GitHub account
1. Go to https://github.com and click **Sign up**
2. Choose the **Free** plan
3. Create a new repository: click **+** → **New repository**
4. Name it `radius-morning-briefing`, set it to **Private**, click **Create repository**

### Step 2 — Upload the files
In your new repository, upload all files from this folder:
- `main.py`
- `scrape.py`
- `parse.py`
- `generate.py`
- `send.py`
- `requirements.txt`
- `.github/workflows/nightly_briefing.yml` ← this folder structure matters

To create the `.github/workflows/` folder, click **Add file → Create new file**,
type `.github/workflows/nightly_briefing.yml` as the filename, paste the contents, and save.

### Step 3 — Add your secrets
GitHub Secrets store your passwords and API keys securely — they are never visible
in your code or logs.

Go to your repository → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Add each of the following:

| Secret name | Value |
|-------------|-------|
| `RADIUS_URL` | Your Radius login URL, e.g. `https://app.radiusapp.com` |
| `RADIUS_USERNAME` | Your Radius username/email |
| `RADIUS_PASSWORD` | Your Radius password |
| `RADIUS_REPORT_URL` | URL of the daily session report page in Radius |
| `ANTHROPIC_API_KEY` | Your Claude API key from https://console.anthropic.com |
| `SMTP_USER` | The email address that sends the report |
| `SMTP_PASSWORD` | Gmail App Password (see Step 4) |
| `REPORT_RECIPIENTS` | Comma-separated list: `you@example.com, colleague@example.com` |
| `CENTER_NAME` | `Teaneck` (or your center name) |

### Step 4 — Set up a sending email (Gmail)
The easiest option is a free Gmail account (e.g. `teaneck.briefing@gmail.com`).

To generate an App Password (required — Gmail blocks regular passwords for scripts):
1. Log into the Gmail account
2. Go to https://myaccount.google.com/security
3. Enable **2-Step Verification** if not already on
4. Search for **App Passwords** at the top
5. Create a new app password, name it "Morning Briefing"
6. Copy the 16-character password → use this as `SMTP_PASSWORD`

### Step 5 — Get a Claude API key
1. Go to https://console.anthropic.com
2. Sign up or log in
3. Click **API Keys** → **Create Key**
4. Copy the key → use as `ANTHROPIC_API_KEY`

Note: The API is pay-as-you-go. This script uses the Haiku model which costs
approximately $0.01–0.02 per nightly report.

### Step 6 — Fill in Radius selectors
This is the only step that requires inspecting your Radius site.

Open Radius in Chrome, go to the login page, and right-click the username field.
Click **Inspect**. Find the `id` or `name` attribute of the input field and update
`scrape.py` accordingly. Do the same for the password field, login button, and the
CSV export button on the report page.

If you need help with this step, share a screenshot of the Radius login page and
report page and we can identify the correct selectors together.

### Step 7 — Test manually
Before relying on the nightly schedule, run a test:

1. Go to your GitHub repository → **Actions** tab
2. Click **Nightly Morning Briefing** → **Run workflow** → **Run workflow**
3. Watch the logs — each step will print its progress
4. Check your inbox for the email

If anything fails, the logs will show exactly which step and why.

---

## Testing locally
If you want to test without scraping Radius (e.g. with your sample CSV):

```bash
pip install -r requirements.txt
playwright install chromium

export ANTHROPIC_API_KEY="your-key"
export SMTP_USER="your@gmail.com"
export SMTP_PASSWORD="your-app-password"
export REPORT_RECIPIENTS="you@example.com"
export CENTER_NAME="Teaneck"

python main.py --csv path/to/your/sample.csv
```

---

## Schedule
The workflow runs at **10 PM Eastern Time** every night.

GitHub Actions uses UTC. The workflow is set to `0 2 * * *` (2:00 AM UTC)
which equals 10:00 PM EDT (summer). During winter (EST), adjust to `0 3 * * *`
or use a timezone-aware cron tool like https://crontab.guru.

---

## Troubleshooting

**"Failed to log in"** — Check `RADIUS_USERNAME` and `RADIUS_PASSWORD` secrets.
Also verify the login selectors in `scrape.py` match your Radius page.

**"No such element"** — A CSS selector in `scrape.py` doesn't match the page.
Inspect Radius and update the selector.

**"Authentication error" from Claude** — Check your `ANTHROPIC_API_KEY` and
that your Anthropic account has credits.

**Email not arriving** — Check `SMTP_PASSWORD` is the App Password (not your
regular Gmail password). Check spam folder. Verify `REPORT_RECIPIENTS` format.
