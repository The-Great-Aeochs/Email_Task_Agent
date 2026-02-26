# Architecture

## Overview

The Bharat Email Agent uses a **pipeline architecture** with three specialized agents:

```
Email Source → Extraction Agent → Prioritization Agent → Briefing Agent → Output
```

## Agent Responsibilities

### 1. Extraction Agent (`src/agents/extraction.py`)
- **Input**: Raw email content (EmailMessage objects)
- **Process**: Sends email to Claude with structured extraction prompt
- **Output**: List of ExtractedTask objects with initial scores
- **Key Design**: Low temperature (0.2) for deterministic extraction

### 2. Prioritization Agent (`src/agents/prioritization.py`)
- **Input**: List of ExtractedTask objects
- **Process**: 
  1. Applies VIP sender boosting (rule-based)
  2. Sends tasks to Claude for nuanced Eisenhower Matrix scoring
  3. Falls back to rule-based scoring if Claude fails
- **Output**: Sorted, prioritized task list
- **Key Design**: Hybrid approach (rules + LLM) for reliability

### 3. Briefing Agent (`src/agents/briefing.py`)
- **Input**: Prioritized tasks + calendar events
- **Process**: Generates natural-language daily brief using Claude
- **Output**: Markdown brief with stats, groupings, and recommendations
- **Key Design**: Higher temperature (0.3) for natural writing

## Data Flow

```
Gmail API / MCP
      │
      ▼
EmailMessage (dataclass)
      │
      ▼
ExtractionAgent.extract_tasks()
      │  ┌─ Claude API call (structured JSON output)
      │  └─ Parse → ExtractedTask objects
      ▼
PrioritizationAgent.prioritize()
      │  ┌─ VIP boost (rule-based)
      │  ├─ Claude API call (scoring)
      │  └─ Fallback: rule-based Eisenhower Matrix
      ▼
TaskStore.save_tasks()  (SQLite persistence)
      │
      ▼
BriefingAgent.generate_brief_markdown()
      │  ┌─ Claude API call (natural language)
      │  └─ Calendar conflict checking
      ▼
Output (Markdown / JSON / CSV / CLI table)
```

## Why This Architecture?

### vs. Single-prompt approach
A single "extract and prioritize" prompt would be simpler but:
- Harder to debug individual steps
- Can't swap prioritization strategies
- No persistence between runs
- No fallback if one step fails

### vs. Multi-agent framework (LangGraph, CrewAI)
We chose a lightweight pipeline over a full framework because:
- Fewer dependencies = easier to deploy
- Claude Code Skills don't need a framework
- Each agent is independently testable
- The pipeline is linear — no complex routing needed

### Fallback Strategy
Every agent has a non-LLM fallback:
- Extraction: Returns empty list on failure
- Prioritization: Rule-based Eisenhower Matrix
- Briefing: Structured template from DailyBrief.to_markdown()

## Storage

SQLite was chosen for:
- Zero configuration
- Portable (single file)
- Good enough for individual/small team use
- Easy to query with Claude Code

Schema:
- `tasks` table: All extracted tasks with full metadata
- `processing_log` table: Run history for analytics
