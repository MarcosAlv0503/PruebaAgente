.PHONY: help up down migrate migrate-down test lint types build-frontend worker rn rn-retry bot-pause clean verify-template-cleanup install-agent install-dashboard check-python

# Pin Python explicitly so local environments cannot drift to 3.14+; CI uses
# the same major.minor (see .github/workflows/ci.yml).
PYTHON ?= python3.13

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "%-30s %s\n", $$1, $$2}'

check-python: ## Fail if $(PYTHON) is not exactly Python 3.13
	@$(PYTHON) -c "import sys; ver=sys.version_info; assert ver[:2] == (3, 13), f'expected Python 3.13, got {ver.major}.{ver.minor}'" \
		|| (echo "ERROR: $(PYTHON) is not Python 3.13. Install python3.13 or override PYTHON=..." && exit 1)

up: ## Start db + agent + dashboard via docker compose
	DOCKER_BUILDKIT=1 docker compose up -d
	@echo "agent  → http://localhost:8000"
	@echo "dash   → http://localhost:3000"

down: ## Stop all services and drop volumes
	docker compose down -v

migrate: ## Apply Alembic migrations against the running db
	cd agent && .venv/bin/alembic upgrade head

migrate-down: ## Rollback the last Alembic revision
	cd agent && .venv/bin/alembic downgrade -1

install-agent: check-python ## Bootstrap the agent venv with dev deps (requires Python 3.13)
	cd agent && $(PYTHON) -m venv .venv && .venv/bin/pip install --upgrade pip && .venv/bin/pip install -e ".[dev]"

install-dashboard: ## Install the dashboard's npm deps
	cd dashboard && npm install

lint: ## Lint Python and TypeScript
	cd agent && .venv/bin/ruff check src tests
	cd dashboard && npm run lint

types: ## Type-check Python (mypy strict) and TypeScript (tsc --noEmit)
	cd agent && .venv/bin/mypy --strict src
	cd dashboard && npm run typecheck

test: lint types ## Run lint + types + tests + frontend build (mirrors CI)
	cd agent && .venv/bin/pytest --cov=agent --cov-report=term-missing --cov-fail-under=70
	cd dashboard && npm run test --if-present
	$(MAKE) build-frontend

build-frontend: ## Build the dashboard (next build); runs as part of `make test`
	cd dashboard && npm run build

worker: ## Run the worker loop locally (outside docker)
	cd agent && .venv/bin/python -m agent.worker

rn: ## Run a single execution. Usage: make rn ID=<customer-id>
	@test -n "$(ID)" || (echo "ID required: make rn ID=<customer-id>" && exit 1)
	cd agent && .venv/bin/python -m agent.cli run --customer "$(ID)"

rn-retry: ## Retry a failed execution. Usage: make rn-retry ID=<execution-id>
	@test -n "$(ID)" || (echo "ID required: make rn-retry ID=<execution-id>" && exit 1)
	cd agent && .venv/bin/python -m agent.cli retry --execution "$(ID)"

bot-pause: ## Toggle the bot pause flag in the running api
	curl -X POST http://localhost:8000/api/bot/pause

verify-template-cleanup: ## Fail if any TODO loang-template marker or _example.* file remains
	@found=0; tmp=$$(mktemp); \
	grep -rn "TODO loang-template" . \
		--exclude-dir=.git --exclude-dir=node_modules --exclude-dir=.venv \
		--exclude-dir=.next --exclude-dir=__pycache__ --exclude-dir=.mypy_cache \
		--exclude-dir=.ruff_cache --exclude-dir=.pytest_cache \
		--exclude-dir=docs --exclude-dir=.github \
		--exclude=Makefile --exclude=README.md --exclude=CLAUDE.md \
		--exclude=CHANGELOG.md \
		>$$tmp 2>/dev/null || true; \
	if [ -s $$tmp ]; then \
		echo "Pending TODO loang-template markers:"; \
		cat $$tmp; \
		found=1; \
	fi; \
	rm -f $$tmp; \
	tmp2=$$(mktemp); \
	find . \( -path ./.git -o -path ./node_modules -o -path ./.venv \
		-o -path ./.next -o -name __pycache__ -o -name .mypy_cache \
		-o -name .ruff_cache -o -name .pytest_cache \) -prune -o \
		\( -name '_example*' -not -name '*.template' \) -type f -print >$$tmp2 2>/dev/null; \
	if [ -s $$tmp2 ]; then \
		echo ""; \
		echo "Pending _example.* files (delete or rename when project replaces them):"; \
		cat $$tmp2; \
		found=1; \
	fi; \
	rm -f $$tmp2; \
	if [ $$found -eq 0 ]; then \
		echo "Template fully customised — no placeholders remain."; \
	else \
		echo ""; \
		echo "ERROR: template still has unresolved placeholders. The consuming project must replace them before going live."; \
		exit 1; \
	fi

clean: ## Remove caches, venvs and build artefacts
	rm -rf agent/.venv agent/.pytest_cache agent/.mypy_cache agent/.ruff_cache agent/.coverage agent/dist agent/build
	rm -rf dashboard/node_modules dashboard/.next dashboard/.turbo
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
