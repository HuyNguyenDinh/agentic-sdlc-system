.PHONY: create validate apply install-skills bootstrap bootstrap-wiki sync-agent sync-workflow test help

WORKFLOW ?= workflow/development.yaml
ADAPTER ?= multica
RUNTIME_ID ?=
MODE ?= monorepo

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

PYTHON ?= python

create: ## Scaffold a new workflow YAML (usage: make create NAME=my-workflow)
	$(PYTHON) -m src.cli create $(NAME)

validate: ## Validate a workflow YAML against schema
	$(PYTHON) -m src.cli validate $(WORKFLOW)

apply: ## Validate + render workflow YAML to markdown
	$(PYTHON) -m src.cli apply $(WORKFLOW)

install-skills: ## Install all skills from skills.txt via npx skills add
	$(PYTHON) -m src.install_skills



INCLUDE_GITNEXUS_ANALYZE ?= 0

# Examples:
#   make bootstrap                                              # wiki + skills + agents + workflow (no GitNexus analysis)
#   make bootstrap INCLUDE_GITNEXUS_ANALYZE=1                   # + monorepo (prompts for GITNEXUS_REPO)
#   make bootstrap INCLUDE_GITNEXUS_ANALYZE=1 MODE=monorepo GITNEXUS_REPO=org/repo
#   make bootstrap INCLUDE_GITNEXUS_ANALYZE=1 MODE=multi-repo GITNEXUS_REPOS="org/a org/b" GROUP_NAME=my-group
#   make bootstrap-gitnexus MODE=monorepo GITNEXUS_REPO=org/repo
#   make bootstrap-gitnexus MODE=multi-repo REPOS="org/a org/b" GROUP_NAME=my-group

bootstrap: ## Bootstrap wiki, skills, agents, workflow sync (usage: make bootstrap [WIKI_REPO=org/repo] [ADAPTER=multica] [WORKFLOW=...] [INCLUDE_GITNEXUS_ANALYZE=0|1] [MODE=monorepo|multi-repo] [GITNEXUS_REPOS="org/a org/b"] [GROUP_NAME=my-group])
	@wiki_repo="$(WIKI_REPO)"; \
	# `wiki_repo` is the private GitHub repository used to bootstrap the Obsidian Wiki
	# (owner/repo or URL). Only prompt for this when running the wiki bootstrap step.
	if [ -z "$$wiki_repo" ]; then read -r -p "Obsidian Wiki private repository to use for bootstrap (owner/repo or URL): " wiki_repo; fi; \
	adapter="$(ADAPTER)"; \
	if [ -z "$$adapter" ]; then read -r -p "Adapter (default: multica, used to sync agents and workflows): " adapter; fi; \
	if [ -z "$$adapter" ]; then adapter="multica"; fi; \
	runtime_id="$(RUNTIME_ID)"; \
	if [ -z "$$runtime_id" ]; then read -r -p "Runtime ID (optional, used to target the same runtime in sync commands): " runtime_id; fi; \
	workflow="$(WORKFLOW)"; \
	if [ -z "$$workflow" ]; then read -r -p "Workflow YAML (default: workflow/orchestrator-debate.yaml, used to sync the workflow definition): " workflow; fi; \
	if [ -z "$$workflow" ]; then workflow="$(WORKFLOW)"; fi; \
	extra_runtime_id=""; \
	if [ -n "$$runtime_id" ]; then extra_runtime_id="--runtime-id $$runtime_id"; fi; \
	$(PYTHON) -m src.cli bootstrap --repo "$$wiki_repo" --workflow "$$workflow" --adapter "$$adapter" $$extra_runtime_id $(if $(DRY_RUN),--dry-run); \
	# Optionally run GitNexus analysis if requested; prompt only when enabled.
	if [ "$(INCLUDE_GITNEXUS_ANALYZE)" = "1" ]; then \
		mode="$(MODE)"; \
		if [ "$$mode" = "monorepo" ]; then \
			gitnexus_repo="$(GITNEXUS_REPO)"; \
			if [ -z "$$gitnexus_repo" ]; then read -r -p "GitNexus monorepo to analyze (owner/repo or URL): " gitnexus_repo; fi; \
			$(MAKE) bootstrap-gitnexus MODE=$$mode REPO="$$gitnexus_repo"; \
		else \
			gitnexus_repos="$(GITNEXUS_REPOS)"; \
			if [ -z "$$gitnexus_repos" ]; then read -r -p "GitNexus repositories to group (space-separated owner/repo or URLs): " gitnexus_repos; fi; \
			$(MAKE) bootstrap-gitnexus MODE=$$mode REPOS="$$gitnexus_repos"; \
		fi; \
	fi

bootstrap-wiki: ## Bootstrap obsidian-wiki runtime at ~/obsidian-wiki with cron sync
	$(PYTHON) -m src.cli bootstrap-wiki

bootstrap-gitnexus: ## Bootstrap GitNexus runtime and analyze repo(s) (usage: make bootstrap-gitnexus MODE=monorepo GITNEXUS_REPO=org/repo | MODE=multi-repo REPOS="org/a org/b" GROUP_NAME=my-group)
	@mode="$(MODE)"; \
	if [ "$$mode" = "monorepo" ]; then \
		repo="$(REPO)"; \
		if [ -z "$$repo" ]; then read -r -p "Repository (owner/repo or URL): " repo; fi; \
		$(PYTHON) -m src.cli bootstrap-gitnexus --mode "$$mode" --repo "$$repo" $(if $(DRY_RUN),--dry-run); \
	else \
		repos="$(REPOS)"; \
		if [ -z "$$repos" ]; then read -r -p "Repositories (space-separated owner/repo or URLs): " repos; fi; \
		group_name="$(GROUP_NAME)"; \
		if [ -z "$$group_name" ]; then read -r -p "Group name: " group_name; fi; \
		$(PYTHON) -m src.cli bootstrap-gitnexus --mode "$$mode" --repos $$repos --group-name "$$group_name" $(if $(DRY_RUN),--dry-run); \
	fi

sync-agent: ## Scan agents directory recursively and publish to target adapter (usage: make sync-agent ADAPTER=multica RUNTIME_ID=my-id)
	$(PYTHON) -m src.cli sync-agent --adapter $(ADAPTER) $(if $(RUNTIME_ID),--runtime-id $(RUNTIME_ID))

sync-workflow: ## Validate + publish a workflow YAML as a squad to multica (usage: make sync-workflow WORKFLOW=workflow/product-squad.yaml)
	$(PYTHON) -m src.cli sync-workflow $(WORKFLOW) --adapter $(ADAPTER) $(if $(RUNTIME_ID),--runtime-id $(RUNTIME_ID))

test: ## Run unit tests recursively
	$(PYTHON) -m unittest discover -s tests

