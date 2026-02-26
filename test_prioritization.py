"""Tests for the Prioritization Agent."""

import json
from datetime import datetime, timedelta

import pytest

from src.agents.prioritization import PrioritizationAgent
from src.models.task import ExtractedTask, Priority


@pytest.fixture
def sample_tasks():
    """Create sample tasks for testing."""
    return [
        ExtractedTask(
            id="task_001",
            title="Fix production server outage",
            description="Server down, immediate action needed",
            source_email_id="email_001",
            source_subject="URGENT: Server down",
            sender="alerts@monitoring.com",
            sender_name="System Alerts",
            deadline=datetime.now() + timedelta(hours=1),
            deadline_text="ASAP",
            urgency_score=0.95,
            importance_score=0.95,
        ),
        ExtractedTask(
            id="task_002",
            title="Review Q1 strategy document",
            description="Strategic review for next quarter",
            source_email_id="email_002",
            source_subject="Q1 Strategy Review",
            sender="ceo@yourcompany.com",
            sender_name="CEO",
            deadline=datetime.now() + timedelta(days=5),
            deadline_text="next week",
            urgency_score=0.3,
            importance_score=0.85,
        ),
        ExtractedTask(
            id="task_003",
            title="Update team Slack channel description",
            description="Housekeeping task",
            source_email_id="email_003",
            source_subject="Slack cleanup",
            sender="admin@yourcompany.com",
            sender_name="Admin",
            urgency_score=0.6,
            importance_score=0.2,
        ),
        ExtractedTask(
            id="task_004",
            title="Read AI newsletter",
            description="Weekly newsletter",
            source_email_id="email_004",
            source_subject="AI Weekly",
            sender="newsletter@ainews.com",
            sender_name="AI News",
            urgency_score=0.1,
            importance_score=0.1,
        ),
    ]


class TestPrioritizationAgent:
    def test_rule_based_prioritization(self, sample_tasks):
        """Test fallback rule-based prioritization."""
        agent = PrioritizationAgent(api_key="test-key")
        agent._rule_based_prioritize(sample_tasks)

        assert sample_tasks[0].priority == Priority.P0_DO_NOW      # High urgency + importance
        assert sample_tasks[1].priority == Priority.P1_SCHEDULE     # Low urgency + high importance
        assert sample_tasks[2].priority == Priority.P2_DELEGATE     # High urgency + low importance
        assert sample_tasks[3].priority == Priority.P3_ARCHIVE      # Low urgency + low importance

    def test_vip_boost(self, sample_tasks):
        """Test VIP sender urgency boosting."""
        agent = PrioritizationAgent(api_key="test-key")
        agent.vip_senders = [
            {"email": "ceo@yourcompany.com", "name": "CEO", "priority_boost": 2}
        ]

        original_urgency = sample_tasks[1].urgency_score
        agent._apply_vip_boost(sample_tasks[1])

        assert sample_tasks[1].urgency_score > original_urgency
        assert "vip:CEO" in sample_tasks[1].tags

    def test_vip_domain_match(self, sample_tasks):
        """Test VIP matching by domain."""
        agent = PrioritizationAgent(api_key="test-key")
        agent.vip_senders = [
            {"domain": "yourcompany.com", "name": "Internal", "priority_boost": 1}
        ]

        agent._apply_vip_boost(sample_tasks[1])  # ceo@yourcompany.com
        assert "vip:Internal" in sample_tasks[1].tags

    def test_group_by_priority(self, sample_tasks):
        """Test grouping tasks by priority level."""
        agent = PrioritizationAgent(api_key="test-key")
        agent._rule_based_prioritize(sample_tasks)

        groups = agent.group_by_priority(sample_tasks)

        assert len(groups["P0"]) == 1
        assert len(groups["P1"]) == 1
        assert len(groups["P2"]) == 1
        assert len(groups["P3"]) == 1

    def test_sorting_order(self, sample_tasks):
        """Test that tasks are sorted P0 → P3 with urgency tiebreaker."""
        agent = PrioritizationAgent(api_key="test-key")
        agent._rule_based_prioritize(sample_tasks)

        # Manually sort like the agent would
        priority_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
        sample_tasks.sort(key=lambda t: (priority_order.get(t.priority.value, 4), -t.urgency_score))

        assert sample_tasks[0].priority == Priority.P0_DO_NOW
        assert sample_tasks[-1].priority == Priority.P3_ARCHIVE
