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

##@ AWS

list: ## list
	@cdk list

synth: ## synthesize
	@cdk synth

deploy: ## deploy
	@cdk deploy

##@ Docker

build: ## build
	@docker build --platform linux/amd64 -t docker-image:test-aws .

run: ## run
	@docker run --platform linux/amd64 -p 9000:8080 docker-image:test-aws

test: ## test
	@curl "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{}'

tag: ## tag
	@docker tag docker-image:test-aws 642938752675.dkr.ecr.eu-central-1.amazonaws.com/aws-test-johannes-julia-private:latest

login: ## login to ecr (private)
	@aws ecr get-login-password --region eu-central-1 | docker login --username AWS --password-stdin 642938752675.dkr.ecr.eu-central-1.amazonaws.com

push: ## push
	@docker push 642938752675.dkr.ecr.eu-central-1.amazonaws.com/aws-test-johannes-julia-private

