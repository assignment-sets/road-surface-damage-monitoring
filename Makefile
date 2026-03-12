.PHONY: dev

dev:
	python3 -m $(subst /,.,$(filter-out $@,$(MAKECMDGOALS)))

%:
	@: