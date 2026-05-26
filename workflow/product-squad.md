> Canonical workflow definition: [`product-squad.yaml`](./product-squad.yaml)
# Product Squad

Product Lead-orchestrated product discovery and PRD creation workflow. Two layers of debate (discovery brief + detailed PRD) with stakeholder HITL reviews.


## Agents

| Agent | Role | Definition |
|-------|------|------------|
| `product-lead-agent` | Squad Leader & Orchestrator | `agents/product/product-lead.md` |
| `product-manager-agent` | Product Manager & PRD Writer | `agents/product/product-manager.md` |
| `product-critic-agent` | Product Critic & Reviewer | `agents/product/product-critic.md` |

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
    Start([PM receives raw PRD])
    step_discovery["1. Product Manager & PRD Writer<br/>PM drafts discovery brief from<br/>raw feature request"]
    Start --> step_discovery
    subgraph step_discovery-debate ["2. Debate: PM and Critic debate the<br/>discovery brief"]
        discovery-debate_actor["Product Manager & PRD Writer"]
        discovery-debate_critic["Product Critic & Reviewer"]
        discovery-debate_actor --> discovery-debate_critic
        discovery-debate_critic -->|rejected| discovery-debate_actor
        discovery-debate_actor -.->|max_turn reached| step_discovery-review
        discovery-debate_critic -->|approved| step_discovery-review
    end
    step_discovery --> step_discovery-debate
    step_discovery-review{{"3. HITL: Stakeholder reviews discovery<br/>brief"}}
    step_discovery-debate --> step_discovery-review
    step_discovery-review -->|approved| step_prd-drafting
    step_discovery-review -->|rejected| step_discovery
    step_prd-drafting["4. Product Manager & PRD Writer<br/>PM writes detailed PRD from<br/>approved brief"]
    step_discovery-review --> step_prd-drafting
    subgraph step_prd-debate ["5. Debate: PM and Critic debate the PRD"]
        prd-debate_actor["Product Manager & PRD Writer"]
        prd-debate_critic["Product Critic & Reviewer"]
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
    step_packaging["7. Squad Leader & Orchestrator<br/>Product Lead packages approved<br/>PRD and exports to KB"]
    step_prd-review --> step_packaging
    step_packaging --> End
    End([Done])
    style step_discovery-review fill:#FF9800,color:#fff
    style step_prd-review fill:#FF9800,color:#fff
    style Start fill:#4CAF50,color:#fff
    style End fill:#4CAF50,color:#fff
```
