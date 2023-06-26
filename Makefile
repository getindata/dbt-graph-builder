.PHONY: check-hooks install install-dev

install-dev:
	@echo "Installing dev packages..."
	@pip install pipx
	@pipx install pdm
	@pdm install --dev

check-hooks:
	@echo "Checking pre-commit hooks..."
	@pre-commit run --all-files
	@echo "Done."
