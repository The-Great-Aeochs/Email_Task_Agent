"""Prioritization Agent — Applies Eisenhower Matrix scoring using Claude."""

import json
import logging
from datetime import datetime
from typing import Optional

import anthropic
import yaml

from src.models.task import ExtractedTask, Priority
from src.utils.prompts import PRIORITIZATION_SYSTEM_PROMPT, PRIORITIZATION_USER_PROMPT

logger = logging.getLogger(__name__)


class PrioritizationAgent:
    """Prioritizes extracted tasks using the Eisenhower Matrix with VIP boosting."""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-20250514",
        vip_config_path: Optional[str] = None,
    ):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.vip_senders = self._load_vip_senders(vip_config_path)

    def prioritize(self, tasks: list[ExtractedTask]) -> list[ExtractedTask]:
        """Prioritize a list of tasks and return them sorted by priority."""
        if not tasks:
            return []

        # Apply VIP boosting first
        for task in tasks:
            self._apply_vip_boost(task)

        # Use Claude for nuanced prioritization
        tasks_json = json.dumps([t.to_dict() for t in tasks], indent=2)
        vip_json = json.dumps(self.vip_senders, indent=2)

        prompt = PRIORITIZATION_USER_PROMPT.format(
            tasks_json=tasks_json,
            vip_senders_json=vip_json,
            today=datetime.now().strftime("%Y-%m-%d"),
        )

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                system=PRIORITIZATION_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
            )

            raw_text = response.content[0].text.strip()
            priorities_data = json.loads(raw_text)

            # Map priorities back to tasks
            priority_map = {p["task_id"]: p for p in priorities_data}
            for task in tasks:
                if task.id in priority_map:
                    p = priority_map[task.id]
                    task.urgency_score = p.get("urgency_score", task.urgency_score)
                    task.importance_score = p.get("importance_score", task.importance_score)
                    task.priority = Priority(p.get("priority", "P1"))

        except (json.JSONDecodeError, anthropic.APIError) as e:
            logger.warning(f"Claude prioritization failed, using rule-based fallback: {e}")
            self._rule_based_prioritize(tasks)

        # Sort: P0 first, then P1, P2, P3
        priority_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
        tasks.sort(key=lambda t: (priority_order.get(t.priority.value, 4), -t.urgency_score))

        return tasks

    def _rule_based_prioritize(self, tasks: list[ExtractedTask]) -> None:
        """Fallback rule-based prioritization (no LLM needed)."""
        for task in tasks:
            u = task.urgency_score
            i = task.importance_score

            if u >= 0.7 and i >= 0.7:
                task.priority = Priority.P0_DO_NOW
            elif u < 0.7 and i >= 0.6:
                task.priority = Priority.P1_SCHEDULE
            elif u >= 0.6 and i < 0.6:
                task.priority = Priority.P2_DELEGATE
            else:
                task.priority = Priority.P3_ARCHIVE

    def _apply_vip_boost(self, task: ExtractedTask) -> None:
        """Boost urgency for tasks from VIP senders."""
        for vip in self.vip_senders:
            match = False
            if "email" in vip and vip["email"].lower() == task.sender.lower():
                match = True
            elif "domain" in vip and task.sender.lower().endswith(f"@{vip['domain'].lower()}"):
                match = True

            if match:
                boost = vip.get("priority_boost", 1) * 0.1
                task.urgency_score = min(task.urgency_score + boost, 1.0)
                task.importance_score = min(task.importance_score + boost, 1.0)
                task.tags.append(f"vip:{vip.get('name', 'VIP')}")
                logger.info(f"VIP boost applied to task '{task.title}' from {task.sender}")
                break

    def _load_vip_senders(self, config_path: Optional[str]) -> list[dict]:
        """Load VIP sender configuration from YAML."""
        if not config_path:
            return []
        try:
            with open(config_path, "r") as f:
                data = yaml.safe_load(f)
                return data.get("vip_senders", [])
        except (FileNotFoundError, yaml.YAMLError) as e:
            logger.warning(f"Could not load VIP config: {e}")
            return []

    def group_by_priority(self, tasks: list[ExtractedTask]) -> dict[str, list[ExtractedTask]]:
        """Group tasks by priority level."""
        groups: dict[str, list[ExtractedTask]] = {
            "P0": [], "P1": [], "P2": [], "P3": []
        }
        for task in tasks:
            groups[task.priority.value].append(task)
        return groups
