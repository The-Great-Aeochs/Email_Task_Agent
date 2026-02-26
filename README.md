# 📧 Email Task Agent

> AI-powered email task extraction and prioritization agent — built with Claude + MCP + Skills

An intelligent agent that reads your Gmail inbox, extracts actionable tasks from emails, prioritizes them using the Eisenhower Matrix, and optionally syncs deadlines with Google Calendar. Built for the Claude Code ecosystem with both **MCP integration** and **Claude Code Skills** support.

## ✨ Key Capabilities

| Capability | Details |
|------------|---------|
| LLM Backend | Claude (Anthropic) |
| Email Access | Gmail API with OAuth |
| Calendar | Google Calendar MCP |
| Architecture | Multi-agent pipeline |
| Prioritization | Eisenhower Matrix + deadline scoring |
| Deployment | Claude Code native + standalone CLI |
| Output | Rich CLI + optional web UI |

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    EMAIL TASK AGENT                       │
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
git clone https://github.com/The-Great-Aeochs/Email_Task_Agent.git
cd Email_Task_Agent

# Install as a Claude Code Skill
cp -r skills/gmail ~/.claude/skills/gmail
cp -r skills/email-triage ~/.claude/skills/email-triage

# Start Claude Code and ask:
# "Fetch my recent emails and extract all tasks with priorities"
```

### Option 2: Standalone CLI

```bash
# Clone & install
git clone https://github.com/The-Great-Aeochs/Email_Task_Agent.git
cd Email_Task_Agent
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your API keys

# Setup Google OAuth
python scripts/setup_google_auth.py

# Run the agent
python main.py --mode extract --emails 20
python main.py --mode prioritize
python main.py --mode brief  # Generate daily brief
```

### Option 3: MCP Integration (Claude Desktop / claude.ai)

If you have Gmail MCP connected in Claude.ai or Claude Desktop, the agent can work directly through MCP. See [MCP Setup Guide](MCP_SETUP.md).

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
# vip_senders.yaml
vip_senders:
  - email: "ceo@yourcompany.com"
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
1. Review investor deck — from: ceo@yourcompany.com — Due: Today
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
Email_Task_Agent/
├── src/
│   ├── agents/
│   │   ├── extraction.py       # Task extraction agent
│   │   ├── prioritization.py   # Eisenhower matrix prioritization
│   │   └── briefing.py         # Daily brief generator
│   ├── tools/
│   │   ├── gmail_client.py     # Gmail API wrapper
│   │   └── task_store.py       # SQLite task persistence
│   ├── models/
│   │   └── task.py             # Task data models
│   └── utils/
│       └── prompts.py          # All Claude prompts
├── main.py                     # CLI entry point
├── vip_senders.yaml            # VIP sender configuration
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
python main.py --mode extract --emails 5
```

## 🐳 Docker

```bash
docker build -t email-task-agent .
docker run -v $(pwd)/.env:/app/.env email-task-agent --mode brief
```

## 🗺️ Roadmap

- [x] Gmail integration (API + MCP + Skills)
- [x] Task extraction with Claude
- [x] Eisenhower Matrix prioritization
- [x] Daily brief generation
- [x] VIP sender detection
- [ ] Slack notification integration
- [ ] Google Tasks / Todoist sync
- [ ] Multi-language support
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

- Architecture informed by [LangChain agents-from-scratch](https://github.com/langchain-ai/agents-from-scratch)
- Skills pattern from [jlongster's Gmail workflow](https://jlongster.com/wrangling-email-claude-code)
- MCP approach from [Harper Reed's email productivity](https://harper.blog/2025/12/03/claude-code-email-productivity-mcp-agents/)
