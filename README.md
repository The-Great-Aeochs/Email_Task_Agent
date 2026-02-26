# 📧 Bharat Email Task Agent

> AI-powered email task extraction and prioritization agent for Bharat Ventures — built with Claude + MCP + Skills

An intelligent agent that reads your Gmail inbox, extracts actionable tasks from emails, prioritizes them using the Eisenhower Matrix, and optionally syncs deadlines with Google Calendar. Built for the Claude Code ecosystem with both **MCP integration** and **Claude Code Skills** support.

## ✨ What Makes This Different?

| Feature | daily-email-task-agent (original) | **This Agent** |
|---------|-----------------------------------|----------------|
| LLM Backend | OpenAI GPT-4o-mini | **Claude (Anthropic)** |
| Email Access | Gmail API (manual OAuth) | **Gmail MCP + Skills** |
| Calendar | ❌ | **Google Calendar MCP** |
| Architecture | Monolithic FastAPI | **Multi-agent pipeline** |
| Prioritization | Simple high/medium/low | **Eisenhower Matrix + deadline scoring** |
| Deployment | Self-hosted only | **Claude Code native + standalone** |
| Dashboard | Basic web UI | **Rich CLI + optional web UI** |

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    BHARAT EMAIL AGENT                     │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────┐   ┌──────────────┐   ┌──────────────────┐ │
│  │  Gmail    │──▶│  Extraction  │──▶│  Prioritization  │ │
│  │  Fetcher  │   │  Agent       │   │  Agent           │ │
│  └──────────┘   └──────────────┘   └──────────────────┘ │
│       │                │                     │           │
│       │          ┌─────▼─────┐         ┌─────▼─────┐    │
│       │          │  Task     │         │  Calendar  │    │
│       │          │  Store    │         │  Sync      │    │
│       │          │ (SQLite)  │         │  (GCal MCP)│    │
│       │          └───────────┘         └───────────┘    │
│       │                                      │           │
│  ┌────▼────────────────────────────────────▼──────────┐ │
│  │              Output Layer                            │ │
│  │  • Priority Matrix (CLI)                             │ │
│  │  • Daily Brief (Markdown)                            │ │
│  │  • JSON Export                                       │ │
│  │  • Dashboard (optional)                              │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Option 1: Claude Code (Recommended)

```bash
# Clone the repo
git clone https://github.com/bharat-ventures/email-task-agent.git
cd email-task-agent

# Install as a Claude Code Skill
cp -r skills/gmail ~/.claude/skills/gmail
cp -r skills/email-triage ~/.claude/skills/email-triage

# Start Claude Code and ask:
# "Fetch my recent emails and extract all tasks with priorities"
```

### Option 2: Standalone CLI

```bash
# Clone & install
git clone https://github.com/bharat-ventures/email-task-agent.git
cd email-task-agent
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your API keys

# Setup Google OAuth
python scripts/setup_google_auth.py

# Run the agent
python -m src.main --mode extract --emails 20
python -m src.main --mode prioritize
python -m src.main --mode brief  # Generate daily brief
```

### Option 3: MCP Integration (Claude Desktop / claude.ai)

If you have Gmail MCP connected in Claude.ai or Claude Desktop, the agent can work directly through MCP. See [MCP Setup Guide](docs/MCP_SETUP.md).

## 📋 Features

### 1. Smart Task Extraction
- Identifies action items from email body text
- Detects implicit tasks ("Can you review...", "Please send...")
- Extracts deadlines (explicit dates + relative: "by EOD", "next week")
- Identifies assignees and stakeholders
- Handles forwarded chains and reply threads

### 2. Eisenhower Matrix Prioritization
```
         URGENT              NOT URGENT
     ┌──────────────┬──────────────────┐
  I  │  P0: DO NOW  │  P1: SCHEDULE    │
  M  │              │                  │
  P  │ Deadline <24h│ Important but    │
  O  │ Boss/Client  │ can be planned   │
  R  ├──────────────┼──────────────────┤
  T  │  P2: DELEGATE│  P3: ARCHIVE     │
  A  │              │                  │
  N  │ Someone else │ FYI / Low impact │
  T  │ can handle   │ newsletters      │
     └──────────────┴──────────────────┘
```

### 3. VIP Sender Detection
Configure important senders (boss, key clients) for automatic priority boosting:
```yaml
# config/vip_senders.yaml
vip_senders:
  - email: "ceo@bharatventures.com"
    name: "CEO"
    priority_boost: 2
  - domain: "client-corp.com"
    name: "Key Client"
    priority_boost: 1
```

### 4. Daily Brief Generation
Generates a concise markdown brief every morning:
```
## 📋 Daily Brief — Feb 26, 2026

### 🔴 P0: Do Now (3 tasks)
1. Review investor deck — from: ceo@bharatventures.com — Due: Today
2. Submit compliance report — from: legal@corp.com — Due: Today 5PM
3. Fix production bug #342 — from: alerts@monitoring.com — Due: ASAP

### 🟡 P1: Schedule (5 tasks)
...

### 📊 Stats
- 47 emails processed | 15 tasks extracted | 3 urgent
```

### 5. Calendar Integration
- Auto-checks Google Calendar for deadline conflicts
- Suggests time blocks for tasks
- Warns about overbooked days

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `ANTHROPIC_API_KEY` | Claude API key | Yes |
| `GOOGLE_CREDENTIALS_FILE` | Path to Google OAuth credentials | Yes (standalone) |
| `GMAIL_MAX_EMAILS` | Max emails to fetch per run | No (default: 50) |
| `PRIORITY_MODEL` | Prioritization model (`eisenhower` / `simple`) | No (default: eisenhower) |
| `VIP_CONFIG_PATH` | Path to VIP senders config | No |
| `OUTPUT_FORMAT` | Output format (`markdown` / `json` / `csv`) | No (default: markdown) |
| `DB_PATH` | SQLite database path | No (default: `./data/tasks.db`) |

### Claude Code CLAUDE.md Integration

Add to your project's `CLAUDE.md`:
```markdown
## Email Task Agent
When I ask about emails, tasks, or priorities:
1. Use the gmail skill to fetch emails
2. Use the email-triage skill to extract and prioritize tasks
3. Always output in Eisenhower Matrix format
4. Check calendar for conflicts before suggesting deadlines
```

## 📁 Project Structure

```
bharat-email-agent/
├── src/
│   ├── main.py                 # CLI entry point
│   ├── agents/
│   │   ├── extraction.py       # Task extraction agent
│   │   ├── prioritization.py   # Eisenhower matrix prioritization
│   │   └── briefing.py         # Daily brief generator
│   ├── tools/
│   │   ├── gmail_client.py     # Gmail API wrapper
│   │   ├── calendar_client.py  # Google Calendar integration
│   │   └── task_store.py       # SQLite task persistence
│   ├── models/
│   │   ├── task.py             # Task data models
│   │   └── email.py            # Email data models
│   └── utils/
│       ├── prompts.py          # All Claude prompts
│       └── date_parser.py      # Natural language date parsing
├── skills/                      # Claude Code Skills
│   ├── gmail/
│   │   ├── SKILL.md
│   │   └── scripts/
│   │       ├── search_gmail.py
│   │       └── fetch_email.py
│   └── email-triage/
│       ├── SKILL.md
│       └── scripts/
│           └── extract_tasks.py
├── config/
│   ├── vip_senders.yaml        # VIP sender configuration
│   └── extraction_rules.yaml   # Custom extraction rules
├── scripts/
│   ├── setup_google_auth.py    # Google OAuth setup
│   └── run_daily.sh            # Cron-compatible daily runner
├── tests/
│   ├── test_extraction.py
│   ├── test_prioritization.py
│   └── fixtures/
│       └── sample_emails.json
├── docs/
│   ├── MCP_SETUP.md
│   ├── SKILLS_GUIDE.md
│   └── ARCHITECTURE.md
├── .env.example
├── .gitignore
├── requirements.txt
├── pyproject.toml
├── Dockerfile
└── README.md
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with sample email fixtures
pytest tests/test_extraction.py -v --fixtures

# Test with your actual emails (requires auth)
python -m src.main --mode test --emails 5
```

## 🐳 Docker

```bash
docker build -t bharat-email-agent .
docker run -v $(pwd)/.env:/app/.env bharat-email-agent --mode brief
```

## 🗺️ Roadmap

- [x] Gmail integration (API + MCP + Skills)
- [x] Task extraction with Claude
- [x] Eisenhower Matrix prioritization
- [x] Daily brief generation
- [x] VIP sender detection
- [ ] Slack notification integration
- [ ] Google Tasks / Todoist sync
- [ ] Multi-language support (Hindi emails)
- [ ] Team dashboard (web UI)
- [ ] Webhook triggers for new high-priority tasks

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgements

- Inspired by [daily-email-task-agent](https://github.com/Suganthi2496/daily-email-task-agent)
- Architecture informed by [LangChain agents-from-scratch](https://github.com/langchain-ai/agents-from-scratch)
- Skills pattern from [jlongster's Gmail workflow](https://jlongster.com/wrangling-email-claude-code)
- MCP approach from [Harper Reed's email productivity](https://harper.blog/2025/12/03/claude-code-email-productivity-mcp-agents/)

---

**Built for [Bharat Ventures](https://bharatventures.com) 🇮🇳**
