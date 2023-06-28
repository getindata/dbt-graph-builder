.PHONY: check-hooks install-dev

install-dev:
	@echo "Installing dev packages..."
	@pip install pipx
	@pipx install pdm
	@pdm install --dev
	@echo "Installing pre-commit hooks..."
	@pre-commit install

check-hooks:
	@echo "Checking pre-commit hooks..."
	@pre-commit run --all-files
	@echo "Done."
