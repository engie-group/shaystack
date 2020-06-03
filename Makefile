#!/usr/bin/env make -f
SHELL=/bin/bash
.SHELLFLAGS = -e -c
.ONESHELL:

ifeq ($(shell echo "$(shell echo $(MAKE_VERSION) | sed 's@^[^0-9]*\([0-9]\+\).*@\1@' ) >= 4" | bc -l),0)
$(error Bad make version, please install make >= 4)
endif

PRJ=carbonapi
PYTHON_SRC=$(PRJ)/*.py
PYTHON_VERSION:=3.7
PRJ_PACKAGE:=$(PRJ)
VENV ?= $(PRJ)
CONDA_BASE:=$(shell conda info --base)
CONDA_PACKAGE:=$(CONDA_PREFIX)/lib/python$(PYTHON_VERSION)/site-packages
CONDA_PYTHON:=$(CONDA_PREFIX)/bin/python
CONDA_ARGS?=
PIP_PACKAGE:=$(CONDA_PACKAGE)/$(PRJ_PACKAGE).egg-link
PIP_ARGS?=
ENVS_JSON?=envs.json

AWS_REGION?=eu-west-3
AWS_STACK=CarbonAPI
AWS_API_HOME=https://$(shell aws apigateway get-rest-apis --output text --query 'items[?name==`$(AWS_STACK)`].id').execute-api.$(AWS_REGION).amazonaws.com/Prod
ENVS_TEST?=NOCOMPRESS=True
# FIXME: remove local default profile ?
#export AWS_DEFAULT_PROFILE=engie

CHECK_VENV=@if [[ "base" == "$(CONDA_DEFAULT_ENV)" ]] || [[ -z "$(CONDA_DEFAULT_ENV)" ]] ; \
  then ( echo -e "$(green)Use: $(cyan)conda activate $(VENV)$(green) before using $(cyan)make$(normal)"; exit 1 ) ; fi

ACTIVATE_VENV=source $(CONDA_BASE)/etc/profile.d/conda.sh && conda activate $(VENV) $(CONDA_ARGS)
DEACTIVATE_VENV=source $(CONDA_BASE)/etc/profile.d/conda.sh && conda deactivate

VALIDATE_VENV=$(CHECK_VENV)

ifneq ($(TERM),)
normal:=$(shell tput sgr0)
bold:=$(shell tput bold)
red:=$(shell tput setaf 1)
green:=$(shell tput setaf 2)
yellow:=$(shell tput setaf 3)
blue:=$(shell tput setaf 4)
purple:=$(shell tput setaf 5)
cyan:=$(shell tput setaf 6)
white:=$(shell tput setaf 7)
gray:=$(shell tput setaf 8)
endif

.PHONY: help
.DEFAULT: help

## Print all majors target
help:
	@echo "$(bold)Available rules:$(normal)"
	@echo
	@sed -n -e "/^## / { \
		h; \
		s/.*//; \
		:doc" \
		-e "H; \
		n; \
		s/^## //; \
		t doc" \
		-e "s/:.*//; \
		G; \
		s/\\n## /---/; \
		s/\\n/ /g; \
		p; \
	}" ${MAKEFILE_LIST} \
	| LC_ALL='C' sort --ignore-case \
	| awk -F '---' \
		-v ncol=$$(tput cols) \
		-v indent=20 \
		-v col_on="$$(tput setaf 6)" \
		-v col_off="$$(tput sgr0)" \
	'{ \
		printf "%s%*s%s ", col_on, -indent, $$1, col_off; \
		n = split($$2, words, " "); \
		line_length = ncol - indent; \
		for (i = 1; i <= n; i++) { \
			line_length -= length(words[i]) + 1; \
			if (line_length <= 0) { \
				line_length = ncol - indent - length(words[i]) - 1; \
				printf "\n%*s ", -indent, " "; \
			} \
			printf "%s ", words[i]; \
		} \
		printf "\n"; \
	}' \
	| more $(shell test $(shell uname) = Darwin && echo '--no-init --raw-control-chars')

	echo -e "Use '$(cyan)make -jn ...$(normal)' for Parallel run"
	echo -e "Use '$(cyan)make -B ...$(normal)' to force the target"
	echo -e "Use '$(cyan)make -n ...$(normal)' to simulate the build"


.PHONY: dump-*
dump-%:
	@if [ "${${*}}" = "" ]; then
		echo "Environment variable $* is not set";
		exit 1;
	else
		echo "$*=${${*}}";
	fi


# -------------------------------------- GIT
.git/config: | .git .git/hooks/pre-push # Configure git
	@git config --local core.autocrlf input
	# Set tabulation to 4 when use 'git diff'
	@git config --local core.page 'less -x4'


# Rule to add a validation before pusing in master branch.
# Use FORCE=y git push to override this validation.
.git/hooks/pre-push: | .git
	@# Add a hook to validate the project before a git push
	cat >>.git/hooks/pre-push <<PRE-PUSH
	#!/usr/bin/env sh
	# Validate the project before a push
	if test -t 1; then
		ncolors=$$(tput colors)
		if test -n "\$$ncolors" && test \$$ncolors -ge 8; then
			normal="\$$(tput sgr0)"
			red="\$$(tput setaf 1)"
	        green="\$$(tput setaf 2)"
			yellow="\$$(tput setaf 3)"
		fi
	fi
	branch="\$$(git branch | grep \* | cut -d ' ' -f2)"
	if [ "\$${branch}" = "master" ] && [ "\$${FORCE}" != y ] ; then
		printf "\$${green}Validate the project before push the commit... (\$${yellow}make validate\$${green})\$${normal}\n"
		make validate
		ERR=\$$?
		if [ \$${ERR} -ne 0 ] ; then
			printf "\$${red}'\$${yellow}make validate\$${red}' failed before git push.\$${normal}\n"
			printf "Use \$${yellow}FORCE=y git push\$${normal} to force.\n"
			exit \$${ERR}
		fi
	fi
	PRE-PUSH
	chmod +x .git/hooks/pre-push

# -------------------------------------- Conda venv
.PHONY: configure
## Prepare the work environment (conda venv, ...)
configure:
	@if [[ "$(PRJ)" == "$(CONDA_DEFAULT_ENV)" ]] ; \
  		then echo -e "$(red)Use $(cyan)conda deactivate$(red) before using $(cyan)make configure$(normal)"; exit ; fi
	@conda create --name "$(VENV)" \
		python=$(PYTHON_VERSION) \
		-y $(CONDA_ARGS)
	echo -e "Use: $(cyan)conda activate $(VENV)$(normal) $(CONDA_ARGS)"

# All dependencies of the project must be here
.PHONY: requirements dependencies
REQUIREMENTS=$(PIP_PACKAGE) .git/config
requirements: $(REQUIREMENTS)
dependencies: requirements

# Rule to update the current venv, with the dependencies describe in `setup.py`
$(PIP_PACKAGE): $(CONDA_PYTHON) $(PRJ)/requirements.txt layer/requirements.txt | .git # Install pip dependencies
	@$(VALIDATE_VENV)
	echo -e "$(cyan)Install build dependencies ... (may take minutes)$(normal)"
	conda install -c conda-forge -c anaconda -y \
		awscli aws-sam-cli make \
		pytype ninja flake8 pylint pytest jq
	echo -e "$(cyan)Build dependencies updated$(normal)"
	echo -e "$(cyan)Install project dependencies ...$(normal)"
	pip install -r $(PRJ)/requirements.txt
	pip install -r layer/requirements.txt
	echo -e "$(cyan)Project dependencies updated$(normal)"
	@touch $(PIP_PACKAGE)

# All dependencies of the project must be here
.PHONY: requirements dependencies
requirements: $(REQUIREMENTS)
dependencies: requirements

remove-$(VENV):
	@$(DEACTIVATE_VENV)
	conda env remove --name "$(VENV)" -y 2>/dev/null
	echo -e "Use: $(cyan)conda deactivate$(normal)"
# Remove virtual environement
remove-venv : remove-$(VENV)

upgrade-$(VENV):
	@$(VALIDATE_VENV)
	conda update --all $(CONDA_ARGS)
	pip list --format freeze --outdated | sed 's/(.*//g' | xargs -r -n1 pip install $(EXTRA_INDEX) -U
	@echo -e "$(cyan)After validation, upgrade the setup.py$(normal)"

# Upgrade packages to last versions
upgrade-venv: upgrade-$(VENV)

# -------------------------------------- Clean
.PHONY: clean-pip
## Remove all the pip package
clean-pip:
	@pip freeze | grep -v "^-e" | grep -v "@" | xargs pip uninstall -y
	@echo -e "$(cyan)Virtual env cleaned$(normal)"

.PHONY: clean-venv clean-$(VENV)
clean-$(VENV): remove-venv
	@conda create -y -q -n $(VENV) $(CONDA_ARGS)
	@echo -e "$(yellow)Warning: Conda virtualenv $(VENV) is empty.$(normal)"
## Set the current VENV empty
clean-venv : clean-$(VENV)

## Clean project
clean: async-stop
	@rm -rf bin/* .aws-sam .mypy_cache .pytest_cache .start build nohup.out dist .make-* .pytype out.json

.PHONY: clean-all
# Clean all environments
clean-all: clean remove-venv


# -------------------------------------- Build
# Template to build custom runtime.
# See https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/building-custom-runtimes.html
# See https://github.com/awslabs/aws-sam-cli/blob/de8ad8e78491ebfa884c02c3439c6bcecd08516b/designs/build_for_layers.md
build-HSZincLayer:
	@if [[ -z "$(ARTIFACTS_DIR)" ]]
	then
		@$(VALIDATE_VENV)
		echo -e "$(green)Build Lambda HSZincLayer$(normal)"
		umask 0
		@sam build HSZincLayer
	else
		# executed inside `sam build`
		# The variable OLDPWD is set to the project home directory
		umask 0
		mkdir -p "$(ARTIFACTS_DIR)/python"
		python -m pip install $(OLDPWD)/hszinc/dist/hszinc-*.whl -t "$(ARTIFACTS_DIR)/python"
	fi

## build specific lambda function (ie. build-About)
build-%: template.yaml $(REQUIREMENTS) $(PYTHON_SRC) template.yaml
	@$(VALIDATE_VENV)
	echo -e "$(green)Build Lambda $*$(normal)"
	umask 0
	@sam build $*

.PHONY: dist build
.aws-sam/build: $(REQUIREMENTS) $(PYTHON_SRC) template.yaml
	@$(VALIDATE_VENV)
	echo -e "$(green)Build Lambdas$(normal)"
	umask 0
	@sam build

## build all lambda function
build: .aws-sam/build

# -------------------------------------- Invoke
.PHONY: invoke-*
## Build and invoke lamda function in local with associated events (ie. invoke-About)
invoke-%: $(ENVS_JSON) .aws-sam/build
	@$(VALIDATE_VENV)
	sam local invoke --env-vars $(ENVS_JSON) $* -e events/$*_event.json >out.json
	jq -r <out.json
	echo -e "\n$(green)Body:$(normal)"
	jq -r '.body' <out.json

.PHONY: start-api async-start-api async-stop-api
## Start api
start-api: $(ENVS_JSON) .aws-sam/build
	@$(VALIDATE_VENV)
	@[ -e .start/start-api.pid ] && $(MAKE) async-stop-api || true
	$(ENVS_TEST) sam local start-api --env-vars $(ENVS_JSON)

# Start local api emulator in background
async-start-api: $(ENVS_JSON) .aws-sam/build
	@$(VALIDATE_VENV)
	@[ -e .start/start-api.pid ] && echo -e "$(orange)Local API was allready started$(normal)" && exit
	mkdir -p .start
	$(ENVS_TEST) nohup sam local start-api --env-vars $(ENVS_JSON) >.start/start-api.log 2>&1 &
	echo $$! >.start/start-api.pid
	sleep 0.5
	tail .start/start-api.log
	echo -e "$(orange)Local API started$(normal)"

# Stop local api emulator in background
async-stop-api:
	@$(VALIDATE_VENV)
	@[ -e .start/start-api.pid ] && kill `cat .start/start-api.pid` && echo -e "$(green)Local API stopped$(normal)"
	rm -f .start/start-api.pid

.PHONY: api
## Print API URL
api:
	@grep -oh 'https://$${ServerlessRestApi}[^"]*' template.yaml | \
	sed 's/https:..$${ServerlessRestApi}.*\//http:\/\/locahost:3000\//g'

## Invoke local API (eg. make api-about)
api-%:
	curl -H "Accept: text/zinc" \
		"http://localhost:3000/$*"


.PHONY: start-lambda async-start-lambda async-stop-lambda
## Start lambda local emulator in background
start-lambda: $(ENVS_JSON) .aws-sam/build
	@$(VALIDATE_VENV)
	[ -e .start/start-lambda.pid ] && $(MAKE) async-stop-lambda || true
	$(ENVS_TEST) sam local start-lambda --env-vars $(ENVS_JSON)
	sleep 2

# Start lambda local emulator in background
async-start-lambda: $(ENVS_JSON) .aws-sam/build
	@$(VALIDATE_VENV)
	@[ -e .start/start-lambda.pid ] && echo -e "$(orange)Local Lambda was allready started$(normal)" && exit
	mkdir -p .start
	$(ENVS_TEST) nohup sam local start-lambda --env-vars $(ENVS_JSON) >.start/start-lambda.log 2>&1 &
	echo $$! >.start/start-lambda.pid
	sleep 0.5
	tail .start/start-lambda.log
	echo -e "$(orange)Local Lambda was started$(normal)"

# Stop lambda local emulator in background
async-stop-lambda:
	@$(VALIDATE_VENV)
	@[ -e .start/start-lambda.pid ] && kill `cat .start/start-lambda.pid` && echo -e "$(green)Local Lambda stopped$(normal)"
	rm -f .start/start-lambda.pid

## Stop all async server
async-stop: async-stop-api async-stop-lambda

# -------------------------------------- AWS
.PHONY: aws-clean-stack
## Remove AWS Stack
aws-clean-stack:
	aws cloudformation delete-stack --stack-name $(AWS_STACK) --region $(AWS_REGION)

##  Invoke lamda function via aws cli (ie. aws-invoke-About)
aws-invoke-%: .aws-sam/build
	$(VALIDATE_VENV)
	FUNCTION=$$(aws cloudformation describe-stack-resource --stack-name $(AWS_STACK) --logical-resource-id About --query 'StackResourceDetail.PhysicalResourceId' --output text)
	aws lambda invoke --function-name $$FUNCTION \
		--payload file://events/$*_event.json \
		out.json \
		--log-type Tail --query 'LogResult' --output text |  base64 -d
	jq -r <out.json
	echo -e "\n$(green)Body:$(normal)"
	jq -r '.body' <out.json

.PHONY: aws-api
## Print AWS API URL
aws-api:
	@grep -oh 'https://$${ServerlessRestApi}[^"]*' template.yaml | \
	sed 's/https:..$${ServerlessRestApi}.*\//$(subst  /,\/,$(AWS_API_HOME))\//g'

## Invoke API via AWS (eg. make aws-api-about)
aws-api-%:
	curl -H "Accept: text/zinc" \
		"$(AWS_API_HOME)/$*"

# -------------------------------------- Tests
.PHONY: unit-test
.make-unit-test: $(REQUIREMENTS) $(PYTHON_SRC) .aws-sam/build Makefile envs.json
	$(VALIDATE_VENV)
	PYTHONPATH=./$(PRJ) $(ENVS_TEST) python -m pytest -m "not functional" -s tests $(PYTEST_ARGS)
	date >.make-unit-test
## Run unit test
unit-test: .make-unit-test

.PHONY: functional-test
.make-functional-test: $(REQUIREMENTS) $(PYTHON_SRC) .aws-sam/build Makefile envs.json
	@$(VALIDATE_VENV)
	$(MAKE) async-start-lambda
	PYTHONPATH=./$(PRJ) $(ENVS_TEST) python -m pytest -m "functional" -s tests $(PYTEST_ARGS)
	date >.make-functional-test
## Run functional test
functional-test: .make-functional-test

.PHONY: test
.make-test: $(REQUIREMENTS) $(PYTHON_SRC) .aws-sam/build
	@$(VALIDATE_VENV)
	$(MAKE) async-start-lambda
	@PYTHONPATH=./$(PRJ) $(ENVS_TEST) python -m pytest -s tests $(PYTEST_ARGS)
	@date >.make-unit-test
	@date >.make-functional-test
	@date >.make-test

## Run all tests (unit and functional)
test: .make-test
	@date >.make-test


# -------------------------------------- hszinc
hszinc/dist: hszinc/hszinc/*.py
	cd hszinc
	python setup.py bdist_wheel

# -------------------------------------- Typing
pytype.cfg: $(CONDA_PREFIX)/bin/pytype
	@$(VALIDATE_VENV)
	@[[ ! -f pytype.cfg ]] && pytype --generate-config pytype.cfg || true
	touch pytype.cfg

.PHONY: typing
.make-typing: $(REQUIREMENTS) $(CONDA_PREFIX)/bin/pytype pytype.cfg $(PYTHON_SRC)
	$(VALIDATE_VENV)
	@echo -e "$(cyan)Check typing...$(normal)"
	# pytype
	pytype "$(PRJ)"
	touch ".pytype/pyi/$(PRJ)"
	touch .make-typing

## Check python typing
typing: .make-typing

# -------------------------------------- Lint
.PHONY: lint
.pylintrc:
	@$(VALIDATE_VENV)
	pylint --generate-rcfile > .pylintrc

.make-lint: $(REQUIREMENTS) $(PYTHON_SRC) | .pylintrc
	$(VALIDATE_VENV)
	@echo -e "$(cyan)Check lint...$(normal)"
	@echo "---------------------- FLAKE"
	@flake8 $(PRJ_PACKAGE)
	@echo "---------------------- PYLINT"
	@PYTHONPATH=./$(PRJ) pylint $(PRJ_PACKAGE)
	touch .make-lint

## Lint the code
lint: .make-lint


.PHONY: deploy
## Deploy lambda functions
deploy: .aws-sam/build
	@$(VALIDATE_VENV)
	sam deploy --region $(AWS_REGION) --parameter-overrides NOCOMPRESS=PPR
	echo -e "$(green)Lambdas are deployed$(normal)"

.PHONY: validate
.make-validate: .make-test .make-lint .aws-sam/build
	sam validate
	@date >.make-validate
## Validate the project
validate: .make-validate

.PHONY: release
## Release the project
release: clean .make-validate

# -------------------------------------- Submodule
submodule-update:
	git submodule update --remote --rebase

submodule-push:
	git push --recurse-submodules=on-demand

submodule-stash:
	git submodule foreach 'git stash'
# -------------------------------------- DEBUG
## Print logs of specific Lambda function
logs-%:
	sam logs -n $* --stack-name $(AWS_STACK) --tail

# TODO: Find how to use debugger
# See https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-using-debugging-python.html
debugging:
	@$(VALIDATE_VENV)
	# Install dependencies
	pip install -r $(PRJ)/requirements.txt -t build/
	pip install -r layer/requirements.txt -t build/
	# Install ptvsd library for step through debugging
	pip install ptvsd -t build/
	cp $(PRJ)/*.py build/
