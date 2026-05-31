# agentic-sdlc-system

## Obsidian Wiki Bootstrap

Use the `bootstrap-wiki` command to initialize a private Obsidian Wiki vault for agent knowledge usage.

### Prerequisites

- `gh` installed and authenticated with access to the private repository.
- `git`, `python`, `pip`, and `crontab` available on the system.
- Permission to write to `~/obsidian-wiki` or a custom `--vault-path`.

### Bootstrap

```bash
make bootstrap-wiki
```

This will:

1. Clone the private repo into `~/obsidian-wiki` using `gh`.
2. Clone `https://github.com/Ar9av/obsidian-wiki.git` into a temporary installer checkout.
3. Write `OBSIDIAN_VAULT_PATH=~/obsidian-wiki` into the installer checkout `.env`.
4. Run `OBSIDIAN_VAULT_PATH=~/obsidian-wiki bash setup.sh`.
5. Run `obsidian-wiki setup --vault ~/obsidian-wiki`.
6. Remove the temporary installer checkout after setup completes.
7. Install a cron entry that runs every 5 minutes:

```cron
*/5 * * * * cd ~/obsidian-wiki && git add . && git commit -m "automated backup commit" && git push origin main
```

### Verification

Run a post-bootstrap check to confirm the env var, cron entry, and git remote are in place:

```bash
python -m src.cli check-wiki-bootstrap --repo org/private-kb
```

## GitNexus Bootstrap

Use the `bootstrap-gitnexus` command to install and initialize GitNexus for repository codebase analysis and to build cross-repo contracts and links.

### Prerequisites

- `npm` and `npx` available on the system.
- Network access to any remote Git repositories you plan to analyze.

### Single repository

Run analysis for a single repository (accepts owner/repo slug or GitHub URL):

```bash
make bootstrap-gitnexus MODE=single REPO=org/private-repo DRY_RUN=1
```

### Multi-repository (group)

Create or reuse a GitNexus group, analyze multiple repositories, and sync the group:

```bash
make bootstrap-gitnexus MODE=multi REPOS="org/repo-a org/repo-b" GROUP_NAME=my-team DRY_RUN=1
```

### Makefile

There is a convenience Makefile target:

```bash
make bootstrap-gitnexus MODE=single REPO=org/private-repo
make bootstrap-gitnexus MODE=multi REPOS="org/a org/b" GROUP_NAME=my-group
```

### What it does

- Installs `gitnexus` globally via `npm install -g gitnexus` if needed (or prints the install command in `--dry-run`).
- In `single` mode runs `npx gitnexus analyze <repo>`.
- In `multi` mode creates/uses a group, analyzes each repo, attaches results to the group, then runs `npx gitnexus group sync`.
