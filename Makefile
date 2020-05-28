SHELL=/bin/bash
.SHELLFLAGS = -e -c
.ONESHELL:

ifeq ($(shell echo "$(shell echo $(MAKE_VERSION) | sed 's@^[^0-9]*\([0-9]\+\).*@\1@' ) >= 4" | bc -l),0)
$(error Bad make version, please install make >= 4)
endif

PRJ=carbonapi
PYTHON_SRC=$(PRJ)/*.py
PRJ_PACKAGE:=$(PRJ)
VENV ?= $(PRJ)
REQUIREMENTS=
CONDA_BASE:=$(shell conda info --base)
CONDA_PACKAGE:=$(CONDA_PREFIX)/lib/python$(PYTHON_VERSION)/site-packages
CONDA_PYTHON:=$(CONDA_PREFIX)/bin/python
CONDA_ARGS?=
PIP_PACKAGE:=$(CONDA_PACKAGE)/$(PRJ_PACKAGE).egg-link
PIP_ARGS?=
ENVS_JSON?=envs.json
ENVS_TEST?=
# FIXME

CHECK_VENV=@if [[ "base" == "$(CONDA_DEFAULT_ENV)" ]] || [[ -z "$(CONDA_DEFAULT_ENV)" ]] ; \
  then ( echo -e "$(green)Use: $(cyan)conda activate $(VENV)$(green) before using 'make'$(normal)"; exit 1 ) ; fi

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


# -------------------------------------- Conda venv
.PHONY: configure
## Prepare the work environment (conda venv, kernel, ...)
configure:
	@conda create --name "$(VENV)" python=$(PYTHON_VERSION) -y $(CONDA_ARGS)
	@if [[ "base" == "$(CONDA_DEFAULT_ENV)" ]] || [[ -z "$(CONDA_DEFAULT_ENV)" ]] ; \
	then echo -e "Use: $(cyan)conda activate $(VENV)$(normal) $(CONDA_ARGS)" ; fi

dependencies:
# TODO validate
	@$(VALIDATE_VENV)
	conda install -c conda-forge aws-sam-cli
	conda install -c conda-forge awscli
	pip install pylint pytype flake8

remove-$(VENV):
# TODO validate
	@$(DEACTIVATE_VENV)
	conda env remove --name "$(VENV)" -y 2>/dev/null
	echo -e "Use: $(cyan)conda deactivate$(normal)"
# Remove virtual environement
remove-venv : remove-$(VENV)

upgrade-$(VENV):
# TODO validate
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
# TODO validate
	@$(VALIDATE_VENV)
	pip freeze | grep -v "^-e" | xargs pip uninstall -y
	@echo -e "$(cyan)Virtual env cleaned$(normal)"

.PHONY: clean-venv clean-$(VENV)
clean-$(VENV): remove-venv
# TODO validate
	@conda create -y -q -n $(VENV) $(CONDA_ARGS)
	@echo -e "$(yellow)Warning: Conda virtualenv $(VENV) is empty.$(normal)"
# Set the current VENV empty
clean-venv : clean-$(VENV)

# Clean project
clean: async-stop
	@rm -rf bin/* .aws-sam .mypy_cache .pytest_cache .run build nohup.out dist .make-* .pytype

.PHONY: clean-all
# Clean all environments
clean-all: clean remove-venv


# -------------------------------------- Build
# Template to build custom runtime.
# See https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/building-custom-runtimes.html
#build-custom-runtime:
#	cp carbonapi/*.py $(ARTIFACTS_DIR)
#	cp carbonapi/requirements.txt $(ARTIFACTS_DIR)
#	python -m pip install -r carbonapi/requirements.txt -t $(ARTIFACTS_DIR)
#	rm -rf $(ARTIFACTS_DIR)/bin

## build specific lambda function (ie. build-About)
build-%: template.yaml $(PYTHON_SRC) template.yaml
	@sam build $*
	chmod -R o+rwx .aws-sam

.PHONY: dist build
.aws-sam/build: $(PYTHON_SRC) template.yaml
	@sam build
	chmod -R o+rwx .aws-sam

## build all lambda function
build: .aws-sam/build

# -------------------------------------- Invoke
.PHONY: invoke-*
## Build and invoke lamda function in local with associated events (ie. invoke-About)
invoke-%: $(ENVS_JSON)
	$(MAKE) build-$*
	sam local invoke --env-vars $(ENVS_JSON) $* -e events/$*_event.json

## Build and invoke lamda function via aws cli (ie. invoke-About)
aws-invoke-%:
	$(MAKE) build-$*
	aws lambda invoke --function-name %* out.json --log-type Tail --query 'LogResult' --output text |  base64 -d

.PHONY: start-api async-start-api async-stop-api
## Start api
start-api: $(ENVS_JSON) build
	@[ -e .run/start-api.pid ] && $(MAKE) async-stop-api || true
	$(ENVS_TEST) sam local start-api --env-vars $(ENVS_JSON)

# Start local api emulator in background
async-start-api: $(ENVS_JSON) $(PYTHON_SRC)
	@[ -e .run/start-api.pid ] && echo -e "$(orange)Local API was allready started$(normal)" && exit
	mkdir -p .run
	$(ENVS_TEST) nohup sam local start-api --env-vars $(ENVS_JSON) >.run/start-api.log 2>&1 &
	echo $$! >.run/start-api.pid
	sleep 0.5
	tail .run/start-api.log
	echo -e "$(orange)Local API started$(normal)"

# Stop local api emulator in background
async-stop-api:
	@[ -e .run/start-api.pid ] && kill `cat .run/start-api.pid` && echo -e "$(green)API stopped$(normal)"
	rm -f .run/start-api.pid

.PHONY: start-lambda async-start-lambda async-stop-lambda
## Start lambda local emulator in background
start-lambda: $(ENVS_JSON) build
	[ -e .run/start-lambda.pid ] && $(MAKE) async-stop-lambda || true
	$(ENVS_TEST) sam local start-lambda --env-vars $(ENVS_JSON)

# Start lambda local emulator in background
async-start-lambda: $(ENVS_JSON) $(PYTHON_SRC)
	@[ -e .run/start-lambda.pid ] && echo -e "$(orange)Local Lambda was allready started$(normal)" && exit
	mkdir -p .run
	$(ENVS_TEST) nohup sam local start-lambda --env-vars $(ENVS_JSON) >.run/start-lambda.log 2>&1 &
	echo $$! >.run/start-lambda.pid
	sleep 0.5
	tail .run/start-lambda.log
	echo -e "$(orange)Local Lambda was started$(normal)"

# Stop lambda local emulator in background
async-stop-lambda:
	@[ -e .run/start-lambda.pid ] && kill `cat .run/start-lambda.pid` && echo -e "$(green)Local Lambda stopped$(normal)"
	rm -f .run/start-lambda.pid

## Stop all async server
async-stop: async-stop-api async-stop-lambda

# -------------------------------------- Tests
.PHONY: unit-test
.make-unit-test: $(PYTHON_SRC) .aws-sam/build Makefile envs.json
	$(VALIDATE_VENV)
	PYTHONPATH=./carbonapi $(ENVS_TEST) python -m pytest -m "not functional" -s tests $(PYTEST_ARGS)
	date >.make-unit-test
## Run unit test
unit-test: .make-unit-test

.PHONY: functional-test
.make-functional-test: $(PYTHON_SRC) .aws-sam/build Makefile envs.json
	@$(VALIDATE_VENV)
	$(MAKE) async-start-lambda
	PYTHONPATH=./carbonapi $(ENVS_TEST) python -m pytest -m "functional" -s tests $(PYTEST_ARGS)
	date >.make-functional-test
## Run functional test
functional-test: .make-functional-test

.PHONY: test
.make-test: $(PYTHON_SRC) .aws-sam/build
	@$(VALIDATE_VENV)
	$(MAKE) async-start-lambda
	@PYTHONPATH=./carbonapi python -m pytest -s tests $(PYTEST_ARGS)
	@date >.make-unit-test
	@date >.make-functional-test
	@date >.make-test

## Run all tests (unit and functional)
test: .make-test
	@date >.make-test


# -------------------------------------- Typing
# FIXME
pytype.cfg: $(CONDA_PREFIX)/bin/pytype
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
	pylint --generate-rcfile > .pylintrc

.make-lint: $(REQUIREMENTS) $(PYTHON_SRC) | .pylintrc
	$(VALIDATE_VENV)
	@echo -e "$(cyan)Check lint...$(normal)"
	@echo "---------------------- FLAKE"
	@flake8 $(PRJ_PACKAGE)
	@echo "---------------------- PYLINT"
	@pylint $(PRJ_PACKAGE)
	touch .make-lint

## Lint the code
lint: .make-lint

# -------------------------------------- Packages
dist/carbonapi.zip: carbonapi/*
	@mkdir -p dist/package
# TODO: Add package from TOUL ?
	# pip install --target ./dist/package Pillow
	cd dist/package
	zip -r9 ../carbonapi.zip . -i .
	cd ../..
	zip -g dist/carbonapi.zip carbonapi/*.py

.PHONY: dist
## Build distribution
dist: dist/carbonapi.zip validate

.PHONY: deploy
# TODO : valide see https://docs.aws.amazon.com/lambda/latest/dg/python-package.html
## Deploy lambda functions
deploy: dist/carbonapi.zip
	aws lambda update-function-code --function-name About --zip-file fileb://dist/carbonapi.zip
	aws lambda update-function-code --function-name ExtendWithCO2e --zip-file fileb://dist/carbonapi.zip

.PHONY: validate
## Validate the project
validate: .make-test .make-lint dist/carbonapi.zip

.PHONY: release
## Release the project
release: clean dist

# -------------------------------------- TODO
# TODO: Find how to use debugger
# See https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-using-debugging-python.html
debugging:
	# Install dependencies
	pip install -r carbonapi/requirements.txt -t build/
	# Install ptvsd library for step through debugging
	pip install ptvsd -t build/
	cp carbonapi/*.py build/

# -------------------------------------- Source
carbonapi/haystackapi.py: carbonapi/lambda_types.py
