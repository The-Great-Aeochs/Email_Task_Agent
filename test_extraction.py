"""Tests for the Task Extraction Agent."""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.agents.extraction import ExtractionAgent
from src.models.task import EmailMessage


@pytest.fixture
def sample_emails():
    """Load sample emails from fixtures."""
    fixture_path = Path(__file__).parent / "fixtures" / "sample_emails.json"
    with open(fixture_path) as f:
        data = json.load(f)
    return [
        EmailMessage(
            id=e["id"],
            thread_id=e["thread_id"],
            subject=e["subject"],
            sender=e["sender"],
            sender_name=e["sender_name"],
            recipients=e["recipients"],
            cc=e.get("cc", []),
            date=datetime.fromisoformat(e["date"]),
            body=e["body"],
            snippet=e["snippet"],
            labels=e.get("labels", []),
            is_reply=e.get("is_reply", False),
            has_attachments=e.get("has_attachments", False),
        )
        for e in data
    ]


@pytest.fixture
def mock_claude_response():
    """Mock Claude API response for task extraction."""
    return json.dumps([
        {
            "title": "Review Q4 budget allocations and provide feedback",
            "description": "Department heads need to confirm spend vs forecast",
            "assignee": "Department heads",
            "deadline_text": "EOD Wednesday",
            "deadline_iso": "2026-02-26T17:00:00",
            "urgency_signals": ["EOD Wednesday", "board meeting next Monday"],
            "importance_signals": ["budget", "board meeting", "action required"],
            "confidence": 0.95,
            "tags": ["finance", "budget"],
            "dependencies": [],
        },
        {
            "title": "Submit revised cloud infrastructure costs",
            "description": "Engineering to submit updated cloud costs for Q4",
            "assignee": "Engineering",
            "deadline_text": "by Friday",
            "deadline_iso": "2026-02-28T17:00:00",
            "urgency_signals": ["by Friday", "board meeting Monday"],
            "importance_signals": ["board meeting", "budget"],
            "confidence": 0.90,
            "tags": ["engineering", "infrastructure"],
            "dependencies": ["Review Q4 budget allocations"],
        },
    ])


class TestExtractionAgent:
    def test_extraction_parses_claude_response(self, sample_emails, mock_claude_response):
        """Test that extraction correctly parses Claude's JSON output."""
        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text=mock_claude_response)]
        mock_client.messages.create.return_value = mock_message

        agent = ExtractionAgent(api_key="test-key")
        agent.client = mock_client

        tasks = agent.extract_tasks(sample_emails[0])  # Budget review email

        assert len(tasks) == 2
        assert tasks[0].title == "Review Q4 budget allocations and provide feedback"
        assert tasks[0].confidence == 0.95
        assert tasks[0].assignee == "Department heads"
        assert tasks[0].deadline is not None
        assert "finance" in tasks[0].tags

    def test_extraction_handles_empty_response(self, sample_emails):
        """Test handling of emails with no tasks."""
        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="[]")]
        mock_client.messages.create.return_value = mock_message

        agent = ExtractionAgent(api_key="test-key")
        agent.client = mock_client

        tasks = agent.extract_tasks(sample_emails[2])  # Newsletter email
        assert len(tasks) == 0

    def test_extraction_handles_malformed_json(self, sample_emails):
        """Test graceful handling of malformed Claude output."""
        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="not valid json")]
        mock_client.messages.create.return_value = mock_message

        agent = ExtractionAgent(api_key="test-key")
        agent.client = mock_client

        tasks = agent.extract_tasks(sample_emails[0])
        assert len(tasks) == 0

    def test_urgency_scoring(self):
        """Test urgency signal scoring."""
        agent = ExtractionAgent(api_key="test-key")

        # ASAP should score high
        high = agent._calc_initial_urgency({"urgency_signals": ["ASAP", "immediately"]})
        assert high >= 0.9

        # "next week" should score low
        low = agent._calc_initial_urgency({"urgency_signals": ["next week"]})
        assert low <= 0.4

        # No signals
        none = agent._calc_initial_urgency({"urgency_signals": []})
        assert none == 0.3

    def test_importance_scoring(self):
        """Test importance signal scoring."""
        agent = ExtractionAgent(api_key="test-key")

        high = agent._calc_initial_importance({"importance_signals": ["revenue", "legal"]})
        assert high >= 0.9

        low = agent._calc_initial_importance({"importance_signals": ["fyi", "newsletter"]})
        assert low <= 0.2

    def test_batch_extraction(self, sample_emails, mock_claude_response):
        """Test batch extraction across multiple emails."""
        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text=mock_claude_response)]
        mock_client.messages.create.return_value = mock_message

        agent = ExtractionAgent(api_key="test-key")
        agent.client = mock_client

        tasks = agent.extract_from_batch(sample_emails[:2])
        # 2 tasks per email × 2 emails
        assert len(tasks) == 4
