---
name: gmail
description: Allows access to read and search the user's Gmail inbox. Use this skill whenever the user asks about their emails, inbox, or wants to process email content.
---

# Gmail Skill

## Instructions

Scripts available in the `scripts` folder to help query the user's email:

* `search_gmail.py`: Run this script to search/fetch emails from Gmail. Pass a Gmail search query as the argument.
* `fetch_email.py`: Run this script to fetch the full content of a specific email by message ID.

### Setup Required
Before first use, the user needs Google OAuth credentials:
1. A `credentials.json` file from Google Cloud Console (Gmail API enabled)
2. Run `python scripts/setup_auth.py` to complete OAuth flow
3. This creates a `token.json` for subsequent use

### Common Search Queries
- `is:unread` — All unread emails
- `is:unread newer_than:1d` — Unread emails from today
- `from:someone@example.com` — Emails from a specific sender
- `subject:meeting` — Emails with "meeting" in subject
- `label:important` — Emails with the important label
- `has:attachment` — Emails with attachments
- `newer_than:7d` — Emails from the last 7 days
- `is:unread from:boss@company.com newer_than:3d` — Combine filters

## Examples

User: Show me my unread emails from today
Claude Code: <run `python scripts/search_gmail.py "is:unread newer_than:1d"`>

User: Find all emails from the CEO this week
Claude Code: <run `python scripts/search_gmail.py "from:ceo@bharatventures.com newer_than:7d"`>

User: Get the full content of email ID abc123
Claude Code: <run `python scripts/fetch_email.py abc123`>

User: Show me emails about the investor meeting
Claude Code: <run `python scripts/search_gmail.py "subject:investor meeting"`>
