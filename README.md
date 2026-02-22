# JobTrack

**A free, open-source desktop application for job seekers.**

JobTrack searches multiple job boards at once, plots results on an interactive map with real commute estimates, automatically tracks every application you submit, and puts an AI assistant one click away — all from a single window, with no subscription required and no data leaving your computer.

Built for entry-level candidates navigating their first serious job search, but practical for anyone tired of managing five browser tabs, a stale spreadsheet, and a mental model of which companies they've heard back from.

---

## Table of Contents

- [What It Does](#what-it-does)
- [Privacy](#privacy)
- [Installation](#installation)
  - [Option 1 — Windows Installer](#option-1--windows-installer-recommended)
  - [Option 2 — Run from Source](#option-2--run-from-source)
- [First-Time Setup](#first-time-setup)
- [Features](#features)
  - [Multi-Provider Job Search](#multi-provider-job-search)
  - [Filtering](#filtering)
  - [Map View & Commute Times](#map-view--commute-times)
  - [Application Tracker](#application-tracker)
  - [AI Assistant](#ai-assistant)
  - [Google Sheets Sync](#google-sheets-sync)
  - [Preferences](#preferences)
- [Job Providers](#job-providers)
- [Platform Support](#platform-support)
- [Building the Executable](#building-the-executable)
- [Contributing](#contributing)
- [License](#license)

---

## What It Does

Most job seekers end up with the same messy workflow: multiple job board tabs open simultaneously, a tracking spreadsheet that's a week out of date, no memory of which companies they've actually heard from, and no sense of whether a commute is realistic without opening Google Maps separately for each listing. JobTrack replaces all of that.

**Search once, search everywhere.** Type your keywords and location once. JobTrack queries all your enabled job boards simultaneously and merges the results into a single deduplicated list sorted by date. When the same posting appears on multiple boards you see it once, with the most complete version of the data.

**Filter without burning API calls.** Four filter controls let you narrow results by distance, work type (remote/hybrid/onsite), experience level, and custom keywords — all applied instantly in memory with no additional requests to any service.

**See everything on a map.** The Map View plots every job with coordinates as a color-coded pin on an interactive map centered on your home. Green is under 30 minutes. Orange is 30–60. Red is over an hour. Click any pin to see the title, company, salary, remote badge, and a direct apply link — without leaving the map.

**Track applications automatically.** Mark a job as Applied and it's recorded. Advance it to Phone Screen, Interview Scheduled, or Offer Received and those milestones are timestamped automatically, building a complete timeline of your search history without requiring you to manually log a single date.

**Ask questions in plain English.** The built-in AI assistant knows what panel you're viewing, how many results loaded, and what your current filter settings are, so it can actually answer useful questions like "why aren't I seeing remote jobs?" or "help me rewrite this cover letter."

---

## Privacy

**Nothing you enter into JobTrack is ever stored outside your own computer or your own accounts.**

- **API keys** are stored in your operating system's built-in credential manager — Windows Credential Manager on Windows, Keychain on macOS. They are never written to a plain text file anywhere.
- **Job search data** is saved to a local SQLite database in your AppData folder. Optionally, it can also sync to a Google Sheet in your own Google Drive — your choice.
- **Your location** is stored in a local `config.json` file and is only ever transmitted as part of a job search query to the providers you've enabled.
- **Commute times** are fetched from OpenRouteService and cached locally — the same route is never looked up twice.
- **JobTrack has no backend server, no telemetry, and no account system.** It connects only to the job board APIs you explicitly configure.

This is verifiable. The entire source code is in this repository. Every network call the app makes originates from a file in the `integrations/` folder, and you can read exactly what each one sends and why.

---

## Installation

### Option 1 — Windows Installer (Recommended)

No Python or technical setup required.

1. Go to the [Releases](../../releases) page
2. Download `JobTrack_Setup_X.X.X.exe`
3. Run the installer — no administrator privileges required
4. Launch JobTrack from the Start Menu or desktop shortcut and follow the setup wizard

### Option 2 — Run from Source

Requires **Python 3.11 or 3.12**.

**1. Clone the repository**

```bash
git clone https://github.com/Irehund/JobTracker.git
cd JobTracker
```

**2. Create a virtual environment** (strongly recommended)

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Launch**

```bash
python main.py
```

The setup wizard runs automatically on first launch.

#### System Requirements

| | Minimum |
|-|---------|
| OS | Windows 10, macOS 10.15 |
| Python | 3.11 |
| RAM | 256 MB |
| Disk | 150 MB |
| Internet | Required for job searches |

---

## First-Time Setup

On first launch, a guided wizard walks you through configuration. Each step includes screenshots showing exactly where to find API keys and create accounts — nothing assumes prior technical knowledge. Every step is skippable; anything you skip can be configured later in Preferences.

**The wizard covers these steps in order:**

1. **Providers** — Choose which job boards to enable. USAJobs is always on. Everything else is optional.
2. **USAJobs API Key** — Register for a free key at [developer.usajobs.gov](https://developer.usajobs.gov/APIRequest/) and enter it here along with your registered email address.
3. **Indeed / LinkedIn / Glassdoor** — These three share a single RapidAPI key. The wizard shows exactly where to sign up and where to copy the key from.
4. **Adzuna** — Separate free registration at [developer.adzuna.com](https://developer.adzuna.com/). The wizard explains the `app_id:app_key` format Adzuna uses.
5. **Location** — Your city, state, and zip code. Used to center search results and calculate commute times. Never shared beyond your search queries.
6. **Job Preferences** — Default search keywords, preferred work type, experience level filter, and search radius.
7. **Application Tracker** — Choose between local-only storage or Google Sheets sync.
8. **Google Account** — If you chose Google Sheets, connect your account here via a standard browser OAuth flow.

After the wizard completes, JobTrack opens directly to the main window on every subsequent launch.

---

## Features

### Multi-Provider Job Search

Clicking Search (or auto-search on launch) queries all enabled providers in parallel using a thread pool — one thread per provider. A five-provider search takes about as long as the slowest individual provider, not the combined total.

**Retry behavior:** Each provider retries up to three times on transient failures (network timeouts, server errors), with a two-second delay between attempts. A small toast notification appears in the corner whenever a retry is in progress. Authentication errors (401/403) skip retries immediately since they won't self-resolve.

**Deduplication:** After all providers return, results are deduplicated by matching on a normalized composite key of job title, company, and state. When the same posting appears on multiple boards, the version with the highest data completeness score is kept — a posting with a full description and salary data beats one with only a title. The final merged list is sorted newest-first.

### Filtering

Four filter controls are available in the Jobs panel. They operate entirely in memory — changing any filter never triggers a new API request and never consumes any of your monthly provider quota.

| Filter | How it works |
|--------|-------------|
| **Search Radius** | Snaps to 10, 25, 50, 75, or 100 miles. Calculated as straight-line distance from your home coordinates. Jobs with no location data are never filtered out. |
| **Work Type** | Remote, Hybrid, Onsite, or Any. Detected from job title and description text. Jobs where work type can't be determined always pass through. |
| **Experience Level** | Entry, Mid, Senior, or Any. Inferred from title keywords and grade classifications (e.g. GS grades on federal jobs). Unknown experience level always passes through. |
| **Keywords** | Case-insensitive substring match against title and description. A job passes if it matches any keyword in your list. Leave empty to show everything. |

Filters run in the order listed above. Any filter set to "Any" or left empty is skipped entirely and adds no processing overhead.

### Map View & Commute Times

The Map View generates a standalone interactive Leaflet.js map as an HTML file and opens it in your default browser. No internet connection is required to view the map once generated — it's entirely self-contained.

Your home location appears as a blue house marker. Each job with GPS coordinates appears as a color-coded circle:

- 🟢 **Green** — under 30 minutes drive
- 🟠 **Orange** — 30 to 60 minutes
- 🔴 **Red** — over 60 minutes
- ⚫ **Gray** — commute not yet calculated, or no route available

Clicking any pin opens a popup showing the job title, company, city, commute time, salary range, remote/hybrid status badges, and a direct Apply button linking to the posting.

**Commute calculation** uses the [OpenRouteService](https://openrouteservice.org/) driving API (free tier: 40 requests/minute, 500/day). Times are fetched in batches of up to 50 destinations per call, cached in memory and in the local database, and never re-requested for a route already calculated. Commute calculation is on-demand — click "Calculate Commutes" in the Map panel to trigger it. The map works fully without an OpenRouteService key; pins just display as gray.

Jobs without coordinates are silently excluded from the map but remain visible in the Jobs list.

### Application Tracker

The tracker records every job you mark as Applied and lets you advance it through the hiring process. Certain status changes automatically record a timestamp when set, building a timeline of your search without manual date entry.

**All available statuses:**

| Status | Auto-timestamped |
|--------|:---:|
| Applied | |
| No Response | |
| Phone Screen | ✅ |
| Interview Scheduled | ✅ |
| Interview Completed | ✅ |
| Second Interview | ✅ |
| Offer Received | ✅ |
| Offer Accepted | ✅ |
| Offer Declined | ✅ |
| Rejected | ✅ |
| Withdrawn | |

Tracker data is stored in a local SQLite database:

- **Windows:** `%APPDATA%\JobTrack\jobtrack.db`
- **macOS:** `~/Library/Application Support/JobTrack/jobtrack.db`

This file belongs to you. You can open it with any SQLite viewer, back it up, or copy it to another machine. JobTrack will never delete or modify it without your instruction.

### AI Assistant

The assistant panel is a full chat interface powered by [Claude](https://anthropic.com) (Anthropic's AI model). It is context-aware — when you send a message, the assistant knows which panel you're currently viewing, how many results are loaded, what your location and radius are set to, and whether any providers failed during the last search.

This makes it useful for in-the-moment questions during an active search, not just general knowledge queries:

- *"Why am I not seeing any remote jobs?"* — It can see your current filter settings and explain exactly what's blocking them.
- *"What's the difference between a SOC Analyst I and a SOC Analyst II?"* — Career terminology explained in plain language.
- *"Help me write a cover letter for this position."* — Drafts based on whatever context you provide.
- *"What does a GS-9 step 5 actually pay in Texas?"* — Federal pay scale and locality questions.
- *"What is an API key and where do I get one for USAJobs?"* — Setup guidance without leaving the app.

The assistant requires an Anthropic API key, set in Preferences → Providers & Keys. Chat history is not persisted between app launches — each session starts fresh. You can also start a new conversation within a session by clicking "New Conversation."

### Google Sheets Sync

When Google Sheets mode is enabled, every application you log is automatically pushed to a spreadsheet in your Google Drive. The spreadsheet is created in a folder called `JobTrack` in your Drive root on first sync.

**Column layout:**

| Column | Contents |
|--------|----------|
| A — Company | Employer name |
| B — Job Title | Position title |
| C — Location | City, state |
| D — Provider | Which job board it came from |
| E — Job URL | Direct link to the posting |
| F — Date Applied | Date only, no time |
| G — Status | Current application status |
| H+ — Timeline | Auto-added columns, e.g. "Phone Screen Date", "Interview Scheduled Date" |

Timeline columns are added automatically the first time each milestone status is reached — the spreadsheet starts at seven columns and expands as your search progresses.

JobTrack connects via standard OAuth2. It requests only the permissions it needs: write access to Sheets, and access to Drive files it creates itself. It cannot read other files in your Drive.

To disconnect: **Preferences → Tracker → Disconnect**, or revoke access from your [Google Account permissions page](https://myaccount.google.com/permissions).

### Preferences

All settings from the wizard are accessible in Preferences at any time. Changes take effect after clicking Save — Cancel discards all edits.

| Tab | What you can change |
|-----|-------------------|
| **Location** | City, state, zip, search radius |
| **Job Search** | Keywords, work type, experience level |
| **Providers & Keys** | Enable/disable each provider; update API keys |
| **Tracker** | Switch storage mode; connect/disconnect Google |
| **Appearance** | Light, dark, or system theme; Reset to Defaults |

---

## Job Providers

| Provider | Always On | Free | Notes |
|----------|:---------:|:----:|-------|
| **USAJobs** | ✅ | ✅ | Federal government jobs. Free registration at [developer.usajobs.gov](https://developer.usajobs.gov/APIRequest/). Requires an API key and the email address used to register. |
| **Indeed** | Optional | Limited | Via [RapidAPI JSearch](https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch). Free tier: 10 requests/month. |
| **LinkedIn** | Optional | Limited | Also via RapidAPI JSearch — same key as Indeed. |
| **Glassdoor** | Optional | Limited | Also via RapidAPI JSearch — same key as Indeed and LinkedIn. |
| **Adzuna** | Optional | ✅ | Direct [Adzuna API](https://developer.adzuna.com/). Free tier: 250 requests/month. Enter credentials as `app_id:app_key`. |

**Note on RapidAPI providers:** Indeed, LinkedIn, and Glassdoor all route through the same JSearch endpoint. One RapidAPI key covers all three, and they share a single monthly quota. Enabling one is effectively enabling all three at no additional cost.

---

## Platform Support

| Platform | Status |
|----------|--------|
| Windows 10 / 11 | ✅ Fully supported |
| macOS 10.15+ | 🔜 Planned — build scripts already in place |
| Linux | 🔜 Community contributions welcome |

---

## Building the Executable

```bash
# Check all dependencies are installed
python build.py --check

# Build folder distribution (recommended — faster launch)
python build.py

# Build single-file .exe (easier to share, ~5s slower first launch)
python build.py --onefile

# Clean previous build artifacts first
python build.py --clean
```

To create a Windows installer with Start Menu integration (requires [Inno Setup](https://jrsoftware.org/isinfo.php)):

```bash
python build.py       # Build first
iscc installer.iss    # Then package
# Output: dist/JobTrack_Setup_1.0.0.exe
```

See [BUILDING.md](BUILDING.md) for troubleshooting, macOS build notes, and expected output sizes.

---

## Contributing

Pull requests are welcome. Please open an issue first to discuss significant changes.

**To add a new job provider:**

1. Create `integrations/yourprovider_provider.py` implementing `BaseProvider` from `integrations/base_provider.py`
2. Add the provider to `core/job_fetcher.py` in `_get_enabled_providers()`
3. Add a card for it in `ui/wizard/step_providers.py` and `ui/dialogs/preferences_dialog.py`
4. Add wizard screenshots to `assets/wizard_screens/yourprovider/`
5. Write tests in `tests/test_yourprovider_provider.py` — all API calls must be mocked; no live network access in tests

**Running tests:**

```bash
pip install pytest pytest-mock
pytest tests/
```

All 506 tests pass with no network access and no real API keys required.

---

## License

MIT — see [LICENSE](LICENSE)
