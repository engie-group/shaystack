#!/usr/bin/env make
SHELL=/bin/bash
.SHELLFLAGS = -e -c
.ONESHELL:
MAKEFLAGS += --no-print-directory

ifeq ($(shell [[ ( $(shell echo $(MAKE_VERSION) | cut -f1 -d.) -ge 4) ]] || echo 1),1)
$(error "Unsupported Make version. The build system does not work properly\
with GNU Make $(MAKE_VERSION),please use GNU Make 4 or above.")
endif

# You can change the password in .env
PRJ?=shaystack
HAYSTACK_PROVIDER?=shaystack.providers.db
HAYSTACK_DB?=sample/carytown.zinc
REFRESH=15
USE_OKTA?=N
AWS_PROFILE?=default
AWS_REGION?=eu-west-3
AWS_CLUSTER_NAME=haystack
AWS_STAGE?=$(STAGE)
LOGLEVEL?=WARNING
PG_PASSWORD?=password
PGADMIN_USER?=$(USER)@domain.com
PGADMIN_PASSWORD?=password
MYSQL_USER?=mysql
MYSQL_PASSWORD?=password
MONGO_USER?=mongo
MONGO_PASSWORD?=password
TLS_VERIFY=False
TERM?=dumb

# Default parameter for make [aws-]api-read
READ_PARAMS?=?filter=his&limit=5
# Default parameter for make [aws-]api-hisRead
HISREAD_PARAMS?=?id=@id1

# Override project variables
ifneq (,$(wildcard .env))
include .env
endif


PYTHON_SRC=$(shell find . -name '*.py')
PYTHON_VERSION?=3.8
PRJ_PACKAGE:=$(PRJ)
VENV ?= $(PRJ)
CONDA ?=conda
CONDA_PYTHON_EXE?=/opt/conda/bin/conda
CONDA_EXE?=$(shell which conda)
CONDA_BASE:=$(shell $(CONDA_EXE) info --base || '/opt/conda')
CONDA_PACKAGE:=$(CONDA_PREFIX)/lib/python$(PYTHON_VERSION)/site-packages
CONDA_PYTHON:=$(CONDA_PREFIX)/bin/python
CONDA_ARGS?=
GIT_CLONE_URL=$(shell git remote get-url origin)
FLASK_DEBUG?=1
STAGE=dev
AWS_STAGE?=$(STAGE)
ZAPPA_ENV=zappa_venv
DOCKER_REPOSITORY=$(USER)
PORT?=3000
INPUT_NETWORK?=localhost
HOST_API?=localhost
COOKIE_SECRET_KEY?=2d1a12a6-3232-4328-9365-b5b65e64a68f
TWINE_USERNAME?=__token__
SIGN_IDENTITY?=$(USER)
URL_PREFIX=

PIP_PACKAGE:=$(CONDA_PACKAGE)/$(PRJ_PACKAGE).egg-link

AWS_API_HOME=$(shell zappa status $(AWS_STAGE) --json | jq -r '."API Gateway URL"')

# For minio
MINIO_HOME=$(HOME)/.minio
AWS_ACCESS_KEY=$(shell aws configure --profile $(AWS_PROFILE) get aws_access_key_id)
AWS_SECRET_KEY=$(shell aws configure --profile $(AWS_PROFILE) get aws_secret_access_key)

# Export all project variables
export PRJ
export HAYSTACK_PROVIDER
export HAYSTACK_DB
export LOGLEVEL
export AWS_PROFILE
export AWS_REGION
export PYTHON_VERSION
export READ_PARAMS
export HISREAD_PARAMS
export FLASK_DEBUG
export COOKIE_SECRET_KEY
export PYTHON_VERSION
export TLS_VERIFY
export TWINE_USERNAME

# Calculate the make extended parameter
# Keep only the unknown target
#ARGS = `ARGS="$(filter-out $@,$(MAKECMDGOALS))" && echo $${ARGS:-${1}}`
# Hack to ignore unknown target. May be used to calculate parameters
#%:
#	@:

define BROWSER
	python -c '
	import os, sys, webbrowser
	from urllib.request import pathname2url

	webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])), autoraise=True)
	sys.exit(0)
	'
endef

CHECK_VENV=if [[ $(VENV) != "$(CONDA_DEFAULT_ENV)" ]] ; \
  then ( echo -e "$(green)Use: $(cyan)conda activate $(VENV)$(green) before using $(cyan)make$(normal)"; exit 1 ) ; fi

ACTIVATE_VENV=source $(CONDA_BASE)/etc/profile.d/conda.sh && conda activate $(VENV) $(CONDA_ARGS)
DEACTIVATE_VENV=source $(CONDA_BASE)/etc/profile.d/conda.sh && conda deactivate

VALIDATE_VENV?=$(CHECK_VENV)

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
	echo
	sed -n -e "/^## / { \
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


# --------------------------- Info
## Print all URL
info: api url-pg aws-api

conda-info:
	conda info


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
	@echo -e "$(green)HAYSTACK_PROVIDER=$(HAYSTACK_PROVIDER)$(normal)"
	echo -e "$(green)HAYSTACK_DB=$(HAYSTACK_DB)$(normal)"
	echo -e "$(green)AWS_PROFILE=$(AWS_PROFILE)$(normal)"
	echo -e "$(green)STAGE=$(STAGE)$(normal)"
	echo -e "$(green)PORT=$(PORT)$(normal)"
	echo -e "$(green)PIP_INDEX_URL=$(PIP_INDEX_URL)$(normal)"
	echo -e "$(green)PIP_EXTRA_INDEX_URL=$(PIP_EXTRA_INDEX_URL)$(normal)"
	echo -e "$(green)READ_PARAMS=$${READ_PARAMS}$(normal)"
	echo -e "$(green)HISREAD_PARAMS=$${HISREAD_PARAMS}$(normal)"

.PHONY: shell bash env
# Start a child shell
shell bash zsh:
	@$(SHELL)

env:
	env

# -------------------------------------- GIT
.env:
	@touch .env

.git/config: | .git .git/hooks/pre-push # Configure git
	@git config --local core.autocrlf input
	# Set tabulation to 4 when use 'git diff'
	git config --local core.page 'less -x4'
	git config --local push.followTags true

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
	if [ "\$${branch}" = "master" ] || [[ "\$${branch}" = release/* ]] && [ "\$${FORCE}" != y ] ; then
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

fetch:
	@git fetch

pull:
	@git pull

## Push the source code to git and the tag simultaneously
push:
	@git push --atomic origin develop $(shell git describe --tag)

# -------------------------------------- Initialize Virtual env
.PHONY: configure _configure _check_configure

## Prepare the working environment (conda venv, ...)
configure: _check_configure _configure

_check_configure:
	@if [[ "$(CONDA_DEFAULT_ENV)" != "" && "$(CONDA_DEFAULT_ENV)" != "base" ]] ; \
		then echo -e "$(red)Use $(cyan)conda deactivate$(red) before using $(cyan)make configure$(normal)"; exit ; fi

# Configure with the check. Use to be called inside a docker, with a mapping /opt/conda
# to create an environment via the docker.
_configure:
	@if [[ "$(VENV)" != "base" ]]
	then
		$(CONDA_EXE) create --name "$(VENV)" -c conda-forge python=$(PYTHON_VERSION) -y $(CONDA_ARGS)
		echo -e "Use: $(cyan)conda activate $(VENV)$(normal) $(CONDA_ARGS)"
	else
		$(CONDA_EXE) install -c conda-forge python=$(PYTHON_VERSION) -y $(CONDA_ARGS)
	fi

# -------------------------------------- Standard requirements
# Rule to update the current venv, with the dependencies describe in `setup.py`
$(PIP_PACKAGE): $(CONDA_PYTHON) setup.* requirements.txt | .git # Install pip dependencies
	@$(VALIDATE_VENV)
	echo -e "$(cyan)Install build dependencies ... (may take minutes)$(normal)"
ifeq ($(USE_OKTA),Y)
	pip install gimme-aws-creds
endif
	echo -e "$(cyan)Install binary dependencies ...$(normal)"
	conda install -y -c conda-forge conda setuptools make git jq libpq curl psycopg2 md-toc
	echo -e "$(cyan)Install project dependencies ...$(normal)"
	pip install supersqlite
	echo -e "$(cyan)pip install -e .[dev,flask,graphql,lambda]$(normal)"
	pip install -e '.[dev,flask,graphql,lambda]'
	echo -e "$(cyan)pip install -e .$(normal)"
	pip install -e .
	touch $(PIP_PACKAGE)

# All dependencies of the project must be here
.PHONY: requirements dependencies
REQUIREMENTS=$(PIP_PACKAGE) .git/config
requirements: $(REQUIREMENTS)
dependencies: requirements

# Remove the current conda environment
remove-venv remove-$(VENV):
	@$(DEACTIVATE_VENV)
	conda env remove --name "$(VENV)" -y 2>/dev/null
	echo -e "Use: $(cyan)conda deactivate$(normal)"

# Upgrade packages to last versions
upgrade-venv upgrade-$(VENV):
	@$(VALIDATE_VENV)
	conda update --all $(CONDA_ARGS)
	pip list --format freeze --outdated | sed 's/(.*//g' | xargs -r -n1 pip install $(EXTRA_INDEX) -U
	echo -e "$(cyan)After validation, upgrade the setup.py$(normal)"

# -------------------------------------- Clean
.PHONY: clean-pip
# Remove all the pip package
clean-pip:
	@pip freeze | grep -v "^-e" | grep -v "@" | xargs pip uninstall -y
	echo -e "$(cyan)Virtual env cleaned$(normal)"

.PHONY: clean-venv clean-$(VENV)
# Clean venv
clean-$(VENV): remove-venv
	@conda create -y -q -n $(VENV) $(CONDA_ARGS)
	echo -e "$(yellow)Warning: Conda virtualenv $(VENV) is empty.$(normal)"
## Clean the environment (Remove all components)
clean-venv : clean-$(VENV)

# clean-zappa
clean-zappa:
	@rm -fr handler_venv $(ZAPPA_ENV) $(PRJ)-$(AWS_STAGE)-*.* handler_$(PRJ)-$(AWS_STAGE)*.zip

## Clean project
clean: async-stop clean-zappa
	@rm -rf bin/* .eggs shaystack.egg-info .ipynb_checkpoints .mypy_cache .pytest_cache .start build nohup.out dist \
		.make-* .pytype out.json test.db zappa_settings.json ChangeLog
	mkdir dist/

.PHONY: clean-all
# Clean all environments
clean-all: clean docker-rm docker-rm-dmake remove-venv

# -------------------------------------- Build
.PHONY: dist build compile-all api api-read api-hisRead

# Compile all python files
compile-all:
	@$(VALIDATE_VENV)
	@echo -e "$(cyan)Compile all python file...$(normal)"
	$(CONDA_PYTHON) -m compileall

# -------------------------------------- Docs
.PHONY: docs docs-tm

docs/api: $(REQUIREMENTS)
	@$(VALIDATE_VENV)
	pdoc -f --html -o docs/api shaystack app

docs-tm: docs/index.md docs/contributing.md docs/AWS.md docs/AppSync.md
	md_toc -p github $?

## Generate the API HTML documentation
docs: docs/api docs-tm docs/*
	@touch docs

## Start the pdoc server to update the docstrings
start-docs:
	@$(VALIDATE_VENV)
	pdoc --http : -f --html -o docs/api shaystack app

# -------------------------------------- Client API
.PHONY: api
## Print API endpoint URL
api:
	@echo http://$(HOST_API):$(PORT)/haystack

.PHONY: api-*
## Invoke local API (eg. make api-about)
api-%:
	@TARGET="$(HOST_API):$(PORT)"
	curl -H "Accept: text/zinc" \
			"$${TARGET}/haystack/$*"

api-read:
	@echo -e "Use $(yellow)READ_PARAMS=$(READ_PARAMS)$(normal)"
	TARGET="$(HOST_API):$(PORT)"
	curl -H "Accept: text/zinc" \
			"$${TARGET}/haystack/read$(READ_PARAMS)"

api-hisRead:
	@echo -e "Use $(yellow)HISREAD_PARAMS=$(HISREAD_PARAMS)$(normal)"
	TARGET="$(HOST_API):$(PORT)"
	curl -H "Accept: text/zinc" \
			"$${TARGET}/haystack/hisRead$(HISREAD_PARAMS)"

# -------------------------------------- Server API
.PHONY: start-api async-start-api async-stop-api
## Start api
start-api: $(REQUIREMENTS)
	@$(VALIDATE_VENV)
	[ -e .start/start-api.pid ] && $(MAKE) async-stop-api || true
	echo -e "$(green)PROVIDER=$${HAYSTACK_PROVIDER}"
	echo -e "$(green)DB=$${HAYSTACK_DB}"
	echo -e "$(green)TS=$${HAYSTACK_TS}"
	echo -e "$(green)Use http://$(HOST_API):$(PORT)/graphql or http://$(HOST_API):$(PORT)/haystack$(normal)"
	FLASK_DEBUG=1 FLASK_ENV=$(STAGE) \
	URL_PREFIX=$(URL_PREFIX) $(CONDA_PYTHON) -m app.main --port $(PORT) --host $(INPUT_NETWORK)

# Start local API server in background
async-start-api: $(REQUIREMENTS)
	@$(VALIDATE_VENV)
	[ -e .start/start-api.pid ] && echo -e "$(yellow)Local API was allready started$(normal)" && exit
	mkdir -p .start
	FLASK_DEBUG=1 FLASK_APP=app.run FLASK_ENV=$(STAGE) \
	nohup $(CONDA_PYTHON) -m app.main --port $(PORT) >.start/start-api.log 2>&1 &
	echo $$! >.start/start-api.pid
	sleep 1
	tail .start/start-api.log
	echo -e "$(yellow)Local API started$(normal)"
	echo -e "$(green)PROVIDER=$${HAYSTACK_PROVIDER}"
	echo -e "$(green)DB=$${HAYSTACK_DB}"
	echo -e "$(green)TS=$${HAYSTACK_TS}"
	echo -e "$(green)Use http://$(HOST_API):$(PORT)/graphql or http://$(HOST_API):$(PORT)/haystack$(normal)"

# Stop the background local API server
async-stop-api:
	@$(VALIDATE_VENV)
	[ -e .start/start-api.pid ] && kill `cat .start/start-api.pid` 2>/dev/null >/dev/null || true && echo -e "$(green)Local API stopped$(normal)"
	rm -f .start/start-api.pid

# -------------------------------------- GraphQL
.PHONY: graphql-schema graphql-api
## Print GraphQL endpoint API URL
graphql-api:
	@echo "http://$(HOST_API):$(PORT)/graphql"

graphql-api-%:
	@$(VALIDATE_VENV)
	curl \
		-X POST \
		-H "Content-Type: application/json" \
		--data '{ "query": "{ haystack { about { name } } }" }' \
		http://$(HOST_API):$(PORT)/graphql/

schema.graphql: app/graphql_model.py app/blueprint_graphql.py
	@$(VALIDATE_VENV)
	python -m app.blueprint_graphql >schema.graphql

## Print haystack graphql schema
graphql-schema: schema.graphql
	@cat schema.graphql


# -------------------------------------- Minio
# https://min.io/
# See https://docs.min.io/docs/how-to-use-aws-sdk-for-python-with-minio-server.html
.minio:
	@mkdir -p .minio

start-minio: .minio $(REQUIREMENTS)
	@docker run -p 9000:9000 \
	-e "MINIO_ACCESS_KEY=$(AWS_ACCESS_KEY)" \
	-e "MINIO_SECRET_KEY=$(AWS_SECRET_KEY)" \
	-v  "$(MINIO_HOME):/data" \
	minio/minio server /data

async-stop-minio:
	@$(VALIDATE_VENV)
	[ -e .start/start-minio.pid ] && kill `cat .start/start-minio.pid` 2>/dev/null >/dev/null || true && echo -e "$(green)Local Minio stopped$(normal)"
	rm -f .start/start-minio.pid

async-start-minio: .minio $(REQUIREMENTS)
	@$(VALIDATE_VENV)
	[ -e .start/start-minio.pid ] && echo -e "$(yellow)Local Minio was allready started$(normal)" && exit
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
	echo -e "$(yellow)Local Minio was started$(normal)"


## Stop all background server
async-stop: async-stop-api async-stop-minio stop-pg stop-pgadmin stop-mysql stop-mongodb async-docker-stop


# -------------------------------------- AWS
ifeq ($(USE_OKTA),Y)
.PHONY: aws-update-token
# Update the AWS Token
aws-update-token: $(REQUIREMENTS)
	@aws sts get-caller-identity >/dev/null 2>/dev/null || gimme-aws-creds --profile $(AWS_PROFILE)
else
aws-update-token:
	@echo -e "$(yellow)Nothing to do to refresh the token. (Set USE_OKTA ?)$(normal)"
endif

.PHONY: aws-package aws-deploy aws-update aws-undeploy _zappa_settings

# Install a clean venv before invoking zappa
_zappa_pre_install: clean-zappa
	@virtualenv -p python$(PYTHON_VERSION) $(ZAPPA_ENV)
	source $(ZAPPA_ENV)/bin/activate
	pip install -U pip setuptools
	pip install -e '.[graphql,lambda]'
	find . | grep -E "(__pycache__|\.pyc|\.pyo$)" | xargs rm -rf

_zappa_settings: zappa_settings.json.template
	@envsubst <zappa_settings.json.template >zappa_settings.json

## Build lambda package
aws-package: $(REQUIREMENTS) _zappa_pre_install compile-all _zappa_settings aws-update-token
	@echo -e "$(cyan)Create lambda package...$(normal)"
	source $(ZAPPA_ENV)/bin/activate
	zappa package $(AWS_STAGE)
	rm -Rf $(ZAPPA_ENV)


## Deploy lambda functions
aws-deploy: $(REQUIREMENTS) _zappa_pre_install _zappa_settings compile-all
	@$(VALIDATE_VENV)
	source $(ZAPPA_ENV)/bin/activate
	zappa deploy $(AWS_STAGE)
	rm -Rf $(ZAPPA_ENV)
	echo -e "$(green)Lambdas are deployed$(normal)"
	grep --color=never 'HAYSTACK_' zappa_settings.json

## Update lambda functions
aws-update: $(REQUIREMENTS) _zappa_pre_install _zappa_settings compile-all
	@$(VALIDATE_VENV)
	source $(ZAPPA_ENV)/bin/activate
	zappa update $(AWS_STAGE)
	rm -Rf $(ZAPPA_ENV)
	echo -e "$(green)Lambdas are updated$(normal)"

## Remove AWS Stack
aws-undeploy: $(REQUIREMENTS) _zappa_settings
ifeq ($(USE_OKTA),Y)
	gimme-aws-creds --profile $(AWS_PROFILE)
endif
	@zappa undeploy $(AWS_STAGE) --remove-logs

.PHONY: aws-api
## Print AWS API endpoint URL
aws-api: aws-update-token
	@echo $(AWS_API_HOME)/

## Print GraphQL API endpoint URL
aws-graphql-api: aws-update-token
	@echo $(AWS_API_HOME)/graphql/

.PHONY: aws-api-*
## Call AWS api (ie. aws-api-about)
aws-api-%:
	@$(VALIDATE_VENV)
	TARGET="$(AWS_API_HOME)"
	curl -H "Accept: text/zinc" \
			"$${TARGET}/haystack/$*"

aws-api-read:
	@$(VALIDATE_VENV)
	TARGET="$(AWS_API_HOME)"
	curl -H "Accept: text/zinc" \
			"$${TARGET}/haystack/read?filter=point&limit=5"

aws-api-hisRead:
	@$(VALIDATE_VENV)
	TARGET="$(AWS_API_HOME)"
	curl -H "Accept: text/zinc" \
			"$${TARGET}/haystack/hisRead$(HISREAD_PARAMS)"

## Print AWS logs
aws-logs:
	@$(VALIDATE_VENV)
	zappa tail

_aws_check_repositoy:
	@[ ! -z "$(AWS_REPOSITORY)" ] || (echo "Set AWS_REPOSITORY" ; exit 1)

~/.docker/config.json: Makefile
	@aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $(AWS_REPOSITORY)

## Push the docker image to AWS repository
aws-docker-push: _aws_check_repositoy ~/.docker/config.json docker-build aws-update-token
	@docker tag $(DOCKER_REPOSITORY)/$(PRJ):latest $(AWS_REPOSITORY)/$(PRJ):latest
	docker image push $(AWS_REPOSITORY)/$(PRJ):latest

aws-docker-deploy: aws-update-token ~/.docker/config.json
	aws ecs run-task -task-definition task-def-name -cluster $(AWS_CLUSTER_NAME)

# -------------------------------------- Tests
.PHONY: unit-test
.make-unit-test: $(REQUIREMENTS) $(PYTHON_SRC) Makefile | .env
	@$(VALIDATE_VENV)
	$(CONDA_PYTHON) -m nose -s tests -a '!aws' --where=tests $(NOSETESTS_ARGS)
	date >.make-unit-test

## Run unit test
unit-test: .make-unit-test

.make-test: .make-unit-test
	@date >.make-test

## Run all tests (unit and functional)
test: .make-test

.make-test-aws: aws-update-token
	@$(VALIDATE_VENV)
	echo -e "$(green)Running AWS tests...$(normal)"
	$(CONDA_PYTHON) -m nose -s tests -a 'aws' --where=tests $(NOSETESTS_ARGS)
	echo -e "$(green)AWS tests done$(normal)"
	date >.make-test-aws

## Run only tests with connection with AWS
test-aws: .make-test-aws


# Test local deployment with URL provider
functional-url-local: $(REQUIREMENTS)
	@$(VALIDATE_VENV)
	@echo -e "$(green)Test URL local...$(normal)"
	@$(MAKE) async-stop-api >/dev/null
	export HAYSTACK_PROVIDER=shaystack.providers.db
	export HAYSTACK_DB=sample/carytown.zinc
	$(MAKE) HAYSTACK_PROVIDER=$$HAYSTACK_PROVIDER HAYSTACK_DB=$$HAYSTACK_DB async-start-api
	PYTHONPATH=tests:. $(CONDA_PYTHON) tests/functional_test.py
	echo -e "$(green)Test with url serveur and local file OK$(normal)"
	$(MAKE) async-stop-api >/dev/null

# Test local deployment with URL provider
functional-url-s3: $(REQUIREMENTS) aws-update-token
	@$(VALIDATE_VENV)
	@echo -e "$(green)Test URL on S3...$(normal)"
	@$(MAKE) async-stop-api >/dev/null
	export HAYSTACK_PROVIDER=shaystack.providers.db
	export HAYSTACK_DB=s3://shaystack/carytown.zinc
	$(MAKE)	HAYSTACK_PROVIDER=$$HAYSTACK_PROVIDER HAYSTACK_DB=$$HAYSTACK_DB async-start-api
	PYTHONPATH=tests:. $(CONDA_PYTHON) tests/functional_test_s3.py
	echo -e "$(green)Test with url serveur and s3 file OK$(normal)"
	$(MAKE) async-stop-api >/dev/null
#

# Clean DB, Start API, and try with SQLite
functional-db-sqlite: $(REQUIREMENTS)
	@$(VALIDATE_VENV)
	@echo -e "$(green)Test local SQLite...$(normal)"
	@$(MAKE) async-stop-api>/dev/null
	pip install supersqlite >/dev/null
	rm -f test.db
	export HAYSTACK_PROVIDER=shaystack.providers.db
	export HAYSTACK_DB=sqlite3://localhost/test.db
	$(CONDA_PYTHON) -m shaystack.providers.import_db --reset sample/carytown.zinc $${HAYSTACK_DB}
	echo -e "$(green)Data imported in SQLite ($${HAYSTACK_DB})$(normal)"
	$(MAKE) HAYSTACK_PROVIDER=$$HAYSTACK_PROVIDER HAYSTACK_DB=$$HAYSTACK_DB async-start-api
	PYTHONPATH=tests:. $(CONDA_PYTHON) tests/functional_test.py
	echo -e "$(green)Test with local SQLite serveur OK$(normal)"
	$(MAKE) async-stop-api >/dev/null

# Clean DB, Start API, and try with SQLite + Time stream
functional-db-sqlite-ts: $(REQUIREMENTS)
	@$(VALIDATE_VENV)
	@echo -e "$(green)Test local SQLite + Timestream...$(normal)"
	@$(MAKE) async-stop-api>/dev/null
	pip install supersqlite boto3 >/dev/null
	rm -f test.db
	export HAYSTACK_PROVIDER=shaystack.providers.timestream
	export HAYSTACK_DB=sqlite3://localhost/test.db
	export HAYSTACK_TS='timestream://shaystack?mem_ttl=8760&mag_ttl=400'
	export LOG_LEVEL=INFO
	#$(CONDA_PYTHON) -m shaystack.providers.import_db --reset sample/carytown.zinc $${HAYSTACK_DB} $${HAYSTACK_TS}
	echo -e "$(green)Data imported in SQLite and Time stream ($${HAYSTACK_DB})$(normal)"
	$(MAKE) HAYSTACK_PROVIDER="$$HAYSTACK_PROVIDER" HAYSTACK_DB="$$HAYSTACK_DB" \
    	HAYSTACK_TS="$$HAYSTACK_TS" async-start-api
	# PYTHONPATH=tests:. $(CONDA_PYTHON) tests/functional_test.py
	# echo -e "$(green)Test with local SQLite serveur and Time Stream OK$(normal)"
	$(MAKE) async-stop-api >/dev/null


# Start Postgres, Clean DB, Start API and try
functional-db-postgres: $(REQUIREMENTS) clean-pg
	@$(VALIDATE_VENV)
	@echo -e "$(green)Test local Postgres...$(normal)"
	@$(MAKE) async-stop-api >/dev/null
	pip install psycopg2 >/dev/null
	$(MAKE) start-pg
	PG_IP=$(shell docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' postgres)
	export HAYSTACK_PROVIDER=shaystack.providers.db
	export HAYSTACK_DB=postgresql://postgres:password@localhost:5432/postgres#haystack
	$(CONDA_PYTHON) -m shaystack.providers.import_db --reset sample/carytown.zinc $${HAYSTACK_DB}
	echo -e "$(green)Data imported in Postgres ($${HAYSTACK_DB})$(normal)"
	$(MAKE) HAYSTACK_PROVIDER=$$HAYSTACK_PROVIDER HAYSTACK_DB=$$HAYSTACK_DB async-start-api
	PYTHONPATH=tests:. $(CONDA_PYTHON) tests/functional_test.py
	echo -e "$(green)Test with local Postgres serveur OK$(normal)"
	$(MAKE) async-stop-api >/dev/null


# Start mysql, Clean DB, Start API and try
functional-db-mysql: $(REQUIREMENTS) clean-mysql
	@$(VALIDATE_VENV)
	@echo -e "$(green)Test local MySQL...$(normal)"
	@$(MAKE) async-stop-api >/dev/null
	pip install pymysql >/dev/null
	$(MAKE) start-mysql
	PG_IP=$(shell docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' mysql)
	export HAYSTACK_PROVIDER=shaystack.providers.db
	export HAYSTACK_DB=mysql://mysql:password@localhost/haystackdb#haystack
	$(CONDA_PYTHON) -m shaystack.providers.import_db --reset sample/carytown.zinc $${HAYSTACK_DB}
	echo -e "$(green)Data imported in MySQL ($${HAYSTACK_DB})$(normal)"
	$(MAKE) HAYSTACK_PROVIDER=$$HAYSTACK_PROVIDER HAYSTACK_DB=$$HAYSTACK_DB async-start-api
	PYTHONPATH=tests:. $(CONDA_PYTHON) tests/functional_test.py
	echo -e "$(green)Test with local MySQL serveur OK$(normal)"
	$(MAKE) async-stop-api >/dev/null


# Start mongodb, Clean DB, Start API and try
functional-mongodb: $(REQUIREMENTS) #clean-mongodb
	@$(VALIDATE_VENV)
	@echo -e "$(green)Test local MongoDB...$(normal)"
	$(MAKE) async-stop-api >/dev/null
	pip install pymongo >/dev/null
	$(MAKE) start-mongodb
	PG_IP=$(shell docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' mongodb)
	export HAYSTACK_PROVIDER=shaystack.providers.mongodb
	export HAYSTACK_DB=mongodb://localhost/haystackdb#haystack
	$(CONDA_PYTHON) -m shaystack.providers.import_db --reset sample/carytown.zinc $${HAYSTACK_DB}
	echo -e "$(green)Data imported in MongoDB ($${HAYSTACK_DB})$(normal)"
	$(MAKE) HAYSTACK_PROVIDER=$$HAYSTACK_PROVIDER HAYSTACK_DB=$$HAYSTACK_DB async-start-api
	PYTHONPATH=tests:. $(CONDA_PYTHON) tests/functional_test.py
	echo -e "$(green)Test with local MongoDB serveur OK$(normal)"
	$(MAKE) async-stop-api >/dev/null

.PHONY: functional-database
functional-database: $(REQUIREMENTS) start-pg start-mysql start-mongodb
	@$(VALIDATE_VENV)
	echo -e "$(green)Test same request with all databases...$(normal)"
	@$(CONDA_PYTHON) -m nose tests/test_provider_db.py $(NOSETESTS_ARGS)
	echo -e "$(green)Test same request with all databases OK$(normal)"

#functional-db-sqlite and functional-db-sqlite-ts not available
.make-functional-test: functional-url-local  functional-db-postgres functional-db-mysql\
		functional-url-s3 functional-mongodb functional-database
	@touch .make-functional-test

## Test graphql client with different providers
functional-test: .make-functional-test

# -------------------------------------- Typing
pytype.cfg: $(CONDA_PREFIX)/bin/pytype
	@$(VALIDATE_VENV)
	[[ ! -f pytype.cfg ]] && pytype --generate-config pytype.cfg || true
	touch pytype.cfg

.PHONY: typing
.make-typing: $(REQUIREMENTS) $(CONDA_PREFIX)/bin/pytype pytype.cfg $(PYTHON_SRC)
	@$(VALIDATE_VENV)
	echo -e "$(cyan)Check typing...$(normal)"
	MYPYPATH=stubs pytype --config=pytype.cfg -V $(PYTHON_VERSION) shaystack app tests
	touch .make-typing

## Check python typing
typing: .make-typing

# -------------------------------------- Lint
.PHONY: lint
.pylintrc:
	@$(VALIDATE_VENV)
	pylint --generate-rcfile > .pylintrc

.make-lint: $(REQUIREMENTS) $(PYTHON_SRC) | .pylintrc .pylintrc-test
	@$(VALIDATE_VENV)
	echo -e "$(cyan)Check lint...$(normal)"
	pylint -d duplicate-code app shaystack
	echo -e "$(cyan)Check lint for tests...$(normal)"
	pylint --rcfile=.pylintrc-test tests
	touch .make-lint

## Lint the code
lint: .make-lint


.PHONY: validate
.make-validate: .make-typing .make-lint .make-test .make-test-aws .make-functional-test dist
	@echo -e "$(green)The project is validated$(normal)"
	date >.make-validate

## Validate the project
validate: .make-validate


# ------------- Postgres database
## Print sqlite db url connection
sqlite-url:
	@echo "sqlite3://test.db#haystack"

# ------------- Postgres database
## Start Postgres database in background
start-pg:
	@docker start postgres || docker run \
		--name postgres \
		--hostname postgres \
		-e POSTGRES_PASSWORD=password \
		-p 5432:5432 \
		-d postgres
	echo -e "$(yellow)Postgres started$(normal)"

## Stop postgres database
stop-pg:
	@docker stop postgres 2>/dev/null >/dev/null || true
	echo -e "$(green)Postgres stopped$(normal)"

## Print Postgres db url connection
url-pg: start-pg
	@IP=$$(docker inspect --format '{{ .NetworkSettings.IPAddress }}' postgres)
	echo "postgres://postgres:password@$$IP:5432/postgres#haystack"

pg-shell:
	@IP=$$(docker inspect --format '{{ .NetworkSettings.IPAddress }}' postgres)
	docker exec -e PGPASSWORD=$(PG_PASSWORD) -it postgres psql -U postgres -h $$IP

clean-pg: start-pg
	@IP=$$(docker inspect --format '{{ .NetworkSettings.IPAddress }}' postgres)
	docker exec -e PGPASSWORD=$(PG_PASSWORD) -t postgres psql -U postgres -h $$IP \
	-c 'drop table if exists haystack;drop table if exists haystack_meta_datas;drop table if exists haystack_ts;'


## Start PGAdmin in background
start-pgadmin:
	@docker start pgadmin || docker run \
	--name pgadmin \
	-p 8082:80 \
	--link postgres \
    -e 'PGADMIN_DEFAULT_EMAIL=$(PGADMIN_USER)' \
    -e 'PGADMIN_DEFAULT_PASSWORD=$(PGADMIN_PASSWORD)' \
    -d dpage/pgadmin4
	echo -e "$(yellow)PGAdmin started (http://$(HOST_API):8082). Use $(cyan)$(PGADMIN_USER)$(yellow) and $(cyan)$(PGADMIN_PASSWORD)$(yellow) $(normal)"

## Stop PGAdmin
stop-pgadmin:
	@docker stop pgadmin 2>/dev/null >/dev/null || true
	echo -e "$(green)PGAdmin stopped$(normal)"

# ------------- MySQL database
## Start MySQL database in background
start-mysql:
	@docker start mysql || docker run \
		--name mysql \
		--hostname mysql \
		-e MYSQL_DATABASE="haystackdb" \
		-e MYSQL_PASS="password" \
		-e MYSQL_ROOT_PASSWORD=$(MYSQL_PASSWORD) \
		-e MYSQL_USER=$(MYSQL_USER) \
		-e MYSQL_PASSWORD=$(MYSQL_PASSWORD) \
		-p 3306:3306 \
		-d mysql
	sleep 2
	echo -e "$(yellow)MySQL started$(normal)"

## Stop MySQL database
stop-mysql:
	@docker stop mysql 2>/dev/null >/dev/null || true
	echo -e "$(green)MySQL stopped$(normal)"

## Print Postgres db url connection
url-mysql: start-mysql
	@IP=$$(docker inspect --format '{{ .NetworkSettings.IPAddress }}' mysql)
	echo "mysql://mysql:password@$$IP:3306/haystackdb#haystack"

# Start a shell for MySQL
mysql-shell:
	docker exec -it mysql mysql --user=root --password=$(MYSQL_PASSWORD) -h localhost haystackdb

# Clean MySQL database
clean-mysql: start-mysql
	@IP=$$(docker inspect --format '{{ .NetworkSettings.IPAddress }}' mysql)
	docker exec -t mysql mysql --user=root --password=$(MYSQL_PASSWORD) -h localhost haystackdb \
	--execute='drop table if exists haystack ; drop table if exists haystack_meta_datas ; drop table if exists haystack_ts;'


# ------------- Mongo database
## Start Mongo database in background
start-mongodb:
	@docker start mongodb || docker run \
		--name mongodb \
		--hostname mongodb \
        -e MONGO_INITDB_ROOT_USERNAME=$(MONGO_USER) \
	    -e MONGO_INITDB_ROOT_PASSWORD=$(MONGO_PASSWORD) \
	    --authenticationDatabase admin \
		-p 27017-27019:27017-27019 \
		-d haystackdb
	sleep 2
	echo -e "$(yellow)MongoDB started$(normal)"

## Stop mongo database
stop-mongodb:
	@docker stop mongodb 2>/dev/null >/dev/null || true
	echo -e "$(green)MongoDB stopped$(normal)"

## Start Mongo CI
mongo: start-mongodb
	docker exec -it mongodb mongo mongodb://localhost/haystackdb

# Start shell in mongodo docker container
mongodb-shell:
	docker exec -it mongodb mongosh

## Print Postgres db url connection
url-mongo: start-mongodb
	@IP=$$(docker inspect --format '{{ .NetworkSettings.IPAddress }}' mongodb)
	echo "mongo://$$IP:3306/haystackdb#haystack"

# Clean Mongo database
clean-mongodb: start-mongodb
	@docker exec -t mongodb mongosh mongodb://localhost/haystackdb \
	--quiet --eval 'db.haystack.drop();db.haystack_ts.drop();db.haystack_meta_datas.drop();' >/dev/null


# --------------------------- Docker
## Build a Docker image with the project and current Haystack parameter (see `make dump-params`)
docker-build:
	@echo "Build image with"
	echo -e "$(green)PROVIDER=$${HAYSTACK_PROVIDER}"
	echo -e "$(green)DB=$${HAYSTACK_DB}"
	echo -e "$(green)TS=$${HAYSTACK_TS}"
	@docker build \
		--build-arg PORT='$(PORT)' \
		--build-arg HAYSTACK_PROVIDER='$(HAYSTACK_PROVIDER)' \
		--build-arg HAYSTACK_DB='$(HAYSTACK_DB)' \
		--build-arg HAYSTACK_TS='$(HAYSTACK_TS)' \
		--build-arg REFRESH='$(REFRESH)' \
		--build-arg STAGE='$(STAGE)' \
		--build-arg PIP_INDEX_URL='$(PIP_INDEX_URL)' \
		--build-arg PIP_EXTRA_INDEX_URL='$(PIP_EXTRA_INDEX_URL)' \
		--tag '$(DOCKER_REPOSITORY)/$(PRJ)' \
		-f docker/Dockerfile .
	echo -e "$(green)Docker image '$(yellow)$(DOCKER_REPOSITORY)/$(PRJ)$(green)' build with$(normal)"
	$(MAKE) dump-params

## Run the docker image
docker-run: async-docker-stop docker-rm docker-inspect
	docker run --rm \
		-it \
		--name '$(PRJ)' \
		-p $(PORT):$(PORT) \
		$(DOCKER_REPOSITORY)/$(PRJ)

# Print environment variables inside the docker image
docker-inspect:
	@echo -e "$(green)Parameter inside the docker image:$(normal)"
	docker inspect --format '{{join .Config.Env "\n" }}' $(DOCKER_REPOSITORY)/$(PRJ)

## Run the docker with a Flask server in background
async-docker-start: docker-rm
	@docker run -dp $(PORT):$(PORT) --name '$(PRJ)' $(DOCKER_REPOSITORY)/$(PRJ)
	echo -e "$(green)shift-4-haystack in docker is started$(normal)"

## Stop the background docker with a Flask server
async-docker-stop:
	@docker stop '$(PRJ)' 2>/dev/null >/dev/null || true
	echo -e "$(green)'$(DOCKER_REPOSITORY)/$(PRJ)' docker stopped$(normal)"

## Remove the docker image
docker-rm: async-docker-stop
	@docker rm '$(PRJ)' >/dev/null || true
	echo -e "$(green)'$(DOCKER_REPOSITORY)/$(PRJ)' docker removed$(normal)"

# Start the docker image with current shell
docker-run-shell:
	docker run --rm \
		-it \
		--name '$(PRJ)' \
		-p $(PORT):$(PORT) \
		--entrypoint $(SHELL) \
		$(DOCKER_REPOSITORY)/$(PRJ)

# --------------------------- Docker Make
.PHONY: docker-build-dmake docker-alias-dmake docker-inspect-dmake \
	docker-configure-dmake docker-exec-dmake docker-inspect-dmake docker-rm-dmake

#-v "$(CONDA_BASE):/opt/conda"
_DOCKER_RUN_PARAMS=\
--rm \
-v "$(CONDA_BASE)/envs/:/opt/conda/envs" \
-v "$(PWD):/$(PRJ)" \
-v /var/run/docker.sock:/var/run/docker.sock \
-v $$HOME/.aws:/home/$(PRJ)/.aws \
-v $$HOME/.okta_aws_login_config:/home/$(PRJ)/.okta_aws_login_config \
--group-add $$(getent group docker | cut -d: -f3) \
-it

DMAKE=docker run $(_DOCKER_RUN_PARAMS) $(DOCKER_REPOSITORY)/$(PRJ)-dmake

## Create a docker image to build the project with dmake (docker make)
docker-build-dmake: docker/DMake.Dockerfile
	@echo -e "$(green)Build docker image '$(DOCKER_REPOSITORY)/$(PRJ)-dmake' to build the project...$(normal)"
	REPO=$(shell git remote get-url origin)
	docker build \
		--build-arg UID=$$(id -u) \
		--build-arg AWS_PROFILE="$(AWS_PROFILE)" \
		--build-arg AWS_REGION="$(AWS_REGION)" \
		--build-arg PYTHON_VERSION="$(PYTHON_VERSION)" \
		--build-arg USE_OKTA="$(USE_OKTA)" \
		--build-arg PIP_INDEX_URL='$(PIP_INDEX_URL)' \
		--build-arg PIP_EXTRA_INDEX_URL='$(PIP_EXTRA_INDEX_URL)' \
		--build-arg PORT=$(PORT) \
		--tag $(DOCKER_REPOSITORY)/$(PRJ)-dmake \
		-f docker/DMake.Dockerfile .
	# but with the mapping /opt/conda
	$(MAKE) docker-configure-dmake
	echo ""
	echo -e "$(green)Image '$(DOCKER_REPOSITORY)/$(PRJ)-dmake' build with:$(normal)"
	$(MAKE) docker-inspect-dmake
	$(MAKE) docker-alias-dmake

# Print the alias for 'dmake'
docker-alias-dmake:
	@printf	"$(green)Declare\n$(cyan)alias dmake='$(DMAKE)'\n"
	echo -e "$(green)and use $(cyan)dmake ...$(normal)  # Use make in a Docker container"

# Hack to create the venv docker-shaystack inside the docker
docker-configure-dmake: $(CONDA_BASE)/envs/docker-$(PRJ)

$(CONDA_BASE)/envs/docker-$(PRJ): docker/DMake.Dockerfile
	$(DMAKE) \
		CONDA_PREFIX=/opt/conda \
		VALIDATE_VENV='exit' \
		VENV=docker-shaystack \
		PYTHON_VERSION=$(PYTHON_VERSION) \
		_configure

# Start a shell to build the project in a docker container
docker-exec-dmake:
	@docker run \
		--entrypoint bash \
		--user 1000 \
		$(_DOCKER_RUN_PARAMS) \
		$(DOCKER_REPOSITORY)/$(PRJ)-dmake

# Print env variable for the docker image dmake
docker-inspect-dmake:
	@echo -e "$(green)Parameter inside the docker dmake image:$(normal)"
	docker inspect --format '{{join .Config.Env "\n" }}' $(DOCKER_REPOSITORY)/$(PRJ)-dmake

# Remove the dmake image
docker-rm-dmake:
	@docker image rm $(DOCKER_REPOSITORY)/$(PRJ)-dmake || true
	echo -e "$(cyan)Docker image '$(DOCKER_REPOSITORY)/$(PRJ)-make' removed$(normal)"

# --------------------------- Distribution
dist/:
	mkdir dist

.PHONY: bdist
dist/$(subst -,_,$(PRJ_PACKAGE))-*.whl: $(REQUIREMENTS) $(PYTHON_SRC) schema.graphql | dist/
	@$(VALIDATE_VENV)
	export PBR_VERSION=$$(git describe --tags)
	$(CONDA_PYTHON) setup.py bdist_wheel

## Create a binary wheel distribution
bdist: dist/$(subst -,_,$(PRJ_PACKAGE))-*.whl | dist/

.PHONY: sdist
dist/$(PRJ_PACKAGE)-*.tar.gz: $(REQUIREMENTS) schema.graphql | dist/
	@$(VALIDATE_VENV)
	$(CONDA_PYTHON) setup.py sdist

sdist: dist/$(PRJ_PACKAGE)-*.tar.gz | dist/

.PHONY: clean-dist dist

clean-dist:
	rm -Rf dist/*

# see https://packaging.python.org/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/
## Create a full distribution
dist: clean-dist bdist sdist
	@echo -e "$(yellow)Package for distribution created$(normal)"

.PHONY: check-twine test-keyring test-twine
## Check the distribution before publication
check-twine: bdist
	@$(VALIDATE_VENV)
	twine check \
		$(shell find dist/ -type f \( -name "*.whl" -or -name '*.gz' \) -and ! -iname "*dev*" )

## Create keyring for Test-twine
test-keyring:
	@[ -s "$$TWINE_USERNAME" ] && read -p "Test Twine username:" TWINE_USERNAME
	keyring set https://test.pypi.org/legacy/ $$TWINE_USERNAME

## Publish distribution on test.pypi.org
test-twine: dist check-twine
	@$(VALIDATE_VENV)
	[[ $$( find dist/ -name "*.dev*.whl" | wc -l ) == 0 ]] || \
		( echo -e "$(red)Add a tag version in GIT before release$(normal)" \
		; exit 1 )
	rm -f dist/*.asc
	echo -e "$(green)Enter the Pypi password$(normal)"
	twine upload --sign -i $(SIGN_IDENTITY) --repository-url https://test.pypi.org/legacy/ \
		$(shell find dist/ -type f \( -name "*.whl" -or -name '*.gz' \) -and ! -iname "*dev*" )
	echo -e "To the test repositiry"
	echo -e "$(green)export PIP_INDEX_URL=https://test.pypi.org/simple$(normal)"
	echo -e "$(green)export PIP_EXTRA_INDEX_URL=https://pypi.org/simple$(normal)"

.PHONY: keyring release

## Create keyring for release
keyring:
	@[ -s "$$TWINE_USERNAME" ] && read -p "Twine username:" TWINE_USERNAME
	keyring set https://upload.pypi.org/legacy/ $$TWINE_USERNAME

.PHONY: push-docker-release push-release release

## Publish a distribution on pypi.org
release: clean .make-validate check-twine
	@$(VALIDATE_VENV)
	[[ $$( find dist/ -name "*.dev*" | wc -l ) == 0 ]] || \
		( echo -e "$(red)Add a tag version in GIT before release$(normal)" \
		; exit 1 )
	rm -f dist/*.asc
	echo -e "$(green)Enter the Pypi password$(normal)"
	twine upload --sign \
		$(shell find dist -type f \( -name "*.whl" -or -name '*.gz' \) -and ! -iname "*dev*" )

# Push release in dockerhub
docker-push-release: docker-build
	TAG=$(shell git describe --abbrev=0)
	docker push $(DOCKER_REPOSITORY)/shaystack
	docker image tag $(DOCKER_REPOSITORY)/shaystack $(DOCKER_REPOSITORY)/shaystack:$(TAG)
	docker push $(DOCKER_REPOSITORY)/shaystack:$(TAG)

## Publish the release and tag
push-release: docker-push-release
	TAG=$(shell git describe --abbrev=0)
	git push --atomic origin master $TAG
