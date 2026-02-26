"""Data models for tasks and emails."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class Priority(str, Enum):
    """Eisenhower Matrix priority levels."""
    P0_DO_NOW = "P0"       # Urgent + Important
    P1_SCHEDULE = "P1"     # Not Urgent + Important
    P2_DELEGATE = "P2"     # Urgent + Not Important
    P3_ARCHIVE = "P3"      # Not Urgent + Not Important


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DELEGATED = "delegated"
    ARCHIVED = "archived"


@dataclass
class EmailMessage:
    """Represents a parsed email."""
    id: str
    thread_id: str
    subject: str
    sender: str
    sender_name: str
    recipients: list[str]
    cc: list[str]
    date: datetime
    body: str
    snippet: str
    labels: list[str] = field(default_factory=list)
    is_reply: bool = False
    has_attachments: bool = False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "thread_id": self.thread_id,
            "subject": self.subject,
            "sender": self.sender,
            "sender_name": self.sender_name,
            "recipients": self.recipients,
            "cc": self.cc,
            "date": self.date.isoformat(),
            "body": self.body[:500],  # Truncate for summaries
            "snippet": self.snippet,
            "labels": self.labels,
            "is_reply": self.is_reply,
            "has_attachments": self.has_attachments,
        }


@dataclass
class ExtractedTask:
    """A task extracted from an email."""
    id: str
    title: str
    description: str
    source_email_id: str
    source_subject: str
    sender: str
    sender_name: str
    assignee: Optional[str] = None
    deadline: Optional[datetime] = None
    deadline_text: Optional[str] = None  # Original text like "by EOD Friday"
    priority: Priority = Priority.P1_SCHEDULE
    urgency_score: float = 0.5  # 0.0 - 1.0
    importance_score: float = 0.5  # 0.0 - 1.0
    confidence: float = 0.8  # Extraction confidence
    status: TaskStatus = TaskStatus.PENDING
    tags: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    calendar_conflict: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "source_email_id": self.source_email_id,
            "source_subject": self.source_subject,
            "sender": self.sender,
            "sender_name": self.sender_name,
            "assignee": self.assignee,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "deadline_text": self.deadline_text,
            "priority": self.priority.value,
            "urgency_score": self.urgency_score,
            "importance_score": self.importance_score,
            "confidence": self.confidence,
            "status": self.status.value,
            "tags": self.tags,
            "dependencies": self.dependencies,
            "created_at": self.created_at.isoformat(),
            "calendar_conflict": self.calendar_conflict,
        }

    @property
    def priority_label(self) -> str:
        labels = {
            Priority.P0_DO_NOW: "🔴 DO NOW",
            Priority.P1_SCHEDULE: "🟡 SCHEDULE",
            Priority.P2_DELEGATE: "🔵 DELEGATE",
            Priority.P3_ARCHIVE: "⚪ ARCHIVE/FYI",
        }
        return labels[self.priority]


@dataclass
class DailyBrief:
    """Daily summary of extracted tasks."""
    date: datetime
    total_emails_processed: int
    total_tasks_extracted: int
    tasks_by_priority: dict[str, list[ExtractedTask]]
    urgent_count: int
    calendar_conflicts: list[str]
    top_senders: list[tuple[str, int]]

    def to_markdown(self) -> str:
        lines = [
            f"## 📋 Daily Brief — {self.date.strftime('%b %d, %Y')}",
            "",
        ]

        for priority_key in ["P0", "P1", "P2", "P3"]:
            tasks = self.tasks_by_priority.get(priority_key, [])
            if not tasks:
                continue

            emoji = {"P0": "🔴", "P1": "🟡", "P2": "🔵", "P3": "⚪"}[priority_key]
            label = {"P0": "Do Now", "P1": "Schedule", "P2": "Delegate", "P3": "Archive/FYI"}[priority_key]
            lines.append(f"### {emoji} {priority_key}: {label} ({len(tasks)} tasks)")

            for i, task in enumerate(tasks, 1):
                deadline_str = f" — Due: {task.deadline_text or task.deadline.strftime('%b %d') if task.deadline else 'No deadline'}"
                lines.append(f"{i}. **{task.title}** — from: {task.sender}{deadline_str}")

            lines.append("")

        lines.extend([
            "### 📊 Stats",
            f"- {self.total_emails_processed} emails processed | {self.total_tasks_extracted} tasks extracted | {self.urgent_count} urgent",
        ])

        if self.calendar_conflicts:
            lines.append("")
            lines.append("### ⚠️ Calendar Conflicts")
            for conflict in self.calendar_conflicts:
                lines.append(f"- {conflict}")

        return "\n".join(lines)
