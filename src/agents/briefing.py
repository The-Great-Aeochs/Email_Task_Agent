"""Briefing Agent — Generates concise daily briefs from prioritized tasks."""

import json
import logging
from datetime import datetime

import anthropic

from src.models.task import DailyBrief, ExtractedTask
from src.utils.prompts import DAILY_BRIEF_SYSTEM_PROMPT, DAILY_BRIEF_USER_PROMPT

logger = logging.getLogger(__name__)


class BriefingAgent:
    """Generates daily email briefs using Claude."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def generate_brief(
        self,
        tasks: list[ExtractedTask],
        emails_count: int,
        calendar_events: list[dict] | None = None,
    ) -> DailyBrief:
        """Generate a structured daily brief."""
        # Group tasks
        groups = {"P0": [], "P1": [], "P2": [], "P3": []}
        for task in tasks:
            groups[task.priority.value].append(task)

        # Count top senders
        sender_counts: dict[str, int] = {}
        for task in tasks:
            name = task.sender_name or task.sender
            sender_counts[name] = sender_counts.get(name, 0) + 1
        top_senders = sorted(sender_counts.items(), key=lambda x: -x[1])[:5]

        # Check calendar conflicts
        conflicts = self._check_calendar_conflicts(tasks, calendar_events or [])

        brief = DailyBrief(
            date=datetime.now(),
            total_emails_processed=emails_count,
            total_tasks_extracted=len(tasks),
            tasks_by_priority=groups,
            urgent_count=len(groups["P0"]),
            calendar_conflicts=conflicts,
            top_senders=top_senders,
        )

        return brief

    def generate_brief_markdown(
        self,
        tasks: list[ExtractedTask],
        emails_count: int,
        calendar_events: list[dict] | None = None,
    ) -> str:
        """Generate a polished markdown brief using Claude for natural language."""
        tasks_json = json.dumps([t.to_dict() for t in tasks], indent=2)
        events_json = json.dumps(calendar_events or [], indent=2)
        today = datetime.now()

        prompt = DAILY_BRIEF_USER_PROMPT.format(
            prioritized_tasks_json=tasks_json,
            emails_count=emails_count,
            tasks_count=len(tasks),
            today=today.strftime("%Y-%m-%d"),
            today_formatted=today.strftime("%b %d, %Y"),
            calendar_events_json=events_json,
        )

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                system=DAILY_BRIEF_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            return response.content[0].text.strip()
        except anthropic.APIError as e:
            logger.error(f"Brief generation failed: {e}")
            # Fallback to structured brief
            brief = self.generate_brief(tasks, emails_count, calendar_events)
            return brief.to_markdown()

    def _check_calendar_conflicts(
        self, tasks: list[ExtractedTask], events: list[dict]
    ) -> list[str]:
        """Check for conflicts between task deadlines and calendar events."""
        conflicts = []
        for task in tasks:
            if not task.deadline:
                continue
            for event in events:
                event_start = event.get("start")
                if not event_start:
                    continue
                try:
                    event_dt = datetime.fromisoformat(event_start)
                    if task.deadline.date() == event_dt.date():
                        conflicts.append(
                            f"⚠️ '{task.title}' due same day as '{event.get('summary', 'event')}'"
                        )
                except (ValueError, TypeError):
                    pass
        return conflicts
