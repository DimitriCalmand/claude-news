# Daily Knowledge — Claude Code Instructions

## What this project does

Every morning, this routine:
1. Runs `daily_knowledge.py` to get today's brief (new topic + due reviews)
2. Generates a rich Notion page for the new lesson
3. Fetches updates for any due review topics
4. Updates `knowledge.csv` via the script's `--add-lesson` and `--mark-reviewed` commands

---

## Daily routine (run at 09:00)

```
Step 1 — Get the brief
  python daily_knowledge.py --json

Step 2 — Generate lesson & reviews (see format below)
  Write a Notion page for the new topic. Note the page ID returned by the Notion API.
  For each due review, search the web and summarise what changed.

Step 3 — Save to CSV (non-interactive, automated)
  python daily_knowledge.py --add-lesson \
    --topic "<exact title as written in Notion, WITHOUT the emoji>" \
    --category <ai|robotics|other_cs> \
    --subcategory <ai_tool|ai_nontechnical|ai_technical|robotics|other_cs> \
    --difficulty <1|2|3> \
    --context "<key facts + what to search at review time>" \
    --notion-page-id "<page ID returned by Notion API>"

Step 4 — Mark reviews done (if any were due)
  python daily_knowledge.py --mark-reviewed <id1> <id2> ...

Step 5 — Commit and push directly to main
  git checkout main
  git add knowledge.csv
  git commit -m "chore: daily knowledge $(date +%Y-%m-%d)"
  git push origin main
```

**CRITICAL: Always run `git checkout main` before committing. Never push to a `claude/*` branch. Never open a pull request.**

---

## Notion page format

Target: the "Daily Knowledge" parent page.
Create one child page per lesson with this structure.
**After creating the page, capture the page ID from the Notion API response — you will need it for Step 3 (`--notion-page-id`).**

### Page title

Must follow this exact format: `<emoji> [YYYY-MM-DD] <Topic Name>`

- Pick one emoji that genuinely fits the topic (e.g. 🧠 for ML concepts, 🔧 for tools, 🤖 for robotics, 🔐 for crypto/security, 🌐 for networking, ⚙️ for systems)
- The emoji makes the page instantly recognisable in the Notion sidebar
- Examples:
  - `🧠 [2026-06-16] Mixture of Experts`
  - `✍️ [2026-06-17] GitHub Copilot — Beyond Autocomplete`
  - `🌐 [2026-06-18] Consistent Hashing`

### Page body (in order)

**TL;DR** *(2–3 sentences, jargon-free)*

**The concept**
- Friendly explanation with concrete analogies
- Real-world examples
- Equations where they add clarity (use LaTeX-style notation)
- At least one diagram or graph if the topic is visual (describe it clearly; generate SVG if possible)

**Work angle**
Connect to: NLP, content moderation, LLM pipelines, AWS/SageMaker, or Bedrock — whichever is relevant.
If no direct connection exists, note that explicitly.

**Key takeaways** *(bullet list, max 5)*

**Further reading** *(3 links — prefer papers, official docs, or high-quality blog posts)*

**Tags**: add Notion tags for category, subcategory, and difficulty level.

---

## Review page format

For each due review, append a section to the same daily Notion page (after the main lesson):

```
--- REVIEW: <Topic> (originally covered <date>) ---

What we covered last time:
<brief recap from context_for_review field>

What changed since then:
<web search results summarised — be specific: dates, numbers, names>

Still relevant to your work?
<yes/no + one sentence why>
```

---

## Tone guidelines

- Friendly, not dry. Write like a smart colleague explaining over coffee.
- Concrete before abstract. Always give an example before the formal definition.
- Depth scales with difficulty: level 1 = intuition only, level 2 = intuition + mechanics, level 3 = full technical depth including math.
- Never skip the work angle — this is the most important part for making knowledge stick.

---

## Context about the learner

- Works on ML/content moderation pipelines at Wildworks
- Daily tools: Python, pandas, AWS Bedrock, SageMaker, Amazon Nova models
- Comfortable with: transformers, fine-tuning (RoBERTa), LLM classification prompts, data engineering
- Wants both breadth (new topics) and depth (technical AI)
- Communicates in French conversationally, English for technical content — write lessons in **English**

### What `ai_tool` means

AI-powered tools and products that improve daily life or work — assistants, creative tools, productivity apps, coding helpers. Examples: Claude, Gemini, HeyGen, Notion AI, GitHub Copilot, Cursor, Perplexity, ElevenLabs, Kling, Suno.

**Not** cloud infrastructure (AWS Bedrock, GCP Vertex, Azure OpenAI) — those belong in `ai_technical` if covered at all.
