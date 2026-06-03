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

## Full Bootstrap

Use the `bootstrap` command to bring up the full agent SDLC stack in one pass:

```bash
make bootstrap
```

This will:

1. Bootstrap the Obsidian Wiki (requires a private `WIKI_REPO`).
2. Install every skill listed in `skills.txt`.
3. Install GitNexus globally with `npm install -g github:HuyNguyenDinh/GitNexus` (install-only by default).
4. Sync the agent definitions to the selected adapter.
5. Sync the workflow YAML to the selected adapter.

The umbrella command prompts for the `WIKI_REPO` (private repo used by the Obsidian Wiki bootstrap), `adapter`, `runtime ID`, and `workflow` when you do not pass them on the command line. It forwards `--adapter` and `--runtime-id` to the agent and workflow sync steps, so you can keep those targets aligned with the same runtime identity you use elsewhere.

GitNexus analysis is opt-in from the umbrella flow. To enable analysis during `make bootstrap` set `INCLUDE_GITNEXUS_ANALYZE=1`. When enabled the Makefile will prompt for the GitNexus repo(s) (or you can pass `GITNEXUS_REPO` / `GITNEXUS_REPOS` on the command line).

Examples:

```bash
# Run full bootstrap without GitNexus analysis (default)
make bootstrap

# Run full bootstrap and include GitNexus monorepo analysis (prompts if GITNEXUS_REPO unset)
make bootstrap INCLUDE_GITNEXUS_ANALYZE=1 MODE=monorepo GITNEXUS_REPO=org/private-repo

# Run full bootstrap and include GitNexus multi-repo group analysis
make bootstrap INCLUDE_GITNEXUS_ANALYZE=1 MODE=multi-repo GITNEXUS_REPOS="org/a org/b" GROUP_NAME=my-group
```

## GitNexus Bootstrap

Use the `bootstrap-gitnexus` command to install and initialize GitNexus for repository codebase analysis and to build cross-repo contracts and links.

### Prerequisites

- `npm` and `npx` available on the system.
- Network access to any remote Git repositories you plan to analyze.

### Monorepo

Run analysis for a monorepo (accepts owner/repo slug or GitHub URL):

```bash
make bootstrap-gitnexus MODE=monorepo GITNEXUS_REPO=org/private-repo DRY_RUN=1
```

### Multi-repository (group)

Create or reuse a GitNexus group, analyze multiple repositories, and sync the group:

```bash
make bootstrap-gitnexus MODE=multi-repo GITNEXUS_REPOS="org/repo-a org/repo-b" GROUP_NAME=my-team DRY_RUN=1
```

### Makefile

There is a convenience Makefile target. If you omit `MODE`, it defaults to `monorepo`; if you omit the repo inputs, the target will prompt you interactively:

```bash
make bootstrap-gitnexus MODE=monorepo GITNEXUS_REPO=org/private-repo
make bootstrap-gitnexus MODE=multi-repo GITNEXUS_REPOS="org/a org/b" GROUP_NAME=my-group
make bootstrap-gitnexus
```

### What it does

- Installs `github:HuyNguyenDinh/GitNexus` globally via `npm install -g github:HuyNguyenDinh/GitNexus` if needed (or prints the install command in `--dry-run`).
- In `monorepo` mode runs `npx gitnexus analyze <repo>`.
- In `multi-repo` mode creates/uses a group, analyzes each repo, attaches results to the group, then runs `npx gitnexus group sync`.
