# Daily Knowledge Pipeline

Automated daily learning system powered by Claude Code + Notion.

## Files

```
daily_knowledge/
├── daily_knowledge.py   # Topic picker & CSV manager (pure Python, no LLM calls)
├── knowledge.csv        # History of covered topics + review schedule
├── CLAUDE.md            # Instructions Claude Code reads for this project
└── README.md            # This file
```

---

## Setup

**1. Install dependencies**
```bash
# No external dependencies — stdlib only (csv, json, random, datetime, pathlib)
python --version  # requires 3.9+
```

**2. Connect Notion MCP in Claude Code**
In your Claude Code project settings, add the Notion MCP server:
```
https://mcp.notion.com/mcp
```
Then note the page ID of your "Daily Knowledge" parent page in Notion.

**3. Register the daily routine in Claude Code**
```
/schedule 09:00 "Run python daily_knowledge.py and follow CLAUDE.md instructions"
```

---

## Manual usage

```bash
# Get today's brief (plain text)
python daily_knowledge.py

# Get today's brief as JSON (useful for scripting)
python daily_knowledge.py --json

# List all topics covered so far
python daily_knowledge.py --list

# After Claude generates the lesson — add new row to CSV
python daily_knowledge.py --update

# After Claude covers reviews — bump their next_review dates
python daily_knowledge.py --mark-reviewed 2 3
```

---

## knowledge.csv fields

| Field | Description |
|-------|-------------|
| `id` | Auto-incremented integer |
| `date` | Date the lesson was generated |
| `type` | `lesson` (always, for now) |
| `topic` | Topic name as written in Notion |
| `category` | `ai` / `robotics` / `other_cs` |
| `subcategory` | `ai_tool` / `ai_nontechnical` / `ai_technical` / `robotics` / `other_cs` |
| `difficulty` | `1` beginner · `2` intermediate · `3` advanced |
| `next_review` | Date of next scheduled review (ISO format) |
| `review_interval` | Days between reviews (auto-set, can override) |
| `context_for_review` | What Claude should recall + search for at review time |

### Default review intervals

| Subcategory | Interval |
|-------------|----------|
| `ai_nontechnical` (news/releases) | 7 days |
| `ai_tool` | 21 days |
| `ai_technical` | 60 days |
| `robotics` / `other_cs` | 90 days |

---

## Probability distribution

```
80%  AI
  └─ 20% AI tool / hands-on tutorial
  └─ 20% AI concept (non-technical)
  └─ 60% AI technical deep dive

10%  Robotics

10%  Other Computer Science
```

---

## Extending the system

**Change probabilities** — edit `CATEGORY_WEIGHTS` and `AI_SUB_WEIGHTS` in `daily_knowledge.py`

**Change review intervals** — edit `REVIEW_INTERVALS` in `daily_knowledge.py`

**Add a new category** — add it to `CATEGORY_WEIGHTS`, `REVIEW_INTERVALS`, `SUBCATEGORY_LABELS`, and `_topic_instruction()`

**Override a specific topic's interval** — edit the `review_interval` column in `knowledge.csv` directly
