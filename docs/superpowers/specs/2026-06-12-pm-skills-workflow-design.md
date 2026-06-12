# PM Skills Workflow Design

## Context
The goal is to minimalize and adapt the `pm-skills` repository for the `product-squad` workflow in an agentic SDLC workspace. The workspace represents a one-man company where the human acts as the Product Owner/Stakeholder, and the AI agents handle the heavy lifting. 

## Approach Selected: Deep Specialization
We are maintaining the multi-agent debate system (Product Lead, Product Manager, Product Critic) but rigorously narrowing their focus to a core subset of PM skills to prevent context bloat and maximize their leverage.

## Agent Skill Mapping
We will inject specific skills from the `pm-skills` repository into the system prompts for each agent:

### 1. Product Lead (The Strategist)
**Role:** Define vision, strategy, and go-to-market.
**Required Skills:**
- `product-strategy`: 9-section Product Strategy Canvas.
- `gtm-strategy`: GTM channels, messaging, and launch plans.
- `north-star-metric`: Defining primary and input metrics.

### 2. Product Manager (The Builder)
**Role:** Translate strategy into executable specs and user stories.
**Required Skills:**
- `opportunity-solution-tree`: Mapping outcomes to solutions/experiments.
- `create-prd`: Rigorous 8-section PRD template.
- `user-stories`: Breaking features into backlog items (INVEST criteria).

### 3. Product Critic (The Red Teamer)
**Role:** Adversarially stress-test output to find blind spots.
**Required Skills:**
- `strategy-red-team`: Surfacing load-bearing assumptions and cheapest tests.
- `identify-assumptions-new`: Categorizing risks across GTM, Viability, and Feasibility.
- `pre-mortem`: Risk classification (Tigers/Paper Tigers/Elephants).

## Workflow Modifications
The `workflow/product.yaml` and `workflow/product.md` will be updated to elevate the Product Lead to the beginning of the flow, replacing the PM's "discovery brief" with a formal strategy phase.

**New Workflow Steps:**
1. **Strategy Phase**: Product Lead drafts Product Strategy & North Star from raw idea.
2. **Strategy Debate**: Product Lead and Product Critic debate the strategy (Critic uses red-team skills).
3. **Strategy Review**: HITL Stakeholder reviews and approves the strategy.
4. **Execution Phase**: Product Manager drafts PRD and User Stories based on approved strategy.
5. **Execution Debate**: Product Manager and Product Critic debate specs (Critic runs pre-mortem).
6. **PRD Review**: HITL Stakeholder reviews and approves PRD.
7. **Packaging**: Product Lead packages final assets to the Knowledge Base.
