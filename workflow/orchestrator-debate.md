> Canonical workflow definition: [`orchestrator-debate.yaml`](./orchestrator-debate.yaml)
# Orchestrator Debate

PM-orchestrated multi-agent debate workflow for SDLC. Two debate layers (architecture + implementation) with HITL gate.


## Agents

| Agent | Role | Definition |
|-------|------|------------|
| `pm-agent` | Squad Leader & Orchestrator | `agents/management/pm-agent.md` |
| `sa-agent` | Software Architect | `agents/solution_architect/sa-agent.md` |
| `sa-critic-agent` | Architecture Critic | `agents/solution_architect/sa-critic-agent.md` |
| `coder-agent` | Software Developer | `agents/coding/coder.md` |
| `code-critic-agent` | Code Reviewer | `agents/coding/code-critic.md` |
| `qa-agent` | Quality Assurance | `agents/qa/qa.md` |
| `qa-critic-agent` | QA Reviewer | `agents/qa/qa-critic.md` |

## Knowledge Sources

| Source | Type | Description | Access |
|--------|------|-------------|--------|
| `codebase` | repository | Project source code and documentation | read, write |
| `llm-wiki` | wiki | Obsidian-based organizational knowledge base | read, write |

### Knowledge Base Protocol

All agents in this squad **MUST** follow these knowledge base interaction rules:

**Before starting work** — query these sources to discover relevant prior art, decisions, patterns, and context. Use findings to inform and ground your work in existing organizational knowledge:
- `codebase` (repository)
- `llm-wiki` (wiki)

**After completing work** — update these sources with new artifacts, decisions, and learnings. Maintain and enrich the knowledge base at your responsibility layer level. Ensure exported knowledge is structured, cross-referenced, and reusable by other squads:
- `codebase` (repository)
- `llm-wiki` (wiki)

## Workflow

```mermaid
flowchart TB
    Start([PM receives raw PRD])
    step_initialization["1. Software Architect<br/>PM assigns SA to create a<br/>draft SRS from the raw PRD"]
    Start --> step_initialization
    subgraph step_architecture-debate ["2. Debate: SA and SA Critic debate to<br/>refine the architecture"]
        architecture-debate_actor["Software Architect"]
        architecture-debate_critic["Architecture Critic"]
        architecture-debate_actor --> architecture-debate_critic
        architecture-debate_critic -->|rejected| architecture-debate_actor
        architecture-debate_actor -.->|max_turn reached| step_hitl
        architecture-debate_critic -->|approved| step_hitl
    end
    step_initialization --> step_architecture-debate
    step_hitl{{"3. HITL: Product Owner reviews and<br/>approves the finalized SRS"}}
    step_architecture-debate --> step_hitl
    step_hitl -->|approved| step_implementation-planning
    step_hitl -->|rejected| step_initialization
    step_implementation-planning["4. Squad Leader & Orchestrator<br/>PM breaks down tasks and<br/>assigns to Workers"]
    step_hitl --> step_implementation-planning
    step_worker-plans["5. Workers submit their<br/>Implementation Plans in<br/>parallel"]
    step_implementation-planning --> step_worker-plans
    worker-plans_coder-plan["Software Developer<br/>plans"]
    step_worker-plans --> worker-plans_coder-plan
    worker-plans_qa-plan["Quality Assurance<br/>plans"]
    step_worker-plans --> worker-plans_qa-plan
    worker-plans_merge[("Plans<br/>Ready")]
    worker-plans_coder-plan --> worker-plans_merge
    worker-plans_qa-plan --> worker-plans_merge
    subgraph step_implementation-debate ["6. Debate: Critics review Implementation<br/>Plans; adversarial debate loop"]
        subgraph implementation-debate_coder-agent ["Software Developer &lt;-&gt; Code Reviewer (max 3 turns)"]
            implementation-debate_coder-agent_actor["Software Developer"]
            implementation-debate_coder-agent_critic["Code Reviewer"]
            implementation-debate_coder-agent_actor --> implementation-debate_coder-agent_critic
            implementation-debate_coder-agent_critic -->|rejected| implementation-debate_coder-agent_actor
        end
        subgraph implementation-debate_qa-agent ["Quality Assurance &lt;-&gt; QA Reviewer (max 3 turns)"]
            implementation-debate_qa-agent_actor["Quality Assurance"]
            implementation-debate_qa-agent_critic["QA Reviewer"]
            implementation-debate_qa-agent_actor --> implementation-debate_qa-agent_critic
            implementation-debate_qa-agent_critic -->|rejected| implementation-debate_qa-agent_actor
        end
    end
    implementation-debate_coder-agent_critic -->|approved| step_execution
    implementation-debate_qa-agent_critic -->|approved| step_execution
    worker-plans_merge --> step_implementation-debate
    step_execution["7. Software Developer<br/>Workers write code and test<br/>suites"]
    step_implementation-debate --> step_execution
    step_completion["8. Squad Leader & Orchestrator<br/>PM synthesizes results and<br/>reports"]
    step_execution --> step_completion
    step_completion --> End
    End([Done])
    style step_hitl fill:#FF9800,color:#fff
    style Start fill:#4CAF50,color:#fff
    style End fill:#4CAF50,color:#fff
```
