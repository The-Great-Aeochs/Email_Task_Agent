"""Task Extraction Agent — Analyzes emails and extracts actionable tasks using Claude."""

import json
import logging
import uuid
from datetime import datetime
from typing import Optional

import anthropic

from src.models.task import EmailMessage, ExtractedTask, Priority
from src.utils.prompts import TASK_EXTRACTION_SYSTEM_PROMPT, TASK_EXTRACTION_USER_PROMPT

logger = logging.getLogger(__name__)


class ExtractionAgent:
    """Extracts actionable tasks from email messages using Claude."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def extract_tasks(self, email: EmailMessage) -> list[ExtractedTask]:
        """Extract tasks from a single email."""
        prompt = TASK_EXTRACTION_USER_PROMPT.format(
            sender=email.sender,
            sender_name=email.sender_name,
            recipients=", ".join(email.recipients),
            cc=", ".join(email.cc) if email.cc else "None",
            date=email.date.strftime("%Y-%m-%d %H:%M"),
            subject=email.subject,
            labels=", ".join(email.labels) if email.labels else "None",
            body=email.body[:3000],  # Limit body to avoid token overflow
            today=datetime.now().strftime("%Y-%m-%d"),
        )

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                system=TASK_EXTRACTION_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,  # Low temp for structured extraction
            )

            raw_text = response.content[0].text.strip()
            tasks_data = json.loads(raw_text)

            if not isinstance(tasks_data, list):
                logger.warning(f"Expected list, got {type(tasks_data)} for email {email.id}")
                return []

            return [self._parse_task(t, email) for t in tasks_data if t.get("title")]

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse extraction response for email {email.id}: {e}")
            return []
        except anthropic.APIError as e:
            logger.error(f"Claude API error during extraction: {e}")
            return []

    def extract_from_batch(self, emails: list[EmailMessage]) -> list[ExtractedTask]:
        """Extract tasks from multiple emails."""
        all_tasks = []
        for i, email in enumerate(emails):
            logger.info(f"Processing email {i+1}/{len(emails)}: {email.subject[:50]}...")
            tasks = self.extract_tasks(email)
            all_tasks.extend(tasks)
            logger.info(f"  → Extracted {len(tasks)} task(s)")
        return all_tasks

    def _parse_task(self, task_data: dict, email: EmailMessage) -> ExtractedTask:
        """Parse Claude's JSON output into an ExtractedTask."""
        deadline = None
        if task_data.get("deadline_iso"):
            try:
                deadline = datetime.fromisoformat(task_data["deadline_iso"])
            except (ValueError, TypeError):
                pass

        return ExtractedTask(
            id=str(uuid.uuid4())[:8],
            title=task_data.get("title", "Untitled task"),
            description=task_data.get("description", ""),
            source_email_id=email.id,
            source_subject=email.subject,
            sender=email.sender,
            sender_name=email.sender_name,
            assignee=task_data.get("assignee"),
            deadline=deadline,
            deadline_text=task_data.get("deadline_text"),
            urgency_score=self._calc_initial_urgency(task_data),
            importance_score=self._calc_initial_importance(task_data),
            confidence=task_data.get("confidence", 0.7),
            tags=task_data.get("tags", []),
            dependencies=task_data.get("dependencies", []),
        )

    def _calc_initial_urgency(self, task_data: dict) -> float:
        """Calculate initial urgency from extraction signals."""
        signals = task_data.get("urgency_signals", [])
        if not signals:
            return 0.3

        urgency_keywords = {
            "asap": 0.9, "urgent": 0.9, "immediately": 1.0,
            "today": 0.85, "eod": 0.85, "tonight": 0.85,
            "tomorrow": 0.7, "this week": 0.5, "soon": 0.4,
            "next week": 0.3, "when you can": 0.2,
        }

        max_score = 0.3
        for signal in signals:
            signal_lower = signal.lower()
            for keyword, score in urgency_keywords.items():
                if keyword in signal_lower:
                    max_score = max(max_score, score)

        return min(max_score, 1.0)

    def _calc_initial_importance(self, task_data: dict) -> float:
        """Calculate initial importance from extraction signals."""
        signals = task_data.get("importance_signals", [])
        if not signals:
            return 0.5

        importance_keywords = {
            "revenue": 0.9, "legal": 0.9, "compliance": 0.9,
            "board": 0.85, "investor": 0.85, "client": 0.8,
            "deadline": 0.7, "approval": 0.7, "sign off": 0.7,
            "team": 0.6, "process": 0.5, "optional": 0.2,
            "fyi": 0.1, "newsletter": 0.1,
        }

        max_score = 0.5
        for signal in signals:
            signal_lower = signal.lower()
            for keyword, score in importance_keywords.items():
                if keyword in signal_lower:
                    max_score = max(max_score, score)

        return min(max_score, 1.0)
