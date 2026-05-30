from typing import Dict, Any, List, Optional
import re
from dataclasses import dataclass


@dataclass
class RenderContext:
    variables: Dict[str, Any]
    knowledge_bindings: List[Dict[str, Any]]
    agent_id: str
    task_type: str


@dataclass
class RenderedInstruction:
    content: str
    used_variables: List[str]
    injected_bindings: int
    render_time_ms: float


class AgentInstructionRenderer:
    """
    Renders agent instructions with variable substitution, knowledge binding injection,
    and structured render pipeline.
    """

    VARIABLE_PATTERN = re.compile(r'\{\{\s*([a-zA-Z0-9_\.]+)\s*\}\}')

    def __init__(self):
        self._render_hooks: List[callable] = []

    def render(self, template: str, context: RenderContext) -> RenderedInstruction:
        """Execute full render pipeline on template."""
        import time
        start = time.time()

        # Step 1: Resolve variables
        content, used_vars = self._resolve_variables(template, context.variables)

        # Step 2: Inject knowledge bindings
        content, bindings_injected = self._inject_knowledge_bindings(content, context.knowledge_bindings)

        # Step 3: Run post-render hooks
        for hook in self._render_hooks:
            content = hook(content, context)

        render_time = (time.time() - start) * 1000

        return RenderedInstruction(
            content=content,
            used_variables=used_vars,
            injected_bindings=bindings_injected,
            render_time_ms=round(render_time, 2)
        )

    def _resolve_variables(self, template: str, variables: Dict[str, Any]) -> tuple[str, List[str]]:
        """Replace {{variable}} placeholders with values from context."""
        used = []

        def replace_match(match: re.Match) -> str:
            var_name = match.group(1)
            value = self._get_nested_value(variables, var_name)
            if value is not None:
                used.append(var_name)
                return str(value)
            return match.group(0)

        result = self.VARIABLE_PATTERN.sub(replace_match, template)
        return result, used

    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Optional[Any]:
        """Get nested dictionary value using dot notation path."""
        parts = path.split('.')
        current = data
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current

    def _inject_knowledge_bindings(self, content: str, bindings: List[Dict[str, Any]]) -> tuple[str, int]:
        """Inject knowledge bindings as clean comment header at very top."""
        if not bindings:
            return content, 0

        footer = "\n### MANDATORY CONSTRAINT\n\n"
        footer += "✅ **YOU MUST QUERY ALL ATTACHED KNOWLEDGE BASES TO VERIFY YOUR THINKING AND ANSWERBEFORE PRODUCING ANY OUTPUT.**\n"
        footer += "✅ Do not start design work until you have read existing patterns, decisions and architecture from knowledge sources.\n"
        footer += "✅ Cite knowledge sources when justifying architectural decisions.\n"
    
        # Append matrix to bottom
        footer += "\n---\n### Knowledge Base Access Matrix\n\n"
        footer += "| Source | Mode | Access | Scope |\n"
        footer += "|--------|------|--------|-------|\n"

        for b in bindings:
            access = "✏️ Read/Write" if 'write' in b.get('access', []) else "📖 Read Only"
            footer += f"| `{b.get('source', 'unknown')}` | {b.get('mode', 'default')} | {access} | {', '.join(b.get('scope', []))} |\n"


        return content + footer, len(bindings)

    def add_render_hook(self, hook: callable) -> None:
        """Add post-render hook to pipeline."""
        self._render_hooks.append(hook)
