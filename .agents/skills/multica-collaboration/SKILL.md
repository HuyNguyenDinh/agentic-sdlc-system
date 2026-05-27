---
name: multica-collaboration
description: Use the multica CLI to synchronize local work with the team workspace, manage projects, execute issue lifecycles, and communicate progress. Use when you need to create tasks, update issue status, assign work, post comments, or manage project coordination in the Multica workspace.
---

# Multica Workspace Collaboration

Use the multica CLI to synchronize your work with the team workspace, manage projects, execute issue lifecycles, and communicate progress.

## Workspaces and Members

| Action | Command |
| :--- | :--- |
| List Workspaces | `multica workspace list` |
| Get Workspace Details | `multica workspace get {slug}` |
| List Members | `multica workspace members` |

## Issues and Projects

| Action | Command |
| :--- | :--- |
| List Projects | `multica project list` (Run first to find project ID) |
| List Issues | `multica issue list` (Add `--status open` to filter) |
| Get Issue Details | `multica issue get {id}` |
| Create Issue | `multica issue create --title "..." --body "..." --project {project-id}` |
| Update Issue | `multica issue update {id} ...` (status, priority, assignee, etc.) |
| Assign to Agent | `multica issue assign {id} --agent {slug}` (triggers task immediately) |
| Set Status | `multica issue status {id} --set {status}` |
| Search Issues | `multica issue search "{query}"` |
| Show Agent Runs | `multica issue runs {id}` |
| Rerun Agent Task | `multica issue rerun {id}` |
| View/Post Comments | `multica issue comment {id} ...` |
| Subscribe/Unsubscribe | `multica issue subscriber {id} ...` |
| Project CRUD | `multica project list/get/create/update/delete/status` |

## Agents and Skills

| Action | Command |
| :--- | :--- |
| List Agents | `multica agent list` |
| Get Agent Config | `multica agent get {slug}` |
| Create Agent | `multica agent create ...` |
| Update Agent | `multica agent update {slug} ...` |
| Archive Agent | `multica agent archive {slug}` |
| Restore Agent | `multica agent restore {slug}` |
| Show Agent Tasks | `multica agent tasks {slug}` |
| Manage Skills | `multica agent skills ...` (attach/detach) |
| Skill CRUD | `multica skill list/get/create/update/delete` |
| Import Skill | `multica skill import ...` (from GitHub, ClawHub, or local) |
| Manage Skill Files | `multica skill files ...` |

## Squads

| Action | Command |
| :--- | :--- |
| List Squads | `multica squad list` |
| Get Squad Details | `multica squad get {id}` |
| Create Squad | `multica squad create --name "..." --leader {agent}` |
| Update Squad | `multica squad update {id} ...` (name, description, instructions, leader, or avatar) |
| Delete Squad | `multica squad delete {id}` (archive / soft-delete) |
| List Members | `multica squad member list {squad-id}` |
| Add Member | `multica squad member add {squad-id}` |
| Remove Member | `multica squad member remove {squad-id}` |
| Record Activity | `multica squad activity {issue-id} {action\|no_action\|failed} --reason "..."` |

## Autopilots

| Action | Command |
| :--- | :--- |
| List Autopilots | `multica autopilot list` |
| Get Autopilot Details | `multica autopilot get {id}` |
| Create Autopilot | `multica autopilot create ...` |
| Update Autopilot | `multica autopilot update {id} ...` |
| Delete Autopilot | `multica autopilot delete {id}` |
| Show Run History | `multica autopilot runs {id}` |
| Trigger Manually | `multica autopilot trigger {id}` |

## Daemon and Runtimes

| Action | Command |
| :--- | :--- |
| Start Daemon | `multica daemon start` (add `--foreground` to run in foreground) |
| Stop Daemon | `multica daemon stop` |
| Restart Daemon | `multica daemon restart` |
| Check Daemon Status | `multica daemon status` (online status and concurrency) |
| View Daemon Logs | `multica daemon logs` |
| List Runtimes | `multica runtime list` |
| Show Resource Usage | `multica runtime usage` |
| View Activity Log | `multica runtime activity` |
| Ping Runtime | `multica runtime ping {id}` |
| Update Runtime Config | `multica runtime update {id} ...` |

## Miscellaneous

| Action | Command |
| :--- | :--- |
| Checkout Repo | `multica repo checkout {url}` (clone locally for agents) |
| View/Edit Config | `multica config` |
| Print CLI Version | `multica version` |
| Upgrade CLI | `multica update` |
| Download Attachment | `multica attachment download {id}` (from issue or comment) |
| Get Full Help | `multica {command} --help` (detailed flags for any command) |

## Workflow Patterns

### 1. Creating and Assigning a New Task
When you need to spawn a new issue based on upstream work, link it to the correct project context:

1. Find the project: `multica project list` to get the `{project-id}`
2. Create the issue: `multica issue create --title "Task Name" --body "Details..." --project {project-id}`
3. Assign the work: `multica issue assign {new-id} --agent {target-agent-slug}`

### 2. Handling Blockers

If blocked by missing requirements or ambiguity:

1. `multica issue comment {id} --body "Blocked by [Specific Reason]. Awaiting clarification."`
2. `multica issue status {id} --set blocked`

### 3. Reporting Completion for Review

When implementation or documentation is complete:

1. Summarize: `multica issue comment {id} --body "### Summary\n- Implemented X\n- Added Y"`
2. Submit for review: `multica issue status {id} --set in_review`

## Best Practices

- **Verify IDs**: Double-check UUIDs/slugs from `multica issue list` and `multica project list` before updates
- **Use --help**: Run `multica {command} --help` for detailed flags and options
- **Check Context**: Use `multica issue get {id}` frequently to see if requirements changed while working
- **Start with Workspace**: Run `multica workspace list` first to confirm you're in the right workspace context

