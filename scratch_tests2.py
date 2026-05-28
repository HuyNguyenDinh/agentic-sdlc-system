import re

with open("tests/test_multica_adapter.py", "r") as f:
    text = f.read()

# Modify make_smart_mock to accept initial_squads
text = text.replace(
    "def make_smart_mock(mock_list):",
    "def make_smart_mock(mock_list, initial_squads=None):\n    if initial_squads is None:\n        initial_squads = [('uuid-my-squad', 'my-squad'), ('uuid-kw-squad', 'kw-squad')]"
)
text = text.replace(
    'base += "uuid-my-squad my-squad lead 1\\n"\n            base += "uuid-kw-squad kw-squad lead 1\\n"',
    'for u, n in initial_squads:\n                base += f"{u} {n} lead 1\\n"'
)

# For update flow, add product-squad to initial_squads
text = text.replace(
    "mock_run.side_effect = make_smart_mock([\n            mock_get, mock_update,",
    "mock_run.side_effect = make_smart_mock([\n            mock_get, mock_update,"
) # wait, I can just use a regex

# Let's just fix test_publish_workflow_create_flow:
# remove mock_get entirely
text = re.sub(
    r'mock_get = MagicMock\(returncode=1\)\n\s+# 2\. Mock multica squad create',
    r'# 1. (removed mock_get)\n        # 2. Mock multica squad create',
    text
)
text = text.replace(
    "make_smart_mock([\n            mock_get, mock_create,",
    "make_smart_mock([\n            mock_create,"
)

# Fix test_publish_workflow_update_flow
# mock_get = MagicMock(returncode=0) -> remove
text = re.sub(
    r'mock_get = MagicMock\(returncode=0\)\n\s+# 2\. Mock multica squad update',
    r'# 1. (removed mock_get)\n        # 2. Mock multica squad update',
    text
)
text = text.replace(
    "make_smart_mock([\n            mock_get, mock_update,",
    "make_smart_mock([\n            mock_update,"
)
# change update assertion to use uuid-product-squad
text = text.replace(
    '["multica", "squad", "update", "product-squad", "--description", "Manage product features"],',
    '["multica", "squad", "update", "uuid-product-squad", "--description", "Manage product features"],'
)

# Fix test_publish_workflow_idempotent_flow
text = re.sub(
    r'mock_get = MagicMock\(returncode=0\)\n\s+# 2\. Mock multica squad update',
    r'# 1. (removed mock_get)\n        # 2. Mock multica squad update',
    text
)
text = text.replace(
    "make_smart_mock([\n            mock_get, mock_update,",
    "make_smart_mock([\n            mock_update,"
)
text = text.replace(
    '["multica", "squad", "update", "product-squad"],',
    '["multica", "squad", "update", "uuid-product-squad"],'
)

# Fix test_publish_workflow_failure_flow (squad create fails)
text = text.replace(
    "make_smart_mock([\n            mock_get, mock_create",
    "make_smart_mock([\n            mock_create"
)

# Fix test_publish_workflow_leader_update_failure
text = text.replace(
    "make_smart_mock([\n            mock_get, mock_create",
    "make_smart_mock([\n            mock_create"
)

# Fix test_publish_workflow_leader_not_found
text = text.replace(
    "make_smart_mock([\n            mock_get, mock_create",
    "make_smart_mock([\n            mock_create"
)

# Fix test_publish_workflow_squad_members
text = re.sub(
    r'mock_squad_get = MagicMock\(returncode=0\)\n\s+mock_squad_update = MagicMock',
    r'# (removed mock_squad_get)\n        mock_squad_update = MagicMock',
    text
)
text = text.replace(
    "make_smart_mock([\n            mock_squad_get, mock_squad_update,",
    "make_smart_mock([\n            mock_squad_update,"
)
text = text.replace(
    '["multica", "squad", "member", "add", "my-squad"',
    '["multica", "squad", "member", "add", "uuid-my-squad"'
)


# Finally we must pass initial_squads for update and idempotent flow!
text = text.replace(
    "def test_publish_workflow_update_flow(self, mock_run):\n",
    "def test_publish_workflow_update_flow(self, mock_run):\n        initial = [('uuid-product-squad', 'product-squad')]\n"
)
text = text.replace(
    "def test_publish_workflow_idempotent_flow(self, mock_run):\n",
    "def test_publish_workflow_idempotent_flow(self, mock_run):\n        initial = [('uuid-product-squad', 'product-squad')]\n"
)

text = re.sub(
    r'test_publish_workflow_update_flow(.*?)make_smart_mock\(\[',
    r'test_publish_workflow_update_flow\1make_smart_mock([',
    text, flags=re.DOTALL
) # Wait, it's easier to just match the exact make_smart_mock line inside those methods.

with open("tests/test_multica_adapter.py", "w") as f:
    f.write(text)
