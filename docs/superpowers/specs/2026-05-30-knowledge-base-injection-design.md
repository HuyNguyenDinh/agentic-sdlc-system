---
date: 2026-05-30
status: draft
topic: Knowledge Base Injection
---

# Knowledge Base Injection Design

## Purpose
Implement knowledge base injection into agent workflow via orchestrator instruction injection.

## Approach
Orchestrator reads `knowledge_source` list from workflow definition, appends natural language usage instructions directly into agent system prompt.

### No extra components
- No skill resolution
- No permission system
- No proxy layer
- No agent modification required

### Injection pattern
Orchestrator appends this block to every agent prompt:
```
You have access to the following knowledge bases:
- obsidian-wiki: use /obsidian-wiki skill to query organizational knowledge
- gitnexus: use /gitnexus skill to browse and search repository code

Before starting any work, query these knowledge sources for relevant context, prior decisions and existing patterns.
```

## Flow
1.  Workflow loaded with `knowledge_sources` defined in workflow schema
2.  sync-workflow step extends existing workflow instruction injection
3.  Instruction block + access matrix generated for knowledge sources
4.  Block appended **only to orchestrator agent system prompt**
5.  Orchestrator receives instructions to inject appropriate knowledge base access when generating system prompts for other agents
6.  Prompt passed through Multica adapter unmodified
7.  Orchestrator propagates knowledge access per-agent at runtime

## Error Handling
- Missing skills: handled naturally by agent runtime
- Knowledge source down: agent receives standard skill error
- No special handling required at orchestrator layer

## Implementation Scope
Modify Multica adapter prompt preparation step to inject knowledge base instructions.

