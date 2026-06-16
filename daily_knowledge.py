#!/usr/bin/env python3
"""
daily_knowledge.py
------------------
Selects today's learning topic and collects due reviews.
Outputs a structured brief for Claude Code to use.

Usage:
    python daily_knowledge.py                  # Print brief to stdout
    python daily_knowledge.py --update         # Interactive: add new lesson row after Claude finishes
    python daily_knowledge.py --mark-reviewed <id> [<id> ...]  # Mark reviews as done, bump next_review
    python daily_knowledge.py --json           # Output brief as JSON instead of plain text
"""

import argparse
import csv
import json
import random
import sys
from datetime import date, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

CSV_PATH = Path(__file__).parent / "knowledge.csv"

# Top-level category weights
CATEGORY_WEIGHTS = {
    "ai":       0.80,
    "robotics": 0.10,
    "other_cs": 0.10,
}

# AI sub-category weights (sum to 1.0)
AI_SUB_WEIGHTS = {
    "ai_tool":        0.20,   # hands-on tool tutorial, work-relevant
    "ai_nontechnical":0.20,   # non-technical concept (how GPT works, Notion AI, etc.)
    "ai_technical":   0.60,   # deep technical dive
}

# Default review intervals (days) per sub-category
REVIEW_INTERVALS = {
    "ai_tool":         21,
    "ai_nontechnical":  7,   # news/releases move fast
    "ai_technical":    60,
    "robotics":        90,
    "other_cs":        90,
}

CSV_FIELDS = [
    "id",
    "date",
    "type",           # lesson | review_done
    "topic",
    "category",       # ai | robotics | other_cs
    "subcategory",    # ai_tool | ai_nontechnical | ai_technical | robotics | other_cs
    "difficulty",     # 1=beginner 2=intermediate 3=advanced
    "next_review",
    "review_interval",
    "context_for_review",  # what Claude should recall + search for at review time
]

# ---------------------------------------------------------------------------
# CSV helpers
# ---------------------------------------------------------------------------

def load_rows() -> list[dict]:
    if not CSV_PATH.exists():
        return []
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_rows(rows: list[dict]) -> None:
    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def next_id(rows: list[dict]) -> int:
    if not rows:
        return 1
    return max(int(r["id"]) for r in rows) + 1


# ---------------------------------------------------------------------------
# Topic selection
# ---------------------------------------------------------------------------

def pick_category() -> tuple[str, str]:
    """Return (category, subcategory)."""
    cat = random.choices(
        list(CATEGORY_WEIGHTS.keys()),
        weights=list(CATEGORY_WEIGHTS.values()),
    )[0]

    if cat == "ai":
        sub = random.choices(
            list(AI_SUB_WEIGHTS.keys()),
            weights=list(AI_SUB_WEIGHTS.values()),
        )[0]
    else:
        sub = cat  # robotics / other_cs are their own subcategory

    return cat, sub


def covered_topics(rows: list[dict]) -> set[str]:
    return {r["topic"].strip().lower() for r in rows if r["type"] == "lesson"}


# ---------------------------------------------------------------------------
# Review collection
# ---------------------------------------------------------------------------

def due_reviews(rows: list[dict]) -> list[dict]:
    today = date.today()
    due = []
    for r in rows:
        if r["type"] != "lesson":
            continue
        if not r.get("next_review"):
            continue
        try:
            review_date = date.fromisoformat(r["next_review"])
        except ValueError:
            continue
        if review_date <= today:
            due.append(r)
    return due


# ---------------------------------------------------------------------------
# Brief generation
# ---------------------------------------------------------------------------

SUBCATEGORY_LABELS = {
    "ai_tool":         "AI tool / hands-on tutorial",
    "ai_nontechnical": "AI concept (non-technical)",
    "ai_technical":    "AI technical deep dive",
    "robotics":        "Robotics",
    "other_cs":        "Computer Science (other)",
}

DIFFICULTY_LABELS = {
    "1": "beginner",
    "2": "intermediate",
    "3": "advanced",
}


def build_brief(category: str, subcategory: str, reviews: list[dict]) -> dict:
    """Return a dict representing today's brief."""
    return {
        "today": str(date.today()),
        "new_topic": {
            "category": category,
            "subcategory": subcategory,
            "subcategory_label": SUBCATEGORY_LABELS[subcategory],
            "instruction": _topic_instruction(subcategory),
        },
        "reviews": [
            {
                "id": r["id"],
                "original_date": r["date"],
                "topic": r["topic"],
                "subcategory_label": SUBCATEGORY_LABELS.get(r["subcategory"], r["subcategory"]),
                "difficulty": DIFFICULTY_LABELS.get(r["difficulty"], r["difficulty"]),
                "context": r.get("context_for_review", ""),
            }
            for r in reviews
        ],
    }


def _topic_instruction(subcategory: str) -> str:
    instructions = {
        "ai_tool": (
            "Pick a practical AI tool relevant to ML engineering or content moderation work "
            "(e.g. a new IDE feature, a Bedrock capability, a LangChain utility). "
            "Focus on hands-on usage with a concrete example."
        ),
        "ai_nontechnical": (
            "Pick a non-technical AI concept or current event — how a well-known model works "
            "at a high level, what a company's AI product actually does under the hood, "
            "recent funding / acquisition news, societal implications, etc."
        ),
        "ai_technical": (
            "Pick a technical AI/ML topic — an architecture, training technique, evaluation method, "
            "or recent paper. Aim for intermediate-to-advanced depth. "
            "Include equations where they clarify things, a diagram if relevant, and a work-angle "
            "connecting the concept to NLP, content moderation, or LLM pipelines."
        ),
        "robotics": (
            "Pick a robotics topic — a sensing technique, control algorithm, "
            "hardware platform, or recent research direction."
        ),
        "other_cs": (
            "Pick any foundational or emerging computer science topic outside AI/robotics — "
            "distributed systems, compilers, cryptography, networking, etc."
        ),
    }
    return instructions.get(subcategory, "")


# ---------------------------------------------------------------------------
# Plain-text brief formatter
# ---------------------------------------------------------------------------

def format_brief_text(brief: dict) -> str:
    lines = []
    lines.append("=" * 60)
    lines.append(f"DAILY KNOWLEDGE BRIEF — {brief['today']}")
    lines.append("=" * 60)
    lines.append("")

    nt = brief["new_topic"]
    lines.append("NEW TOPIC")
    lines.append("---------")
    lines.append(f"Category : {nt['subcategory_label']}")
    lines.append(f"Task     : {nt['instruction']}")
    lines.append("")
    lines.append(
        "→ Choose a specific topic that has NOT been covered before "
        "(the full topic list is in knowledge.csv)."
    )
    lines.append(
        "→ After writing the lesson, call:  "
        "python daily_knowledge.py --update"
    )
    lines.append("")

    if brief["reviews"]:
        lines.append(f"REVIEWS DUE ({len(brief['reviews'])})")
        lines.append("-" * 30)
        for r in brief["reviews"]:
            lines.append(f"[{r['original_date']}]  #{r['id']}  {r['topic']}")
            lines.append(f"  Level   : {r['difficulty']}")
            if r["context"]:
                lines.append(f"  Context : {r['context']}")
            lines.append(
                "  → Fetch latest news / updates on this topic and summarise what changed."
            )
            lines.append("")
        lines.append(
            "After covering the reviews, call:  "
            f"python daily_knowledge.py --mark-reviewed "
            + " ".join(r["id"] for r in brief["reviews"])
        )
    else:
        lines.append("NO REVIEWS DUE TODAY.")

    lines.append("")
    lines.append("=" * 60)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Update commands
# ---------------------------------------------------------------------------

def cmd_update(rows: list[dict]) -> None:
    """Interactively add a new lesson row (called by Claude after generating content)."""
    print("\n── Add new lesson to knowledge.csv ──")
    topic = input("Topic name (as written in Notion): ").strip()
    if not topic:
        print("Aborted: topic cannot be empty.")
        sys.exit(1)

    category = input("Category [ai/robotics/other_cs]: ").strip().lower()
    subcategory = input(
        "Subcategory [ai_tool/ai_nontechnical/ai_technical/robotics/other_cs]: "
    ).strip().lower()
    difficulty = input("Difficulty [1=beginner / 2=intermediate / 3=advanced]: ").strip()
    context = input(
        "Context for future review (key facts, what to search for). Leave blank if none: "
    ).strip()

    interval = REVIEW_INTERVALS.get(subcategory, 30)
    next_review = date.today() + timedelta(days=interval)

    row = {
        "id": str(next_id(rows)),
        "date": str(date.today()),
        "type": "lesson",
        "topic": topic,
        "category": category,
        "subcategory": subcategory,
        "difficulty": difficulty,
        "next_review": str(next_review),
        "review_interval": str(interval),
        "context_for_review": context,
    }

    rows.append(row)
    save_rows(rows)
    print(f"\n✓ Saved: '{topic}' — next review {next_review}")


def cmd_mark_reviewed(rows: list[dict], ids: list[str]) -> None:
    """Bump next_review for the given IDs and record a review_done row."""
    id_set = set(ids)
    updated = []
    for r in rows:
        if r["id"] in id_set and r["type"] == "lesson":
            interval = int(r["review_interval"])
            # Adaptive: if overdue by more than 2× interval, reset from today
            try:
                was_due = date.fromisoformat(r["next_review"])
            except ValueError:
                was_due = date.today()
            overdue_days = (date.today() - was_due).days
            if overdue_days > interval * 2:
                base = date.today()
            else:
                base = was_due
            r["next_review"] = str(base + timedelta(days=interval))
            updated.append(r["topic"])
        rows_out = rows  # mutated in place

    save_rows(rows_out)
    if updated:
        print(f"✓ Marked reviewed and bumped next_review for: {', '.join(updated)}")
    else:
        print("No matching lesson rows found for the given IDs.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Daily Knowledge brief generator")
    parser.add_argument(
        "--update",
        action="store_true",
        help="Interactively add a new lesson row after Claude generates content",
    )
    parser.add_argument(
        "--mark-reviewed",
        nargs="+",
        metavar="ID",
        help="Mark review IDs as done and bump their next_review date",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output brief as JSON instead of plain text",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Print all covered topics and exit",
    )
    args = parser.parse_args()

    rows = load_rows()

    # -- Sub-commands --------------------------------------------------------

    if args.update:
        cmd_update(rows)
        return

    if args.mark_reviewed:
        cmd_mark_reviewed(rows, args.mark_reviewed)
        return

    if args.list:
        topics = sorted(covered_topics(rows))
        if topics:
            print(f"{len(topics)} topics covered so far:")
            for t in topics:
                print(f"  • {t}")
        else:
            print("No topics covered yet.")
        return

    # -- Daily brief ---------------------------------------------------------

    category, subcategory = pick_category()
    reviews = due_reviews(rows)
    brief = build_brief(category, subcategory, reviews)

    if args.json:
        print(json.dumps(brief, indent=2, ensure_ascii=False))
    else:
        print(format_brief_text(brief))


if __name__ == "__main__":
    main()
