import pytest
from src.core.services.agent_instruction_renderer import AgentInstructionRenderer, RenderContext


@pytest.fixture
def renderer():
    return AgentInstructionRenderer()


def test_variable_substitution(renderer):
    template = "Hello {{user.name}}, your task is {{task.title}}"
    context = RenderContext(
        variables={"user": {"name": "Alice"}, "task": {"title": "Code Review"}},
        knowledge_bindings=[],
        agent_id="agent-123",
        task_type="review"
    )

    result = renderer.render(template, context)

    assert "Hello Alice, your task is Code Review" == result.content
    assert "user.name" in result.used_variables
    assert "task.title" in result.used_variables
    assert result.injected_bindings == 0


def test_missing_variable_leaves_placeholder(renderer):
    template = "Value: {{missing.var}}"
    context = RenderContext(variables={}, knowledge_bindings=[], agent_id="test", task_type="test")

    result = renderer.render(template, context)

    assert result.content == "Value: {{missing.var}}"
    assert len(result.used_variables) == 0


def test_knowledge_binding_injection(renderer):
    template = "Base instruction content"
    bindings = [
        {"id": "kb-001", "content": "Previous review guidelines"},
        {"id": "kb-002", "content": "Project coding standards"}
    ]
    context = RenderContext(
        variables={},
        knowledge_bindings=bindings,
        agent_id="agent-123",
        task_type="review"
    )

    result = renderer.render(template, context)

    assert "KNOWLEDGE CONTEXT" in result.content
    assert "Previous review guidelines" in result.content
    assert "Project coding standards" in result.content
    assert result.injected_bindings == 2


def test_empty_bindings_no_injection(renderer):
    template = "Plain instruction"
    context = RenderContext(variables={}, knowledge_bindings=[], agent_id="test", task_type="test")

    result = renderer.render(template, context)

    assert "KNOWLEDGE CONTEXT" not in result.content
    assert result.injected_bindings == 0


def test_render_hook_execution(renderer):
    template = "original content"

    def uppercase_hook(content, ctx):
        return content.upper()

    renderer.add_render_hook(uppercase_hook)
    context = RenderContext(variables={}, knowledge_bindings=[], agent_id="test", task_type="test")

    result = renderer.render(template, context)

    assert result.content == "ORIGINAL CONTENT"


def test_full_render_pipeline(renderer):
    template = "Agent: {{agent.name}}\nTask: {{task.id}}"
    variables = {"agent": {"name": "ReviewBot"}, "task": {"id": 42}}
    bindings = [{"id": "kb-1", "content": "Sample binding"}]
    context = RenderContext(
        variables=variables,
        knowledge_bindings=bindings,
        agent_id="review-bot",
        task_type="review"
    )

    result = renderer.render(template, context)

    assert "Agent: ReviewBot" in result.content
    assert "Task: 42" in result.content
    assert "KNOWLEDGE CONTEXT" in result.content
    assert result.render_time_ms > 0
    assert len(result.used_variables) == 2
    assert result.injected_bindings == 1
