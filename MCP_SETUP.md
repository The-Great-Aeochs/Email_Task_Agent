# MCP Setup Guide

This guide covers how to use the Bharat Email Agent with MCP (Model Context Protocol) integrations.

## Option 1: Claude.ai (Gmail MCP built-in)

If you're using Claude.ai (Pro/Team/Enterprise), you likely already have Gmail and Google Calendar MCP connectors available.

### Setup
1. Go to Claude.ai Settings → Connectors
2. Enable **Gmail** and **Google Calendar**
3. Authorize with your Google account
4. Start chatting with Claude and reference this agent's prompts

### Usage Prompt
```
I want you to act as my email task extraction agent. Here's how:

1. Use Gmail to fetch my unread emails from the past 24 hours
2. For each email, extract actionable tasks with:
   - Clear title (starting with a verb)
   - Deadline (if mentioned)
   - Assignee (if mentioned)
   - Priority using Eisenhower Matrix:
     * P0 (Do Now): Urgent + Important
     * P1 (Schedule): Not Urgent + Important  
     * P2 (Delegate): Urgent + Not Important
     * P3 (Archive): Neither
3. Check my Google Calendar for any conflicts with task deadlines
4. Output a daily brief grouped by priority
```

## Option 2: Claude Desktop (Gmail MCP Server)

### Install a Gmail MCP Server

Several open-source options:

**@gongrzhe/server-gmail-autoauth-mcp** (recommended):
```json
{
  "mcpServers": {
    "gmail": {
      "command": "npx",
      "args": ["@gongrzhe/server-gmail-autoauth-mcp"]
    }
  }
}
```

**vinayak-mehta/gmail-mcp** (Python-based):
```json
{
  "mcpServers": {
    "gmail": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/vinayak-mehta/gmail-mcp", "gmail-mcp"],
      "env": {
        "GMAIL_CREDS_PATH": "/path/to/credentials.json",
        "GMAIL_TOKEN_PATH": "/path/to/token.json"
      }
    }
  }
}
```

### First-time Auth
```bash
# For @gongrzhe version
mkdir -p ~/.gmail-mcp
mv gcp-oauth.keys.json ~/.gmail-mcp/
npx @gongrzhe/server-gmail-autoauth-mcp auth
```

## Option 3: Claude Code (Skills-based — No MCP needed!)

This is the simplest approach. Instead of running an MCP server, Claude Code uses Skills (markdown + scripts) that are auto-loaded.

### Install Skills
```bash
# From the repo root
cp -r skills/gmail ~/.claude/skills/gmail
cp -r skills/email-triage ~/.claude/skills/email-triage
```

### Google OAuth Setup
```bash
# One-time setup
cd ~/.claude/skills/gmail/scripts
python setup_auth.py
```

### Use in Claude Code
```
> Fetch my unread emails and create a priority task list

# Claude Code will automatically:
# 1. Detect the gmail skill
# 2. Run search_gmail.py
# 3. Process results with email-triage skill
# 4. Output prioritized tasks
```

## Comparison

| Approach | Setup Effort | Real-time | Best For |
|----------|-------------|-----------|----------|
| Claude.ai MCP | ⭐ Minimal | ✅ Yes | Quick demos, personal use |
| Claude Desktop MCP | ⭐⭐ Medium | ✅ Yes | Daily workflow |
| Claude Code Skills | ⭐⭐ Medium | ✅ Yes | Power users, automation |
| Standalone CLI | ⭐⭐⭐ More | ❌ Batch | Production, cron jobs |
