# Email Task Agent — Showcase Guide

## Elevator Pitch

> "This agent reads your Gmail inbox, pulls out every actionable task buried in your emails, scores them using the Eisenhower Matrix, and gives you a prioritized daily brief — all powered by Claude AI. No more manually triaging 50 emails every morning."

---

## What It Does (60-second version)

1. **Connects to Gmail** via Google OAuth — reads your actual inbox
2. **Extracts tasks** from email body text using Claude — finds explicit and implicit action items, deadlines, and assignees
3. **Prioritizes everything** using the Eisenhower Matrix (P0 → P3) with urgency + importance scoring
4. **Detects VIP senders** — emails from your boss or key clients automatically get priority boosted
5. **Generates a daily brief** — a clean Markdown summary of what to do today, this week, and what to ignore

---

## Demo Script

### Step 1 — Show the tests (no API key needed)

```bash
cd Email_Task_Agent
source venv/bin/activate
pytest test_extraction.py test_prioritization.py -v
```

**What to say:** *"The core logic — task extraction, urgency scoring, Eisenhower prioritization — is fully tested and works independently of any API. 11 out of 11 tests pass."*

---

### Step 2 — Show the CLI help

```bash
python main.py --help
```

**What to say:** *"It runs as a standalone CLI with four modes: extract tasks from emails, reprioritize existing tasks, generate a daily brief, or run the full pipeline end to end."*

---

### Step 3 — Run the full pipeline (requires API keys)

```bash
# .env must have ANTHROPIC_API_KEY and GOOGLE_CREDENTIALS_FILE set
python main.py --mode extract --emails 20
python main.py --mode prioritize
python main.py --mode brief
```

Expected output:
```
================================================================================
📋 EXTRACTED TASKS — Eisenhower Matrix
================================================================================

🔴 P0: Do Now — Urgent + Important
------------------------------------------------------------
  [95%] Fix production server outage
       From: System Alerts | Due: ASAP

🟡 P1: Schedule — Important, Not Urgent
------------------------------------------------------------
  [90%] Review Q1 strategy document
       From: CEO | Due: next week

🟠 P2: Delegate — Urgent, Not Important
------------------------------------------------------------
  [75%] Update compliance docs
       From: Legal | Due: Friday

⚫ P3: Archive — Neither Urgent nor Important
------------------------------------------------------------
  [60%] Read AI newsletter
       From: AI News | Due: No deadline
```

**What to say:** *"Each task shows a confidence score — how sure the model is that this is actually an action item. The daily brief is saved as a Markdown file you can share with your team or pipe into Slack."*

---

### Step 4 — Show the VIP config

Open `vip_senders.yaml`:

```yaml
vip_senders:
  - email: "ceo@yourcompany.com"
    name: "CEO"
    priority_boost: 2
  - domain: "client-corp.com"
    name: "Key Client"
    priority_boost: 1
```

**What to say:** *"You configure your VIP senders once. Any email from them automatically gets urgency-boosted, so their tasks always surface to the top regardless of how the email is worded."*

---

## Key Technical Points

| What | How |
|------|-----|
| AI model | Claude (Anthropic) — `claude-sonnet-4-6` |
| Email access | Gmail API via Google OAuth |
| Prioritization | Eisenhower Matrix with urgency + importance scoring |
| Storage | SQLite — lightweight, no database setup needed |
| Architecture | Multi-agent pipeline (extraction → prioritization → briefing) |
| Deployment | Runs locally, as a CLI, or inside Docker |
| Integration | Claude Code Skills + MCP compatible |

---

## Setup (for the person running the demo)

### 1. Clone and install

```bash
git clone https://github.com/The-Great-Aeochs/Email_Task_Agent.git
cd Email_Task_Agent
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
mkdir -p logs
```

### 2. Get an Anthropic API key

- Sign up at [console.anthropic.com](https://console.anthropic.com)
- New accounts get free credits — enough for a demo
- Copy the key

### 3. Get Google OAuth credentials

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a project → enable **Gmail API**
3. OAuth consent screen → External → add your Gmail as test user
4. Credentials → Create OAuth client ID → **Desktop app** → Download JSON
5. Save as `credentials.json` in the project root

### 4. Create `.env`

```env
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_CREDENTIALS_FILE=credentials.json
```

### 5. Run

```bash
python main.py --mode full --emails 20
```

On first run, a browser window will open to authorize Gmail access. After that it runs automatically.

---

## What Makes This Worth Attention

- **Not a wrapper** — it's a multi-agent pipeline with distinct extraction, prioritization, and briefing agents each doing one job well
- **Confidence scoring** — every extracted task comes with a confidence score so you know when to trust the output
- **Handles ambiguity** — detects implicit asks ("Can you take a look at this?") not just explicit ones ("Please do X by Friday")
- **Configurable** — VIP senders, custom queries, output format (table / JSON / CSV), all adjustable
- **Testable without live credentials** — the entire logic layer is unit tested with mocks

---

*Built with Claude (Anthropic) · [GitHub](https://github.com/The-Great-Aeochs/Email_Task_Agent)*
