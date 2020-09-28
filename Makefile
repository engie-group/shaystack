#!/usr/bin/env make -f
SHELL=/bin/bash
.SHELLFLAGS = -e -c
.ONESHELL:

ifeq ($(ARTIFACTS_DIR),)
ifeq ($(shell echo "$(shell echo $(MAKE_VERSION) | sed 's@^[^0-9]*\([0-9]\+\).*@\1@' ) >= 4" | bc -l),0)
$(error Bad make version, please install make >= 4 ($(MAKE_VERSION)))
endif
endif

include ./Project.variables
# Override project variables
ifneq (,$(wildcard .env))
include .env
endif

# TODO: tester sans le .env !

# Export all project variables
export PRJ
export HAYSTACK_PROVIDER
export HAYSTACK_URL
export AWS_STACK
export AWS_PROFILE
export AWS_REGION
export AWS_S3_ENDPOINT
export PYTHON_VERSION
export LOGLEVEL
export PARAMS
export SAM_CLI_TELEMETRY

PYTHON_SRC=src/*.py src/providers/*.py
PYTHON_VERSION:=3.8
PRJ_PACKAGE:=$(PRJ)
VENV ?= $(PRJ)
CONDA_BASE:=$(shell AWS_PROFILE=default conda info --base)
CONDA_PACKAGE:=$(CONDA_PREFIX)/lib/python$(PYTHON_VERSION)/site-packages
CONDA_PYTHON:=$(CONDA_PREFIX)/bin/python
CONDA_ARGS?=

PIP_PACKAGE:=$(CONDA_PACKAGE)/$(PRJ_PACKAGE).egg-link

AWS_REGION?=us-east-2
AWS_STAGE?=dev
AWS_API_HOME=$(shell zappa status $(AWS_STAGE) --json | jq -r '."API Gateway URL"')

# For minio
AWS_S3_ENDPOINT?=https://s3.$(AWS_REGION).amazonaws.com
AWS_ACCESS_KEY=$(shell aws configure get aws_access_key_id)
AWS_SECRET_KEY=$(shell aws configure get aws_secret_access_key)

FLASK_DEBUG?=1
export FLASK_DEBUG
MINIO_HOME=$(HOME)/.minio
GIMME?=gimme-aws-creds

ZAPPA_ENV=zappa_venv

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
# Tools to dump makefile variable (make dump-AWS_API_HOME)
dump-%:
	@if [ "${${*}}" = "" ]; then
		echo "Environment variable $* is not set";
		exit 1;
	else
		echo "$*=${${*}}";
	fi

## Print project variables
dump-params:
	@echo PRJ=$(PRJ)
	echo HAYSTACK_PROVIDER=$(HAYSTACK_PROVIDER)
	echo HAYSTACK_URL=$(HAYSTACK_URL)
	echo AWS_PROFILE=$(AWS_PROFILE)
	echo AWS_REGION=$(AWS_REGION)
	echo AWS_STAGE=$(AWS_STAGE)

# -------------------------------------- GIT
.git/config: | .git .git/hooks/pre-push # Configure git
	@git config --local core.autocrlf input
	# Set tabulation to 4 when use 'git diff'
	@git config --local core.page 'less -x4'

# Rule to add a validation before pushing in master branch.
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

# -------------------------------------- Virtualenv
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
$(PIP_PACKAGE): $(CONDA_PYTHON) | .git # Install pip dependencies
	@$(VALIDATE_VENV)
	echo -e "$(cyan)Install build dependencies ... (may take minutes)$(normal)"
ifeq ($(USE_OKTA),Y)
	pip install gimme-aws-creds
endif
	conda install -c conda-forge -c anaconda -y \
		make jq
	echo -e "$(cyan)Install project dependencies ...$(normal)"
	pip install -e .
	pip install file://$$(pwd)#egg=foo[dev]
	pip install file://$$(pwd)#egg=foo[lambda]
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


# clean-zappa
clean-zappa:
	@rm -fr handler_venv $(ZAPPA_ENV) $(PRJ)-$(AWS_STAGE)-*.* handler_$(PRJ)-$(AWS_STAGE)*.zip

## Clean project
clean: async-stop clean-zappa
	@rm -rf bin/* .mypy_cache .pytest_cache .start build nohup.out dist .make-* .pytype out.json

.PHONY: clean-all
# Clean all environments
clean-all: clean remove-venv


# -------------------------------------- Build

.PHONY: dist build compile-all

# Compile all python files
compile-all:
	@echo -e "$(cyan)Compile all python file...$(normal)"
	# FIXME python -m compileall

# -------------------------------------- API
.PHONY: api
## Print API URL
api:
	@echo http://localhost:3000/haystack

.PHONY: api-*
## Invoke local API (eg. make api-about)
api-%:
	@$(VALIDATE_VENV)
	TARGET="localhost:3000"
	curl -H "Accept: text/zinc" \
			"$${TARGET}/haystack/$*"

api-read:
	#$(VALIDATE_VENV)
	TARGET="localhost:3000"
	curl -H "Accept: text/zinc" \
			"$${TARGET}/haystack/read?filter=point&limit=5"

api-hisRead:
	@$(VALIDATE_VENV)
	TARGET="localhost:3000"
	curl -H "Accept: text/zinc" \
			"$${TARGET}/haystack/hisRead$(URL_PARAMS)"

.PHONY: start-api async-start-api async-stop-api
## Start api
start-api: $(REQUIREMENTS)
	@$(VALIDATE_VENV)
	@[ -e .start/start-api.pid ] && $(MAKE) async-stop-api || true
	FLASK_DEBUG=1 FLASK_ENV=$(AWS_STAGE) \
	python -m app.__init__

# Start local api in background
async-start-api: $(REQUIREMENTS)
	@$(VALIDATE_VENV)
	@[ -e .start/start-api.pid ] && echo -e "$(orange)Local API was allready started$(normal)" && exit
	mkdir -p .start
	nohup 	FLASK_DEBUG=1 FLASK_APP=app.run FLASK_ENV=$(AWS_STAGE) \
	flask run >.start/start-api.log 2>&1 &
	echo $$! >.start/start-api.pid
	sleep 0.5
	tail .start/start-api.log
	echo -e "$(orange)Local API started$(normal)"

# Stop local api emulator in background
async-stop-api:
	@$(VALIDATE_VENV)
	@[ -e .start/start-api.pid ] && kill `cat .start/start-api.pid` || true && echo -e "$(green)Local API stopped$(normal)"
	rm -f .start/start-api.pid


# -------------------------------------- Minio
# https://min.io/
# See https://docs.min.io/docs/how-to-use-aws-sdk-for-python-with-minio-server.html
.minio:
	mkdir -p .minio

start-minio: .minio $(REQUIREMENTS)
	docker run -p 9000:9000 \
	-e "MINIO_ACCESS_KEY=$(AWS_ACCESS_KEY)" \
	-e "MINIO_SECRET_KEY=$(AWS_SECRET_KEY)" \
	-v  "$(MINIO_HOME):/data" \
	minio/minio server /data

async-stop-minio:
	@$(VALIDATE_VENV)
	[ -e .start/start-minio.pid ] && kill `cat .start/start-minio.pid` >/dev/null || true && echo -e "$(green)Local Minio stopped$(normal)"
	rm -f .start/start-minio.pid

async-start-minio: .minio $(REQUIREMENTS)
	@$(VALIDATE_VENV)
	[ -e .start/start-minio.pid ] && echo -e "$(orange)Local Minio was allready started$(normal)" && exit
	mkdir -p .start
	nohup  docker run -p 9000:9000 \
	--name minio_$(PRJ) \
	-e "MINIO_ACCESS_KEY=$(AWS_ACCESS_KEY)" \
	-e "MINIO_SECRET_KEY=$(AWS_SECRET_KEY)" \
	-v  "$(MINIO_HOME):/data" \
	minio/minio server /data >.start/start-minio.log 2>&1 &
	echo $$! >.start/start-minio.pid
	sleep 2
	tail .start/start-minio.log
	echo -e "$(orange)Local Minio was started$(normal)"


## Stop all async server
async-stop: async-stop-api async-stop-minio

# -------------------------------------- AWS
ifeq ($(USE_OKTA),Y)
.PHONY: aws-update-token
# Update the AWS Token
aws-update-token:
	@echo -e "$(green)Use AWS profile '$(AWS_PROFILE)$(normal)'"
	@aws sts get-caller-identity >/dev/null 2>/dev/null || $(subst $\",,$(GIMME)) --profile $(AWS_PROFILE)
else
aws-update-token:
	# Nothing
endif

.PHONY: aws-package aws-deploy aws-update aws-undeploy

# Install a clean venv before invoking zappa
_zappa_pre_install: clean-zappa
	@virtualenv $(ZAPPA_ENV)
	source $(ZAPPA_ENV)/bin/activate
	# FIXME: injection des paramètres
	pip install .
	# Install extra
	pip install "file://$$(pwd)#egg=foo[lambda]"
	# Install submodule
	pip install -e hszinc

## Build lambda package
aws-package: $(REQUIREMENTS) _zappa_pre_install compile-all
	echo -e "$(cyan)Create lambda package...$(normal)"
	source $(ZAPPA_ENV)/bin/activate
	zappa package $(AWS_STAGE)
	rm -Rf $(ZAPPA_ENV)


## Deploy lambda functions
aws-deploy: $(REQUIREMENTS) _zappa_pre_install compile-all
	$(VALIDATE_VENV)
ifeq ($(USE_OKTA),Y)
	$(subst $\",,$(GIMME)) --profile $(AWS_PROFILE)
endif
	source $(ZAPPA_ENV)/bin/activate
	zappa deploy $(AWS_STAGE)
	rm -Rf $(ZAPPA_ENV)
	echo -e "$(green)Lambdas are deployed$(normal)"

## Update lambda functions
aws-update: $(REQUIREMENTS) _zappa_pre_install compile-all
	@$(VALIDATE_VENV)
ifeq ($(USE_OKTA),Y)
	$(subst $\",,$(GIMME)) --profile $(AWS_PROFILE)
endif
	source $(ZAPPA_ENV)/bin/activate
	zappa update $(AWS_STAGE)
	rm -Rf $(ZAPPA_ENV)
	echo -e "$(green)Lambdas are updated$(normal)"

## Remove AWS Stack
aws-undeploy: $(REQUIREMENTS)
	zappa undeploy $(AWS_STAGE) --remove-logs

.PHONY: aws-api
## Print AWS API URL
aws-api:
	@echo $(AWS_API_HOME)

## Invoke API via AWS (eg. make aws-api-About)
.PHONY: aws-api-*
## Call AWS api (ie. aws-api-about)
aws-api-%:
	@$(VALIDATE_VENV)
	TARGET="$(AWS_API_HOME)"
	curl -H "Accept: text/zinc" \
			"$${TARGET}/haystack/$*"

aws-api-read:
	$(VALIDATE_VENV)
	TARGET="$(AWS_API_HOME)"
	curl -H "Accept: text/zinc" \
			"$${TARGET}/haystack/read?filter=point&limit=5"

aws-api-hisRead:
	@$(VALIDATE_VENV)
	TARGET="$(AWS_API_HOME)"
	curl -H "Accept: text/zinc" \
			"$${TARGET}/haystack/hisRead$(URL_PARAMS)"

## Print AWS logs
aws-logs:
	@$(VALIDATE_VENV)
	zappa tail

# -------------------------------------- Tests
.PHONY: unit-test
.make-unit-test: $(REQUIREMENTS) $(PYTHON_SRC) Makefile .env
	@$(VALIDATE_VENV)
	PYTHONPATH=./src python -m pytest -m "not functional" -s tests $(PYTEST_ARGS)
	date >.make-unit-test
## Run unit test
unit-test: .make-unit-test

.PHONY: functional-test
.make-functional-test: $(REQUIREMENTS) $(PYTHON_SRC) .aws-sam/build Makefile tests/data
	@$(VALIDATE_VENV)
	$(MAKE) async-start-lambda
	PYTHONPATH=./src python -m pytest -m "functional" -s tests $(PYTEST_ARGS)
	date >.make-functional-test
## Run functional test
functional-test: .make-functional-test

.PHONY: test
.make-test: $(REQUIREMENTS) $(PYTHON_SRC) .aws-sam/build
	@$(VALIDATE_VENV)
	$(MAKE) async-start-lambda
	@PYTHONPATH=./src python -m pytest -s tests $(PYTEST_ARGS)
	@date >.make-unit-test
	@date >.make-functional-test
	@date >.make-test

## Run all tests (unit and functional)
test: .make-test
	@date >.make-test


# -------------------------------------- hszinc
hszinc/dist/hszinc-*.whl: hszinc/hszinc/*.py
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
	pytype -P src -V $(PYTHON_VERSION) src
	touch .make-typing

## Check python typing
typing: .make-typing

# -------------------------------------- Lint
.PHONY: lint
.pylintrc:
	@$(VALIDATE_VENV)
	pylint --generate-rcfile > .pylintrc

.make-lint: $(REQUIREMENTS) $(PYTHON_SRC) tests/*.py | .pylintrc
	$(VALIDATE_VENV)
	@echo -e "$(cyan)Check lint...$(normal)"
	@echo "---------------------- FLAKE"
	@flake8 src
	@echo "---------------------- PYLINT"
	@PYTHONPATH=./src pylint src
	touch .make-lint

## Lint the code
lint: .make-lint


.PHONY: validate
.make-validate: build .make-typing .make-lint .make-test
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
