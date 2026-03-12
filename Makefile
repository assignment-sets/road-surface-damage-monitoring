.PHONY: dev

dev:
	uv run --env-file .env python -m $(subst /,.,$(filter-out $@,$(MAKECMDGOALS)))

%:
	@: