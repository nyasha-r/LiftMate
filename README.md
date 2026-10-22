# LiftMate

**LiftMate is a personal Telegram workout assistant** that analyzes uploaded GPX tracks and is designed to provide AI-assisted workout insights.

> **Project status:** The Vercel deployment and basic Telegram workflow have been tested. GPX uploads are analyzed for distance, duration, pace, elevation gain, and track-point count. Some advanced workflows described below still require end-to-end verification; see [Current status](#current-status).

- **Telegram bot:** [@LiftMateWorkoutBot](https://t.me/LiftMateWorkoutBot)


## Features

### Verified basic workflow
- Telegram bot responds to `/start` and `/help`.
- Accepts GPX files through Telegram (up to 5 MB).
- Parses GPS track points and calculates:
  - Distance
  - Duration when timestamps are available
  - Average pace when calculable
  - Elevation gain
  - Number of track points
- Reports that uploaded-track calculations may differ from a watch or app's moving-time statistics.

### Additional implemented components
The repository also contains code for:
- Telegram and Strava webhook handling
- Background job dispatch through QStash
- PostgreSQL persistence and Upstash Redis state
- Gemini-powered workout analysis and conversation
- Strength and endurance metrics, personal records, and chart generation
- Session memory and scheduled weekly summaries

These components should not all be considered production-verified until their live workflows have been tested. See [Current status](#current-status).

## Architecture


## Architecture

```mermaid
flowchart TD
    S[Strava webhook] --> API[api/index.py]
    T[Telegram webhook] --> API
    API --> Q[QStash queue]
    Q --> W[api/worker]

    W --> O[Orchestrator (LLM)]
    W --> D[Data Agent (Python)]
    W --> M[Memory Manager]

    O --> SA[Strength Analyst]
    O --> EA[Endurance Analyst]
    O --> CA[Chart Agent]

    D --> SA
    D --> EA
    D --> CA

    SA --> R[Telegram Renderer]
    EA --> R
    CA --> R

    W <--> PG[(PostgreSQL)]
    W <--> REDIS[(Redis session state)]

    R --> TG[Telegram response]
```

The app is deployed as a Python application on Vercel. The single entry point, `api/index.py`, routes requests to the application handlers in `app/web/`.


The app is deployed as a Python application on Vercel. The single entry point, `api/index.py`, routes requests to the application handlers in `app/web/`.

## Technology stack

- **Language:** Python
- **API/deployment:** FastAPI-related application components and Vercel Python WSGI entry point
- **Messaging:** Telegram Bot API
- **AI:** Google Gemini
- **Database:** PostgreSQL (Neon or Supabase-compatible)
- **Session/cache:** Upstash Redis
- **Background jobs:** Upstash QStash
- **Workout data:** GPX uploads; optional Strava integration
- **Testing:** pytest

## Repository structure

```text
api/
  index.py                 Vercel entry point and route dispatch
app/
  agents/                  AI and workout-analysis agents
  charts/                  Chart presets and rendering
  clients/                 Telegram, Strava, and Gemini clients
  config.py                Environment configuration and validation
  gpx_analysis.py          GPX track analysis
  memory/                  Conversation/session memory
  metrics/                 Strength and endurance calculations
  parsers/                 Workout-data parsers
  platform/                Runtime wiring and HTTP adapter
  render/                  Telegram message rendering
  storage/                 Database, Redis, queue, and token storage
  web/                     Webhook, worker, OAuth, and cron handlers
  prompts/                 Prompt templates
migrations/                Database schema migrations
scripts/                   Setup and maintenance scripts
tests/                     Automated tests
README.md
LiftMate_PRD.md
DECISIONS.md
requirements.txt
pyproject.toml
vercel.json
```

## Requirements

- Python version supported by the project configuration
- A Telegram bot token and Telegram chat ID
- Google Gemini API key for AI features
- PostgreSQL database
- Upstash Redis and QStash credentials for queued workflows
- Vercel account for deployment

**Strava is optional for the GPX-upload workflow.** Strava credentials and webhook setup are only needed if you want Strava activity syncing and automatic post-workout processing.

Do not commit `.env` files, API keys, bot tokens, database URLs, encryption keys, or other secrets.

## Local setup

Commands below use PowerShell on Windows. Activate your existing virtual environment if you already created one.

```powershell
# Clone your repository
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd <YOUR_REPOSITORY_FOLDER>

# Create and activate a virtual environment (skip if one already exists)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
python -m pip install -r requirements.txt

# Check that configuration loads
python -c "from app.config import get_settings; get_settings(); print('Configuration loads successfully')"
```

Create a local `.env` file with the required settings before running the application. Never paste secret values into GitHub issues, chat messages, screenshots, or public documentation.

The application configuration currently expects these environment-variable names:

```text
TELEGRAM_BOT_TOKEN
TELEGRAM_WEBHOOK_SECRET
TELEGRAM_OWNER_CHAT_ID
GEMINI_API_KEY
DATABASE_URL
UPSTASH_REDIS_REST_URL
UPSTASH_REDIS_REST_TOKEN
QSTASH_TOKEN
QSTASH_CURRENT_SIGNING_KEY
QSTASH_NEXT_SIGNING_KEY
APP_URL
ENCRYPTION_KEY
INTERNAL_API_SECRET
```

Strava-related settings are optional for a GPX-only workflow:

```text
STRAVA_CLIENT_ID
STRAVA_CLIENT_SECRET
STRAVA_VERIFY_TOKEN
STRAVA_ATHLETE_ID
STRAVA_SUBSCRIPTION_ID
```

Use your local `.env` and Vercel environment-variable settings for actual values. Do not put values in this README.

## Run tests

```powershell
pytest -q
```

The README in the original project describes a suite of 165+ tests, but run the command against your current checkout to confirm the present results. A test suite passing does not replace live verification of external integrations.

## Deployment

The project is configured for Vercel. Before deploying:
1. Confirm all required environment variables are set in the correct Vercel environment.
2. Confirm database migrations have been applied.
3. Confirm `APP_URL` matches the deployment URL.
4. If scheduled cron routes are enabled, configure `CRON_SECRET` to match the internal API secret used by the app.
5. Deploy using the Vercel CLI or your configured Git integration.
6. Verify `https://<your-deployment>/api/health` returns `{"status":"ok"}`.
7. Test the Telegram bot with `/start`, `/help`, and a valid GPX file.

Do not redeploy just to change this README. A README-only GitHub update does not require a Vercel deployment.

## Current status

| Area | Status |
|---|---|
| Vercel deployment exists | Verified |
| Telegram `/start` and `/help` | Verified |
| GPX upload and basic track analysis | Verified |
| Local settings load | Verified |
| Full automated test suite | Needs latest test run |
| Gemini conversation end-to-end | Not yet verified |
| Strava webhook 竊・queue 竊・worker 竊・Telegram | Not yet verified |
| OAuth consent flow | Not yet verified |
| Workout-history, PR, and chart commands | Some commands are basic v1 responses; verify with real history |

These labels reflect the checks performed so far and should be updated when more tests are completed.

## Telegram commands

The bot lists the following commands:

`/start` ﾂｷ `/help` ﾂｷ `/last` ﾂｷ `/week` ﾂｷ `/pr` ﾂｷ `/chart` ﾂｷ `/compare` ﾂｷ `/profile` ﾂｷ `/forget` ﾂｷ `/debug`

Some history and analysis commands depend on workout data being available and may provide basic responses when no data has been logged.

## Privacy and security

- Keep `.env` files and production secrets out of version control.
- Do not publish real user workout data, chat IDs, tokens, or database contents in screenshots or example files.
- Consider the privacy implications before sending personal fitness data to an AI provider.
- Use a billed Gemini project if required by your privacy expectations and Google's current terms.
- The `/forget` command and data-deletion behavior should be verified before promising complete deletion to users.

## License

No license is specified here. Add a `LICENSE` file only after choosing a license whose terms you understand.

