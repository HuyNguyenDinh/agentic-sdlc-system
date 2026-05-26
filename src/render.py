from pathlib import Path
import yaml


AGENT_COLORS = {
    "pm-agent": "#2196F3",
}


def _agent_display(agent_id: str, agents: list[dict]) -> str:
    for a in agents:
        if a["id"] == agent_id:
            return a["role"]
    return agent_id


def _label(text: str, width: int = 30) -> str:
    if len(text) <= width:
        return text
    words = text.split()
    lines, current = [], ""
    for w in words:
        if current and len(current) + len(w) + 1 > width:
            lines.append(current)
            current = w
        else:
            current = f"{current} {w}" if current else w
    if current:
        lines.append(current)
    return "<br/>".join(lines)


def _agent_table(agents: list[dict]) -> str:
    lines = [
        "## Agents",
        "",
        "| Agent | Role | Definition |",
        "|-------|------|------------|",
    ]
    for a in agents:
        path = a.get("path", "—")
        lines.append(f"| `{a['id']}` | {a['role']} | `{path}` |")
    return "\n".join(lines)


def render_mermaid(data: dict) -> str:
    agents = data["agents"]
    steps = data["steps"]
    lines = ["```mermaid", "flowchart TB"]

    lines.append("    Start([PM receives raw PRD])")

    prev_node = "Start"
    nodes: list[str] = []

    for idx, step in enumerate(steps):
        sid = step["id"]
        stype = step["type"]
        step_num = idx + 1
        desc = _label(step["description"])

        next_idx = idx + 1
        next_node = (
            f"step_{steps[next_idx]['id']}" if next_idx < len(steps) else "End"
        )

        if stype == "delegate":
            actor_id = step.get("actor", "")
            if isinstance(actor_id, list):
                actor_id = actor_id[0]
            actor_label = _agent_display(actor_id, agents) if actor_id else ""
            label = f"{step_num}. {actor_label}<br/>{desc}"
            node = f"step_{sid}"
            lines.append(f"    {node}[\"{label}\"]")
            lines.append(f"    {prev_node} --> {node}")
            nodes.append(node)
            prev_node = node

        elif stype == "debate":
            node = f"step_{sid}"
            label = f"{step_num}. Debate: {desc}"

            if "debates" in step:
                lines.append(f"    subgraph {node} [\"{label}\"]")
                debate_nodes = []
                for d in step["debates"]:
                    did = f"{sid}_{d['actor']}"
                    actor_label = _agent_display(d["actor"], agents)
                    critic_label = _agent_display(d["critic"], agents)
                    mt = d.get("max_turn", data["workflow"].get("max_turn", 3))
                    lines.append(
                        f"        subgraph {did} "
                        f"[\"{actor_label} &lt;-&gt; {critic_label} (max {mt} turns)\"]"
                    )
                    lines.append(f"            {did}_actor[\"{actor_label}\"]")
                    lines.append(f"            {did}_critic[\"{critic_label}\"]")
                    lines.append(f"            {did}_actor --> {did}_critic")
                    lines.append(f"            {did}_critic -->|rejected| {did}_actor")
                    debate_nodes.append(f"{did}_critic")
                    lines.append("        end")
                lines.append("    end")
                for dn in debate_nodes:
                    lines.append(f"    {dn} -->|approved| {next_node}")
                lines.append(f"    {prev_node} --> {node}")
            else:
                actor_id = step["actor"]
                critic_id = step["critic"]
                actor_label = _agent_display(actor_id, agents)
                critic_label = _agent_display(critic_id, agents)
                mt = step.get("max_turn", data["workflow"].get("max_turn", 3))

                lines.append(f"    subgraph {node} [\"{label}\"]")
                actor_node = f"{sid}_actor"
                critic_node = f"{sid}_critic"
                lines.append(f"        {actor_node}[\"{actor_label}\"]")
                lines.append(f"        {critic_node}[\"{critic_label}\"]")
                lines.append(f"        {actor_node} --> {critic_node}")
                lines.append(f"        {critic_node} -->|rejected| {actor_node}")
                lines.append(f"        {actor_node} -.->|max_turn reached| {next_node}")
                lines.append(f"        {critic_node} -->|approved| {next_node}")
                lines.append("    end")

                lines.append(f"    {prev_node} --> {node}")

            nodes.append(node)
            prev_node = node

        elif stype == "hitl":
            node = f"step_{sid}"
            label = f"{step_num}. HITL: {desc}"
            lines.append(f"    {node}{{{{\"{label}\"}}}}")
            lines.append(f"    {prev_node} --> {node}")

            on_approved = step.get("on_approved", "")
            on_rejected = step.get("on_rejected", "")
            approved_target = (
                f"step_{on_approved}" if on_approved else next_node
            )
            rejected_target = (
                f"step_{on_rejected}" if on_rejected else prev_node
            )
            lines.append(f"    {node} -->|approved| {approved_target}")
            lines.append(f"    {node} -->|rejected| {rejected_target}")

            nodes.append(node)
            prev_node = node

        elif stype == "fanout":
            node = f"step_{sid}"
            label = f"{step_num}. {desc}"
            lines.append(f"    {node}[\"{label}\"]")
            lines.append(f"    {prev_node} --> {node}")

            worker_nodes = []
            for w in step.get("workers", []):
                wid = f"{sid}_{w['id']}"
                worker_label = _agent_display(w["actor"], agents)
                lines.append(f"    {wid}[\"{worker_label}<br/>plans\"]")
                lines.append(f"    {node} --> {wid}")
                worker_nodes.append(wid)

            merge_node = f"{sid}_merge"
            lines.append(f"    {merge_node}[(\"Plans<br/>Ready\")]")
            for wn in worker_nodes:
                lines.append(f"    {wn} --> {merge_node}")

            nodes.append(node)
            prev_node = merge_node

    lines.append(f"    {prev_node} --> End")
    lines.append("    End([Done])")

    for n in nodes:
        for step in steps:
            if step["type"] == "hitl" and f"step_{step['id']}" == n:
                lines.append(f"    style {n} fill:#FF9800,color:#fff")

    lines.append("    style Start fill:#4CAF50,color:#fff")
    lines.append("    style End fill:#4CAF50,color:#fff")
    lines.append("```")

    return "\n".join(lines)


def render_markdown(data: dict, yaml_rel: str = "") -> str:
    wf = data["workflow"]
    agents = data["agents"]

    parts = []

    if yaml_rel:
        parts.append(f"> Canonical workflow definition: [`{yaml_rel}`](./{yaml_rel})")

    parts.append(f"# {wf['name'].replace('-', ' ').title()}")
    parts.append("")

    if wf.get("description"):
        parts.append(wf["description"])
        parts.append("")

    parts.append(_agent_table(agents))
    parts.append("")
    parts.append("## Workflow")
    parts.append("")
    parts.append(render_mermaid(data))
    parts.append("")

    return "\n".join(parts)


def render_file(yaml_path: str, md_path: str) -> None:
    with open(yaml_path) as f:
        data = yaml.safe_load(f)

    yaml_rel = Path(yaml_path).name
    markdown = render_markdown(data, yaml_rel)

    with open(md_path, "w") as f:
        f.write(markdown)
