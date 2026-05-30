# Knowledge Base Injection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend markdown renderer to append knowledge base skill usage instructions for every agent defined in workflow.

**Architecture:** Extend existing `render_markdown()` function. Add knowledge source → skill mapping, generate instruction block + agent access matrix, append ONLY to orchestrator agent instructions. Orchestrator will propagate knowledge access to other agents at runtime when generating their prompts.

**Tech Stack:** Python 3.12, stdlib

---

### Task 1: Extend markdown renderer with knowledge skill injection

**Files:**
- Modify: `src/adapters/markdown_renderer.py:215`
- Test: `tests/test_markdown_renderer.py`

- [ ] **Step 1: Write failing test**

Add this test to `tests/test_markdown_renderer.py`:
```python
def test_render_markdown_appends_knowledge_skill_instructions(self):
    test_data = {
        "workflow": {"name": "test-workflow"},
        "agents": [
            {"id": "pm-agent", "role": "PM", "path": "agents/pm.md"},
            {"id": "coder-agent", "role": "Coder", "path": "agents/coder.md"}
        ],
        "knowledge_sources": [
            {"id": "obsidian-wiki", "type": "wiki", "description": "Org wiki", "access": ["read"]},
            {"id": "gitnexus", "type": "repository", "description": "Codebase", "access": ["read"]}
        ],
        "steps": []
    }

    rendered = render_markdown(test_data)

    self.assertIn("You have access to the following knowledge bases:", rendered)
    self.assertIn("- obsidian-wiki: use /obsidian-wiki skill to query organizational knowledge", rendered)
    self.assertIn("- gitnexus: use /gitnexus skill to browse and search repository code", rendered)
    self.assertIn("Before starting any work, query these knowledge sources", rendered)
```

- [ ] **Step 2: Run test verify fails**
Run: `python -m unittest tests/test_markdown_renderer.py`
Expected: FAIL

- [ ] **Step 3: Implement instruction injection**

Modify `render_markdown()` function at the END before return:
```python
    # Inject knowledge base skill usage instructions
    ks = data.get("knowledge_sources")
    if ks:
        parts.append("")
        parts.append("---")
        parts.append("## Knowledge Base Access")
        parts.append("")
        parts.append("You have access to the following knowledge bases:")
        for source in ks:
            if source["id"] == "obsidian-wiki":
                parts.append(f"- `obsidian-wiki`: use `/obsidian-wiki` skill to query organizational knowledge, prior decisions and patterns")
            elif source["id"] == "gitnexus":
                parts.append(f"- `gitnexus`: use `/gitnexus` skill to browse, search and read repository code")
            else:
                parts.append(f"- `{source['id']}`: use `/{source['id']}` skill")
        parts.append("")
        parts.append("**Before starting any work, query these knowledge sources for relevant context. Always check existing knowledge before making new decisions.**")
        parts.append("")

    return "\n".join(parts)
```

- [ ] **Step 4: Run test verify passes**
Run: `python -m unittest tests/test_markdown_renderer.py`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add src/adapters/markdown_renderer.py tests/test_markdown_renderer.py
git commit -m "renderer: inject knowledge base skill usage instructions"
```

---

### Task 2: Verify end to end with sync-workflow

**Files:** None (test existing workflow)

- [ ] **Step 1: Run sync-workflow on test workflow**
Run: `python -m src.cli sync-workflow workflow/development.yaml`
Expected: Output shows knowledge base instructions added to rendered workflow

- [ ] **Step 2: Verify all existing tests pass**
Run: `python -m unittest discover -s tests`
Expected: All tests pass

---

Plan complete and saved to `docs/superpowers/plans/2026-05-30-knowledge-base-injection.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
