> Canonical workflow definition: [`product.yaml`](./product.yaml)
# Product Squad

Product Lead-orchestrated product strategy and PRD creation workflow. Two layers of debate (strategy brief + detailed PRD) with stakeholder HITL reviews.

## Agents

| Agent | Role | Definition |
|-------|------|------------|
| `product-lead-agent` | Squad Leader, Strategist & Orchestrator | `agents/product/product-lead-agent.md` |
| `product-manager-agent` | Product Manager & PRD Writer | `agents/product/product-manager-agent.md` |
| `product-critic-agent` | Product Critic & Adversarial Reviewer | `agents/product/product-critic-agent.md` |

## Knowledge Sources

| Source | Type | Description | Access |
|--------|------|-------------|--------|
| `llm-wiki` | wiki | Obsidian-based organizational knowledge base | read, write |
| `customer-feedback` | external | Customer feedback, support tickets, and usage analytics | read |

### Knowledge Base Protocol

All agents in this squad **MUST** follow these knowledge base interaction rules:

**Before starting work** — query these sources to discover relevant prior art, decisions, patterns, and context. Use findings to inform and ground your work in existing organizational knowledge:
- `llm-wiki` (wiki)
- `customer-feedback` (external)

**After completing work** — update these sources with new artifacts, decisions, and learnings. Maintain and enrich the knowledge base at your responsibility layer level. Ensure exported knowledge is structured, cross-referenced, and reusable by other squads:
- `llm-wiki` (wiki)

## Workflow

```mermaid
flowchart TB
    Start([Lead receives raw idea])
    step_strategy-drafting["1. Squad Leader, Strategist & Orchestrator<br/>Lead drafts strategy, GTM, and metrics<br/>from raw idea"]
    Start --> step_strategy-drafting
    subgraph step_strategy-debate ["2. Debate: Lead and Critic debate the<br/>strategy brief"]
        strategy-debate_actor["Squad Leader, Strategist & Orchestrator"]
        strategy-debate_critic["Product Critic & Adversarial Reviewer"]
        strategy-debate_actor --> strategy-debate_critic
        strategy-debate_critic -->|rejected| strategy-debate_actor
        strategy-debate_actor -.->|max_turn reached| step_strategy-review
        strategy-debate_critic -->|approved| step_strategy-review
    end
    step_strategy-drafting --> step_strategy-debate
    step_strategy-review{{"3. HITL: Stakeholder reviews strategy<br/>brief"}}
    step_strategy-debate --> step_strategy-review
    step_strategy-review -->|approved| step_prd-drafting
    step_strategy-review -->|rejected| step_strategy-drafting
    step_prd-drafting["4. Product Manager & PRD Writer<br/>PM writes detailed PRD and User Stories<br/>from approved strategy"]
    step_strategy-review --> step_prd-drafting
    subgraph step_prd-debate ["5. Debate: PM and Critic debate the PRD"]
        prd-debate_actor["Product Manager & PRD Writer"]
        prd-debate_critic["Product Critic & Adversarial Reviewer"]
        prd-debate_actor --> prd-debate_critic
        prd-debate_critic -->|rejected| prd-debate_actor
        prd-debate_actor -.->|max_turn reached| step_prd-review
        prd-debate_critic -->|approved| step_prd-review
    end
    step_prd-drafting --> step_prd-debate
    step_prd-review{{"6. HITL: Stakeholder reviews the final<br/>PRD"}}
    step_prd-debate --> step_prd-review
    step_prd-review -->|approved| step_packaging
    step_prd-review -->|rejected| step_prd-drafting
    step_packaging["7. Squad Leader, Strategist & Orchestrator<br/>Lead packages approved artifacts and<br/>exports to KB"]
    step_prd-review --> step_packaging
    step_packaging --> End
    End([Done])
    style step_strategy-review fill:#FF9800,color:#fff
    style step_prd-review fill:#FF9800,color:#fff
    style Start fill:#4CAF50,color:#fff
    style End fill:#4CAF50,color:#fff
```
