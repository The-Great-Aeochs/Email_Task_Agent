"""Main entry point for the Bharat Email Task Agent."""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# Load env vars
load_dotenv()

from src.agents.extraction import ExtractionAgent
from src.agents.prioritization import PrioritizationAgent
from src.agents.briefing import BriefingAgent
from src.tools.gmail_client import GmailClient
from src.tools.task_store import TaskStore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/agent.log", mode="a"),
    ],
)
logger = logging.getLogger("bharat-agent")


def run_extract(args):
    """Fetch emails and extract tasks."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY not set. Add it to .env")
        sys.exit(1)

    # Fetch emails
    gmail = GmailClient(
        credentials_path=os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json"),
        token_path=os.getenv("GOOGLE_TOKEN_FILE", "token.json"),
    )
    gmail.authenticate()

    query = args.query or os.getenv("GMAIL_DEFAULT_QUERY", "is:unread")
    emails = gmail.fetch_emails(max_results=args.emails, query=query)

    if not emails:
        logger.info("No emails found matching query.")
        return

    logger.info(f"Fetched {len(emails)} emails. Starting extraction...")

    # Extract tasks
    extractor = ExtractionAgent(api_key=api_key, model=args.model)
    tasks = extractor.extract_from_batch(emails)

    logger.info(f"Extracted {len(tasks)} tasks from {len(emails)} emails")

    # Save to store
    store = TaskStore(db_path=os.getenv("DB_PATH", "data/tasks.db"))
    store.save_tasks(tasks)
    store.log_processing_run(len(emails), tasks)
    store.close()

    # Output
    _output_tasks(tasks, args.output)


def run_prioritize(args):
    """Prioritize existing tasks."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY not set.")
        sys.exit(1)

    store = TaskStore(db_path=os.getenv("DB_PATH", "data/tasks.db"))
    raw_tasks = store.get_tasks(status="pending")

    if not raw_tasks:
        logger.info("No pending tasks to prioritize.")
        return

    # Convert dicts back to ExtractedTask objects
    from src.models.task import ExtractedTask, Priority, TaskStatus
    tasks = []
    for r in raw_tasks:
        task = ExtractedTask(
            id=r["id"],
            title=r["title"],
            description=r.get("description", ""),
            source_email_id=r.get("source_email_id", ""),
            source_subject=r.get("source_subject", ""),
            sender=r.get("sender", ""),
            sender_name=r.get("sender_name", ""),
            assignee=r.get("assignee"),
            deadline=datetime.fromisoformat(r["deadline"]) if r.get("deadline") else None,
            deadline_text=r.get("deadline_text"),
            priority=Priority(r.get("priority", "P1")),
            urgency_score=r.get("urgency_score", 0.5),
            importance_score=r.get("importance_score", 0.5),
            confidence=r.get("confidence", 0.7),
            tags=json.loads(r.get("tags", "[]")),
        )
        tasks.append(task)

    # Prioritize
    prioritizer = PrioritizationAgent(
        api_key=api_key,
        model=args.model,
        vip_config_path=os.getenv("VIP_CONFIG_PATH", "config/vip_senders.yaml"),
    )
    prioritized = prioritizer.prioritize(tasks)

    # Save updated priorities
    store.save_tasks(prioritized)
    store.close()

    _output_tasks(prioritized, args.output)


def run_brief(args):
    """Generate a daily brief."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY not set.")
        sys.exit(1)

    store = TaskStore(db_path=os.getenv("DB_PATH", "data/tasks.db"))
    raw_tasks = store.get_tasks(limit=100)
    store.close()

    if not raw_tasks:
        logger.info("No tasks for brief generation.")
        return

    from src.models.task import ExtractedTask, Priority
    tasks = []
    for r in raw_tasks:
        task = ExtractedTask(
            id=r["id"],
            title=r["title"],
            description=r.get("description", ""),
            source_email_id=r.get("source_email_id", ""),
            source_subject=r.get("source_subject", ""),
            sender=r.get("sender", ""),
            sender_name=r.get("sender_name", ""),
            deadline=datetime.fromisoformat(r["deadline"]) if r.get("deadline") else None,
            deadline_text=r.get("deadline_text"),
            priority=Priority(r.get("priority", "P1")),
            urgency_score=r.get("urgency_score", 0.5),
            importance_score=r.get("importance_score", 0.5),
            tags=json.loads(r.get("tags", "[]")),
        )
        tasks.append(task)

    briefer = BriefingAgent(api_key=api_key, model=args.model)
    brief_md = briefer.generate_brief_markdown(
        tasks=tasks,
        emails_count=len(raw_tasks),
    )

    # Write brief
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    brief_path = output_dir / f"daily_brief_{today}.md"
    brief_path.write_text(brief_md)

    print("\n" + brief_md)
    logger.info(f"Brief saved to {brief_path}")


def run_full(args):
    """Run the full pipeline: fetch → extract → prioritize → brief."""
    logger.info("=" * 60)
    logger.info("BHARAT EMAIL AGENT — Full Pipeline")
    logger.info("=" * 60)

    run_extract(args)
    run_prioritize(args)
    run_brief(args)

    logger.info("Pipeline complete!")


def _output_tasks(tasks, format: str = "table"):
    """Output tasks in the requested format."""
    if format == "json":
        print(json.dumps([t.to_dict() for t in tasks], indent=2))
    elif format == "csv":
        import csv
        import io
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            "priority", "title", "sender", "deadline_text", "assignee", "confidence"
        ])
        writer.writeheader()
        for t in tasks:
            writer.writerow({
                "priority": t.priority.value,
                "title": t.title,
                "sender": t.sender,
                "deadline_text": t.deadline_text or "",
                "assignee": t.assignee or "",
                "confidence": f"{t.confidence:.0%}",
            })
        print(output.getvalue())
    else:
        # Pretty table
        print("\n" + "=" * 80)
        print("📋 EXTRACTED TASKS — Eisenhower Matrix")
        print("=" * 80)

        current_priority = None
        for task in tasks:
            if task.priority != current_priority:
                current_priority = task.priority
                print(f"\n{task.priority_label}")
                print("-" * 60)

            deadline_str = task.deadline_text or (
                task.deadline.strftime("%b %d") if task.deadline else "No deadline"
            )
            print(f"  [{task.confidence:.0%}] {task.title}")
            print(f"       From: {task.sender_name} | Due: {deadline_str}")
            if task.assignee:
                print(f"       Assignee: {task.assignee}")
            print()


def main():
    parser = argparse.ArgumentParser(
        description="Bharat Email Task Agent — Extract & prioritize tasks from email"
    )
    parser.add_argument(
        "--mode",
        choices=["extract", "prioritize", "brief", "full"],
        default="full",
        help="Pipeline mode (default: full)",
    )
    parser.add_argument("--emails", type=int, default=20, help="Max emails to fetch")
    parser.add_argument("--query", type=str, help="Gmail search query")
    parser.add_argument("--model", default="claude-sonnet-4-20250514", help="Claude model")
    parser.add_argument(
        "--output",
        choices=["table", "json", "csv"],
        default="table",
        help="Output format",
    )

    args = parser.parse_args()

    # Ensure logs directory exists
    Path("logs").mkdir(exist_ok=True)

    mode_map = {
        "extract": run_extract,
        "prioritize": run_prioritize,
        "brief": run_brief,
        "full": run_full,
    }
    mode_map[args.mode](args)


if __name__ == "__main__":
    main()
