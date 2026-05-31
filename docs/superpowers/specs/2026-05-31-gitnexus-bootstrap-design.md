---
date: 2026-05-31
status: draft
topic: GitNexus Bootstrap
---

# GitNexus Bootstrap Design

## Purpose
Add a dedicated bootstrap command for GitNexus so the agent system can install and initialize GitNexus as the codebase knowledge layer.

## Scope
The bootstrap must support two operating modes:

- `single`: initialize one repository and run analysis directly on that repo.
- `multi`: initialize a GitNexus group, analyze each repository in sequence, then sync the group so GitNexus can derive shared contracts and cross-links.

The command must accept both local repository paths and GitHub repository URLs.

## User Flow
1. User runs the bootstrap command and selects the working mode.
2. The command installs GitNexus globally with `npm install -g gitnexus` if it is not already available.
3. The command resolves each input repo into a usable local repository target.
4. In `single` mode, the command runs `npx gitnexus analyze <repo>` for the selected repository.
5. In `multi` mode, the command creates or reuses a GitNexus group, loops over the repository list, pulls latest code for remote repositories when needed, analyzes each repository, and then syncs the group.

## Command Model
Add a dedicated CLI entry point instead of extending the Obsidian bootstrap command.

Suggested inputs:

- `--mode single|multi`
- `--repo` for a single repository
- `--repos` for multi-repo execution
- `--group-name` for multi-repo group identity
- `--non-interactive` to fail instead of prompting
- `--dry-run` to print planned actions without executing them

For remote repositories, the bootstrap should normalize GitHub URL input into repo identifiers and clone or update local working copies before analysis.

## Execution Details
### Single repository mode
- Ensure GitNexus is installed.
- Resolve the repository input.
- Run analysis on the repository with `npx gitnexus analyze <repo>`.

### Multi-repository mode
- Ensure GitNexus is installed.
- Resolve all repository inputs.
- Create or reuse a GitNexus group.
- For each repository:
  - fetch or pull the latest code if the input is remote,
  - run repository analysis,
  - attach the repository results to the group.
- Sync the group at the end to build shared contracts and cross-links.

## Error Handling
- Missing `npm` or `npx`: fail with a clear installation error.
- Invalid repository input: stop before any analysis starts.
- One repository failing in multi mode: report the failed repository and continue only if the command explicitly supports best-effort execution; otherwise fail fast.
- GitNexus command failures: surface the exact command and stderr output.

## Testing
Cover the bootstrap with unit tests for:

- repository input normalization,
- mode selection,
- command construction for single and multi flows,
- multi-repo group creation and sync ordering,
- error propagation from failed external commands.

Add CLI-level tests that verify the new command is wired into the entrypoint without changing the existing Obsidian bootstrap behavior.
