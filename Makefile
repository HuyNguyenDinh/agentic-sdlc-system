.PHONY: create validate apply install-skills sync-agent sync-workflow test help

WORKFLOW ?= workflow/orchestrator-debate.yaml
ADAPTER ?= multica
RUNTIME_ID ?=

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

sync-agent: ## Scan agents directory recursively and publish to target adapter (usage: make sync-agent ADAPTER=multica RUNTIME_ID=my-id)
	$(PYTHON) -m src.cli sync-agent --adapter $(ADAPTER) $(if $(RUNTIME_ID),--runtime-id $(RUNTIME_ID))

sync-workflow: ## Validate + publish a workflow YAML as a squad to multica (usage: make sync-workflow WORKFLOW=workflow/product-squad.yaml)
	$(PYTHON) -m src.cli sync-workflow $(WORKFLOW) --adapter $(ADAPTER) $(if $(RUNTIME_ID),--runtime-id $(RUNTIME_ID))

test: ## Run unit tests recursively
	$(PYTHON) -m unittest discover -s tests

