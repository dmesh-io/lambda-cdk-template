SHELL=/bin/bash

#
# You can use tab for autocomplete on your terminal
# > make[space][tab]
#

.DEFAULT_GOAL := help
.PHONY: help
help:  ## display this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-30s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Clean up

clean: ## Clean up module
	@rm -Rf build/
	@rm -Rf dist/
	@rm -Rf .coverage
	@rm -Rf coverage.xml
	@rm -Rf pytest-results.xml
	@rm -Rf pytest-coverage.txt
	@rm -Rf .eggs/
