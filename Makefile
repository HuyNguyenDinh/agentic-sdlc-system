.PHONY: create validate apply install-skills help

WORKFLOW ?= workflow/orchestrator-debate.yaml

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

PYTHON ?= python3

create: ## Scaffold a new workflow YAML (usage: make create NAME=my-workflow)
	$(PYTHON) -m src.cli create $(NAME)

validate: ## Validate a workflow YAML against schema
	$(PYTHON) -m src.cli validate $(WORKFLOW)

apply: ## Validate + render workflow YAML to markdown
	$(PYTHON) -m src.cli apply $(WORKFLOW)

install-skills: ## Install all skills from skills.txt via npx skills add
	$(PYTHON) -m src.install_skills
