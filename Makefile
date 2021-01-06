#!/usr/bin/env make -f
SHELL=/bin/bash
.SHELLFLAGS = -e -c
.ONESHELL:

ifeq ($(ARTIFACTS_DIR),)
ifeq ($(shell echo "$(shell echo $(MAKE_VERSION) | sed 's@^[^0-9]*\([0-9]\+\).*@\1@' ) >= 4" | bc -l),0)
$(error Bad make version, please install make >= 4 ($(MAKE_VERSION)))
endif
endif

PRJ?=haystackapi
HAYSTACK_PROVIDER?=haystackapi.providers.url
HAYSTACK_URL?=sample/carytown.zinc
HAYSTACK_DB?=sqlite3:///:memory:#haystack
USE_OKTA?=N
AWS_PROFILE?=default
AWS_REGION?=eu-west-3
LOGLEVEL?=WARNING
HISREAD_PARAMS=?id=@id1

# Override project variables
ifneq (,$(wildcard .env))
include .env
endif

# Export all project variables
export PRJ
export HAYSTACK_PROVIDER
export HAYSTACK_URL
export HAYSTACK_DB
export LOGLEVEL
export AWS_PROFILE
export PYTHON_VERSION
export HISREAD_PARAMS
export FLASK_DEBUG


PYTHON_SRC=$(shell find . -name '*.py')
PYTHON_VERSION:=3.8
PRJ_PACKAGE:=$(PRJ)
VENV ?= $(PRJ)
CONDA_BASE:=$(shell conda info --base)
CONDA_PACKAGE:=$(CONDA_PREFIX)/lib/python$(PYTHON_VERSION)/site-packages
CONDA_PYTHON:=$(CONDA_PREFIX)/bin/python
CONDA_ARGS?=
FLASK_DEBUG?=1
AWS_STAGE?=dev
GIMME?=gimme-aws-creds
ZAPPA_ENV=zappa_venv

PIP_PACKAGE:=$(CONDA_PACKAGE)/$(PRJ_PACKAGE).egg-link

AWS_API_HOME=$(shell zappa status $(AWS_STAGE) --json | jq -r '."API Gateway URL"')

# For minio
MINIO_HOME=$(HOME)/.minio
AWS_ACCESS_KEY=$(shell aws configure --profile $(AWS_PROFILE) get aws_access_key_id)
AWS_SECRET_KEY=$(shell aws configure --profile $(AWS_PROFILE) get aws_secret_access_key)


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
	@echo PRJ="$(PRJ)"
	echo HAYSTACK_PROVIDER='$(HAYSTACK_PROVIDER)'
	echo HAYSTACK_URL='$(HAYSTACK_URL)'
	echo HAYSTACK_DB='$(HAYSTACK_DB)'
	echo AWS_PROFILE='$(AWS_PROFILE)'
	echo AWS_STAGE='$(AWS_STAGE)'

# -------------------------------------- GIT
.env:
	touch .env

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
$(PIP_PACKAGE): $(CONDA_PYTHON) setup.py | .git # Install pip dependencies
	@$(VALIDATE_VENV)
	echo -e "$(cyan)Install build dependencies ... (may take minutes)$(normal)"
ifeq ($(USE_OKTA),Y)
	pip install gimme-aws-creds
endif
	conda install -c conda-forge -c anaconda -y \
		make jq
	echo -e "$(cyan)Install project dependencies ...$(normal)"
	echo -e "$(cyan)pip install -e .$(normal)"
	pip install -e .
	echo -e "$(cyan)pip install -e .[dev,flask,graphql,lambda]$(normal)"
	pip install -e "file://$$(pwd)#egg=haystackapi[dev,flask,graphql,lambda]"
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
# Remove all the pip package
clean-pip:
	@pip freeze | grep -v "^-e" | grep -v "@" | xargs pip uninstall -y
	@echo -e "$(cyan)Virtual env cleaned$(normal)"

.PHONY: clean-venv clean-$(VENV)
# Clean venv
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
	@rm -rf bin/* .mypy_cache .pytest_cache .start build nohup.out dist/ .make-* .pytype out.json
	mkdir dist/

.PHONY: clean-all
# Clean all environments
clean-all: clean remove-venv


# -------------------------------------- Build

.PHONY: dist build compile-all

# Compile all python files
compile-all:
	@echo -e "$(cyan)Compile all python file...$(normal)"
	$(CONDA_PYTHON) -m compileall

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
	@$(VALIDATE_VENV)
	TARGET="localhost:3000"
	curl -H "Accept: text/zinc" \
			"$${TARGET}/haystack/read$(READ_PARAMS)"

api-hisRead:
	@$(VALIDATE_VENV)
	TARGET="localhost:3000"
	curl -H "Accept: text/zinc" \
			"$${TARGET}/haystack/hisRead$(HISREAD_PARAMS)"

.PHONY: start-api async-start-api async-stop-api
## Start api
start-api: $(REQUIREMENTS)
	@$(VALIDATE_VENV)
	@[ -e .start/start-api.pid ] && $(MAKE) async-stop-api || true
	echo "$(green)PROVIDER=${HAYSTACK_PROVIDER}"
	echo "$(green)URL=${HAYSTACK_URL}"
	echo "$(green)DB=${HAYSTACK_DB}"
	echo "$(green)Use http://localhost:3000/graphql or http://localhost:3000/haystack$(normal)"
	FLASK_DEBUG=1 FLASK_ENV=$(AWS_STAGE) \
	$(CONDA_PYTHON) -m app.__init__

# Start local api in background
async-start-api: $(REQUIREMENTS)
	$(VALIDATE_VENV)
	[ -e .start/start-api.pid ] && echo -e "$(yellow)Local API was allready started$(normal)" && exit
	mkdir -p .start
	FLASK_DEBUG=1 FLASK_APP=app.run FLASK_ENV=$(AWS_STAGE) \
	nohup $(CONDA_PYTHON) -m app.__init__ >.start/start-api.log 2>&1 &
	echo $$! >.start/start-api.pid
	sleep 0.5
	tail .start/start-api.log
	echo -e "$(yellow)Local API started$(normal)"

# Stop local api emulator in background
async-stop-api:
	$(VALIDATE_VENV)
	@[ -e .start/start-api.pid ] && kill `cat .start/start-api.pid` 2>/dev/null >/dev/null || true && echo -e "$(green)Local API stopped$(normal)"
	rm -f .start/start-api.pid

# -------------------------------------- GraphQL
.PHONY: graphql-schema graphql-api
## Print GraphQL API url
graphql-api:
	@echo "http://localhost:3000/graphql/"

graphql-api-%:
	@$(VALIDATE_VENV)
	curl \
		-X POST \
		-H "Content-Type: application/json" \
		--data '{ "query": "{ haystack { about { name } } }" }' \
		http://localhost:3000/graphql/

schema.graphql: app/graphql_model.py app/blueprint_graphql.py
	@$(VALIDATE_VENV)
	@python -m app.blueprint_graphql >schema.graphql

## Print haystack graphql schema
graphql-schema: schema.graphql
	@cat schema.graphql


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


## Stop all async server
async-stop: async-stop-api async-stop-minio stop-pg stop-pgadmin

# -------------------------------------- AWS
ifeq ($(USE_OKTA),Y)
.PHONY: aws-update-token
# Update the AWS Token
aws-update-token:
	@aws sts get-caller-identity >/dev/null 2>/dev/null || $(subst $\",,$(GIMME)) --profile $(AWS_PROFILE)
else
aws-update-token:
	echo -e "$(yellow)Nothing to do to refresh the token. (Set USE_OKTA and GIMME ?)$(normal)"
endif

.PHONY: aws-package aws-deploy aws-update aws-undeploy

# Install a clean venv before invoking zappa
_zappa_pre_install: clean-zappa
	@virtualenv -p python$(PYTHON_VERSION) $(ZAPPA_ENV)
ifeq ($(USE_OKTA),Y)
	$(subst $\",,$(GIMME)) --profile $(AWS_PROFILE)
endif
	source $(ZAPPA_ENV)/bin/activate
	pip install -e '.[graphql,lambda,aws]'

## Build lambda package
aws-package: $(REQUIREMENTS) _zappa_pre_install compile-all
	echo -e "$(cyan)Create lambda package...$(normal)"
	source $(ZAPPA_ENV)/bin/activate
	zappa package $(AWS_STAGE)
	rm -Rf $(ZAPPA_ENV)


## Deploy lambda functions
aws-deploy: $(REQUIREMENTS) _zappa_pre_install compile-all
	$(VALIDATE_VENV)
	source $(ZAPPA_ENV)/bin/activate
	zappa deploy $(AWS_STAGE)
	rm -Rf $(ZAPPA_ENV)
	echo -e "$(green)Lambdas are deployed$(normal)"

## Update lambda functions
aws-update: $(REQUIREMENTS) _zappa_pre_install compile-all
	@$(VALIDATE_VENV)
	source $(ZAPPA_ENV)/bin/activate
	zappa update $(AWS_STAGE)
	rm -Rf $(ZAPPA_ENV)
	echo -e "$(green)Lambdas are updated$(normal)"

## Remove AWS Stack
aws-undeploy: $(REQUIREMENTS)
ifeq ($(USE_OKTA),Y)
	$(subst $\",,$(GIMME)) --profile $(AWS_PROFILE)
endif
	zappa undeploy $(AWS_STAGE) --remove-logs

.PHONY: aws-api
## Print AWS API URL
aws-api: aws-update-token
	@echo $(AWS_API_HOME)

## Print GraphQL API url
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

# -------------------------------------- Tests
.PHONY: unit-test
.make-unit-test: $(REQUIREMENTS) $(PYTHON_SRC) Makefile | .env
	@$(VALIDATE_VENV)
	PYTHONPATH=tests:. $(CONDA_PYTHON) -m nose -s tests $(NOSETESTS_ARGS)
	date >.make-unit-test
## Run unit test
unit-test: .make-unit-test

.make-test: .make-unit-test
	@date >.make-test

## Run all tests (unit and functional)
test: .make-test

# Test local deployement with URL provider
functional-url-local: $(REQUIREMENTS)
	@$(MAKE) async-stop-api >/dev/null
	export HAYSTACK_PROVIDER=haystackapi.providers.url
	export HAYSTACK_URL=sample/carytown.zinc
	$(MAKE) async-start-api >/dev/null
	PYTHONPATH=tests:. $(CONDA_PYTHON) tests/functional_test.py
	echo -e "$(green)Test with url serveur and local file OK$(normal)"
	$(MAKE) async-stop-api >/dev/null

# Test local deployement with URL provider
functional-url-s3: $(REQUIREMENTS) aws-update-token
	@$(MAKE) async-stop-api >/dev/null
	export HAYSTACK_PROVIDER=haystackapi.providers.url
	export HAYSTACK_URL=s3://haystackapi/carytown.zinc
	$(MAKE) async-start-api >/dev/null
	PYTHONPATH=tests:. $(CONDA_PYTHON) tests/functional_test.py
	echo -e "$(green)Test with url serveur and s3 file OK$(normal)"
	$(MAKE) async-stop-api >/dev/null

# Clean DB, Start API, and try with SQLite
functional-db-sqlite: $(REQUIREMENTS)
	@$(MAKE) async-stop-api>/dev/null
	pip install supersqlite
	rm -f test.db
	export HAYSTACK_PROVIDER=haystackapi.providers.sql
	export HAYSTACK_DB=sqlite3://localhost/test.db
	$(CONDA_PYTHON) -m haystackapi.providers.import_db sample/carytown.zinc $${HAYSTACK_DB}
	echo -e "$(green)Data imported in SQLite$(normal)"
	$(MAKE) async-start-api >/dev/null
	PYTHONPATH=tests:. $(CONDA_PYTHON) tests/functional_test.py
	echo -e "$(green)Test with local SQLite serveur OK$(normal)"
	$(MAKE) async-stop-api >/dev/null

# Start Postgres, Clean DB, Start API and try
functional-db-postgres: $(REQUIREMENTS) clean-pg
	@$(MAKE) async-stop-api >/dev/null
	pip install psycopg2
	export HAYSTACK_PROVIDER=haystackapi.providers.sql
	export HAYSTACK_DB=postgres://postgres:password@172.17.0.2:5432/postgres
	$(CONDA_PYTHON) -m haystackapi.providers.import_db sample/carytown.zinc $${HAYSTACK_DB}
	echo -e "$(green)Data imported in Postgres$(normal)"
	$(MAKE) start-pg async-start-api >/dev/null

	PYTHONPATH=tests:. $(CONDA_PYTHON) tests/functional_test.py
	echo -e "$(green)Test with local Postgres serveur OK$(normal)"
	$(MAKE) async-stop-api >/dev/null

.make-functional-test: functional-url-local functional-db-sqlite functional-db-postgres functional-url-s3
	@touch .make-functional-test

## Test graphql client with different providers
functional-test: .make-functional-test

# -------------------------------------- Typing
pytype.cfg: $(CONDA_PREFIX)/bin/pytype
	@$(VALIDATE_VENV)
	@[[ ! -f pytype.cfg ]] && pytype --generate-config pytype.cfg || true
	touch pytype.cfg

.PHONY: typing
.make-typing: $(REQUIREMENTS) $(CONDA_PREFIX)/bin/pytype pytype.cfg $(PYTHON_SRC)
	$(VALIDATE_VENV)
	@echo -e "$(cyan)Check typing...$(normal)"
	MYPYPATH=stubs pytype -V $(PYTHON_VERSION) haystackapi app tests
	touch .make-typing

## Check python typing
typing: .make-typing

# -------------------------------------- Lint
.PHONY: lint
.pylintrc:
	@$(VALIDATE_VENV)
	pylint --generate-rcfile > .pylintrc

.make-lint: $(REQUIREMENTS) $(PYTHON_SRC) | .pylintrc .pylintrc-test
	$(VALIDATE_VENV)
	@echo -e "$(cyan)Check lint...$(normal)"
	@pylint -d duplicate-code app haystackapi
	@echo -e "$(cyan)Check lint for tests...$(normal)"
	@pylint --rcfile=.pylintrc-test tests
	touch .make-lint

## Lint the code
lint: .make-lint


.PHONY: validate
.make-validate: .make-typing .make-lint .make-test .make-functional-test dist
	@date >.make-validate

## Validate the project
validate: .make-validate


.PHONY: release
## Release the project
release: clean .make-validate

# ------------- Postgres database
## Print sqlite db url connection
sqlite-url:
	echo "sqlite3://test.db#haystack"

# ------------- Postgres database
## Start postgres database
start-pg:
	@docker start postgres || docker run \
		--name postgres \
		--hostname postgres \
		-e POSTGRES_PASSWORD=password \
		-d postgres
	echo -e "$(yellow)Postgres started$(normal)"

## Stop postgres database
stop-pg:
	@docker stop postgres
	echo -e "$(green)Postgres stopped$(normal)"

## Print postgres db url connection
pg-url: start-pg
	@IP=$$(docker inspect --format '{{ .NetworkSettings.IPAddress }}' postgres)
	@echo "postgres://postgres:password@$$IP:5432/postgres#haystack"

pg-shell:
	@IP=$$(docker inspect --format '{{ .NetworkSettings.IPAddress }}' postgres)
	docker exec -e PGPASSWORD=password -it postgres psql -U postgres -h $$IP

clean-pg: start-pg
	@IP=$$(docker inspect --format '{{ .NetworkSettings.IPAddress }}' postgres)
	docker exec -e PGPASSWORD=password -it postgres psql -U postgres -h $$IP \
	-c 'drop table if exists haystack;drop table if exists haystack_meta_datas;drop table if exists haystack_ts;'

# You can change the password in .env
PGADMIN_USER?=$(USER)@domain.com
PGADMIN_PASSWORD?=password

## Start PGAdmin
start-pgadmin:
	@docker start pgadmin || docker run \
	--name pgadmin \
	-p 8082:80 \
	--link postgres \
    -e 'PGADMIN_DEFAULT_EMAIL=$(PGADMIN_USER)' \
    -e 'PGADMIN_DEFAULT_PASSWORD=$(PGADMIN_PASSWORD)' \
    -d dpage/pgadmin4
	echo -e "$(yellow)PGAdmin started (http://localhost:8082). Use $(cyan)$(PGADMIN_USER)$(yellow) and $(cyan)$(PGADMIN_PASSWORD)$(yellow) $(normal)"

## Stop PGAdmin
stop-pgadmin:
	@docker stop pgadmin
	echo -e "$(green)PGAdmin stopped$(normal)"

## Print all URL
info: api pg-url aws-api

# --------------------------- Distribution
dist/:
	mkdir dist

.PHONY: bdist
dist/$(subst -,_,$(PRJ_PACKAGE))-*.whl: $(REQUIREMENTS) $(PYTHON_SRC) schema.graphql | dist/
	@$(VALIDATE_VENV)
	$(CONDA_PYTHON) setup.py bdist_wheel

## Create a binary wheel distribution
bdist: dist/$(subst -,_,$(PRJ_PACKAGE))-*.whl | dist/

.PHONY: sdist
dist/$(PRJ_PACKAGE)-*.tar.gz: $(REQUIREMENTS) schema.graphql | dist/
	@$(VALIDATE_VENV)
	$(CONDA_PYTHON) setup.py sdist

sdist: dist/$(PRJ_PACKAGE)-*.tar.gz | dist/

.PHONY: dist
## Create a full distribution
dist: bdist sdist
	@echo -e "$(yellow)Package for distribution created$(normal)"

.PHONY: check-twine
## Check the distribution before publication
check-twine: bdist
	$(VALIDATE_VENV)
	twine check \
		$(shell find dist/ -type f \( -name "*.whl" -or -name '*.gz' \) -and ! -iname "*dev*" )

.PHONY: test-twine
## Publish distribution on test.pypi.org
test-twine: dist check-twine
	$(VALIDATE_VENV)
	[[ $$( find dist/ -name "*.dev*" | wc -l ) == 0 ]] || \
		( echo -e "$(red)Add a tag version in GIT before release$(normal)" \
		; exit 1 )
	rm -f dist/*.asc
	echo -e "$(green)Enter the Pypi password$(normal)"
	twine upload --sign --repository-url https://test.pypi.org/legacy/ \
		$(shell find dist/ -type f \( -name "*.whl" -or -name '*.gz' \) -and ! -iname "*dev*" )
	echo -e "To the test repositiry"
	echo -e "$(green)export PIP_INDEX_URL=https://test.pypi.org/simple$(normal)"
	echo -e "$(green)export PIP_EXTRA_INDEX_URL=https://pypi.org/simple$(normal)"

.PHONY: release
## Publish distribution on pypi.org
release: clean check-twine
	@$(VALIDATE_VENV)
	[[ $$( find dist/ -name "*.dev*" | wc -l ) == 0 ]] || \
		( echo -e "$(red)Add a tag version in GIT before release$(normal)" \
		; exit 1 )
	rm -f dist/*.asc
	echo -e "$(green)Enter the Pypi password$(normal)"
	twine upload --sign \
		$(shell find dist -type f \( -name "*.whl" -or -name '*.gz' \) -and ! -iname "*dev*" )

