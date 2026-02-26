---
name: email-triage
description: Extracts actionable tasks from emails and prioritizes them using the Eisenhower Matrix. Use this skill whenever the user wants to triage emails, extract tasks, create priority lists, or generate daily briefs.
---

# Email Triage Skill

## Instructions

This skill helps you extract tasks from emails and prioritize them.

### Available Scripts
* `extract_tasks.py`: Takes email content (piped via stdin or from a file) and extracts tasks with priorities.

### How to Use

**Step 1**: Use the `gmail` skill to fetch emails first.

**Step 2**: For each email that needs triage, pass its content to the extraction script:
```bash
echo '<email content>' | python scripts/extract_tasks.py
```

Or extract from a file:
```bash
python scripts/extract_tasks.py --file /path/to/email.txt
```

**Step 3**: The script outputs JSON with extracted tasks, each containing:
- `title`: Actionable task title
- `priority`: P0 (Do Now), P1 (Schedule), P2 (Delegate), P3 (Archive)
- `deadline`: Parsed deadline if found
- `assignee`: Who should do it
- `confidence`: Extraction confidence score

### Priority System (Eisenhower Matrix)
- **P0 — DO NOW**: Urgent + Important (deadline <24h, from boss/client)
- **P1 — SCHEDULE**: Not Urgent + Important (key work, can be planned)
- **P2 — DELEGATE**: Urgent + Not Important (someone else can handle)
- **P3 — ARCHIVE/FYI**: Not Urgent + Not Important (newsletters, FYI)

### VIP Senders
Check `config/vip_senders.yaml` for the list of priority senders whose tasks get automatic urgency boosts.

## Examples

User: Extract tasks from my latest emails and create a priority list
Claude Code: 
1. <run `python skills/gmail/scripts/search_gmail.py "is:unread newer_than:1d"`> to get emails
2. For each email, <run `python skills/gmail/scripts/fetch_email.py <id>`> to get content
3. Analyze each email to extract tasks using the Eisenhower Matrix criteria above
4. Present results grouped by P0, P1, P2, P3

User: What are my urgent tasks from this week's emails?
Claude Code:
1. Fetch emails: <run `python skills/gmail/scripts/search_gmail.py "newer_than:7d"`>
2. Extract and filter to show only P0 and P1 tasks

User: Generate my daily brief
Claude Code:
1. Fetch today's emails
2. Extract all tasks
3. Generate a markdown brief with stats and priority groupings
