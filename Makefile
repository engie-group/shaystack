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
PYTHON_VERSION:=3.7
PRJ_PACKAGE:=$(PRJ)
VENV ?= $(PRJ)
CONDA_BASE:=$(shell AWS_PROFILE=default conda info --base)
CONDA_PACKAGE:=$(CONDA_PREFIX)/lib/python$(PYTHON_VERSION)/site-packages
CONDA_PYTHON:=$(CONDA_PREFIX)/bin/python
CONDA_ARGS?=
PIP_PACKAGE:=$(CONDA_PACKAGE)/$(PRJ_PACKAGE).egg-link
PIP_ARGS?=
ENVS_JSON?=_envs.json
HSZINC_VERSION:=*
OKTA_USERNAME?=
export ROOT_DIR:=$$PWD
export AWS_DEFAULT_REGION:=$(AWS_REGION)
AWS_S3_ENDPOINT?=https://s3.$(AWS_REGION).amazonaws.com
AWS_API_HOME=https://$(shell aws apigateway get-rest-apis --output text --profile $(AWS_PROFILE) --region $(AWS_REGION) --query 'items[?name==`$(AWS_STACK)`].id').execute-api.$(AWS_REGION).amazonaws.com/Prod
AWS_ACCESS_KEY=$(shell aws configure get aws_access_key_id)
AWS_SECRET_KEY=$(shell aws configure get aws_secret_access_key)
MINIO_HOME=$(HOME)/.minio

SAM_TEMPLATE=-t template.yaml
SAM_DEPLOY_PARAMETERS?=$(SAM_TEMPLATE)
SAM_BUILD_PARAMETERS?=-s . $(SAM_TEMPLATE)
SAM_ENV?=--env-vars $(ENVS_JSON)

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


# -------------------------------------- ENV
# Convert .env to json
_envs.json: .env
	@source .env
	cat >_envs.json <<ENVS
	{
	"Parameters": {
		"LOGLEVEL": "$${LOGLEVEL}",
		"DEBUGGING": "false",
		"NOCOMPRESS": "true",
		"HAYSTACK_PROVIDER": "$${HAYSTACK_PROVIDER}",
		"HAYSTACK_URL": "$${HAYSTACK_URL}"
		}
	}
	ENVS

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
$(PIP_PACKAGE): $(CONDA_PYTHON) \
	src/requirements.txt \
	layers/base/requirements.txt \
	layers/parquet/requirements.txt | .git # Install pip dependencies
	@$(VALIDATE_VENV)
	echo -e "$(cyan)Install build dependencies ... (may take minutes)$(normal)"
	pip install -r src/requirements.txt
	find layers -name requirements.txt -exec pip install -r {} \;
	conda install -c conda-forge -c anaconda -y \
		awscli aws-sam-cli make \
		pytype ninja flake8 pylint pytest jq

ifeq ($(USE_OKTA),Y)
	pip install gimme-aws-creds
endif
	echo -e "$(cyan)Build dependencies updated$(normal)"
	echo -e "$(cyan)Install project dependencies ...$(normal)"
	pip install -r src/requirements.txt
	pip install -r layers/base/requirements.txt
	pip install -r layers/parquet/requirements.txt
	# Install the fork of hszinc
	pip install -e hszinc
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
	@rm -rf bin/* .aws-sam .mypy_cache .pytest_cache .start build nohup.out dist .make-* .pytype out.json \
		_envs.json

.PHONY: clean-all
# Clean all environments
clean-all: clean remove-venv
	@rm libsnappy-$(PYTHON_VERSION).so


## Run bash in an AWS lambda image
docker-bash:
	docker run -it lambci/lambda:build-python$(PYTHON_VERSION) bash

tests/data: tests/data/grid.json tests/data/id1234.parquet

# -------------------------------------- Build

# Template to build custom runtime.
# See https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/building-custom-runtimes.html
# See https://github.com/awslabs/aws-sam-cli/blob/de8ad8e78491ebfa884c02c3439c6bcecd08516b/designs/build_for_layers.md
build-HSZincLayer: hszinc/dist/hszinc-*.whl template.yaml Makefile
	@if [[ -z "$(ARTIFACTS_DIR)" ]]
	then
		@$(VALIDATE_VENV)
		echo -e "$(green)Build Lambda HSZincLayer...$(normal)"
		umask 0
		@sam build $(SAM_BUILD_PARAMETERS) HSZincLayer
	else
		# executed inside `sam build`
		# The variable OLDPWD is set to the project home directory
		umask 0
		mkdir -p "$(ARTIFACTS_DIR)/python"
		python -m pip install $(ROOT_DIR)/hszinc/dist/hszinc-$(HSZINC_VERSION)-py3-none-any.whl -t "$(ARTIFACTS_DIR)/python"
	fi


# Download lambda version of compiled library
libsnappy-$(PYTHON_VERSION).so:
	@echo -e "$(green)Download lambda version of libsnappy-$(PYTHON_VERSION).so...$(normal)"
	docker run --rm -v $$(pwd):/foo -w /foo lambci/lambda:build-python$(PYTHON_VERSION) \
	/bin/bash -c "yum install -y snappy-devel ; cp /usr/lib64/libsnappy.so.1 /foo/libsnappy-$(PYTHON_VERSION).so"
	echo -e "$(green)To update the owner of libsnappy-$(PYTHON_VERSION).so we must have a root access$(normal)"
	echo -e "Ask the permission to change owner of libsnappy-$(PYTHON_VERSION).so..."
	sudo chown $(USER):$(USER) libsnappy-$(PYTHON_VERSION).so
	chmod 600 libsnappy-$(PYTHON_VERSION).so

build-ParquetLayer: layers/parquet/requirements.txt template.yaml Makefile libsnappy-$(PYTHON_VERSION).so
	@if [[ -z "$(ARTIFACTS_DIR)" ]]
	then
		@$(VALIDATE_VENV)
		echo -e "$(green)Build Lambda HSZincLayer...$(normal)"
		umask 0
		@sam build $(SAM_BUILD_PARAMETERS) HSZincLayer
	else
		# executed inside `sam build`
		umask 0
		mkdir -p "$(ARTIFACTS_DIR)/python"
		python -m pip install -r layers/parquet/requirements.txt -t "$(ARTIFACTS_DIR)/python"
		# See https://aws.amazon.com/fr/blogs/compute/working-with-aws-lambda-and-lambda-layers-in-aws-sam/
		mkdir -p "$(ARTIFACTS_DIR)/lib"
		cp libsnappy-$(PYTHON_VERSION).so "$(ARTIFACTS_DIR)/lib/libsnappy.so.1"
	fi


build-About: hszinc/dist/hszinc-*.whl
	@if [[ -z "$(ARTIFACTS_DIR)" ]]
	then
		@$(VALIDATE_VENV)
		echo -e "$(green)Build Lambda HSZincLayer...$(normal)"
		umask 0
		@sam build $(SAM_BUILD_PARAMETERS) HSZincLayer
	else
		# executed inside `sam build`
		umask 0
		mkdir -p "$(ARTIFACTS_DIR)/python"
		python -m pip install -r src/requirements.txt -t "$(ARTIFACTS_DIR)/python"
#		cp -R src "$(ARTIFACTS_DIR)"
#		cp libsnappy.so "$(ARTIFACTS_DIR)"
	fi


## Build specific lambda function (ie. build-About)
build-%: template.yaml $(REQUIREMENTS) $(PYTHON_SRC) template.yaml libsnappy-$(PYTHON_VERSION).so
	@$(VALIDATE_VENV)
	echo -e "$(green)Build Lambda $*...$(normal)"
	umask 0
	@sam build $(SAM_BUILD_PARAMETERS) $*

.PHONY: dist build
.aws-sam/build: $(REQUIREMENTS) $(PYTHON_SRC) hszinc template.yaml src/requirements.txt \
	layers/base/requirements.txt layers/parquet/requirements.txt Makefile
	@$(VALIDATE_VENV)
	echo -e "$(green)Build Lambdas...$(normal)"
	umask 0
	sam build $(SAM_BUILD_PARAMETERS)
	find .aws-sam -type f -exec chmod 644 {} \;
	find .aws-sam -type d -exec chmod 755 {} \;

## Build all lambda function
build: .aws-sam/build

# -------------------------------------- Invoke
.PHONY: invoke-*
## Build and invoke lambda function in local with associated events (ie. invoke-About)
invoke-%: $(ENVS_JSON) .aws-sam/build
	@$(VALIDATE_VENV)
	sam local invoke --env-vars $(ENVS_JSON) $* -e events/$*_event.json >.out.json
	jq -r <.out.json
	echo -e "\n$(green)Body:$(normal)"
	jq -r '.body' <.out.json
	rm .out.json

.PHONY: start-api async-start-api async-stop-api
## Start api
start-api: $(ENVS_JSON) .aws-sam/build
	@$(VALIDATE_VENV)
	@[ -e .start/start-api.pid ] && $(MAKE) async-stop-api || true
	sam local start-api --env-vars $(ENVS_JSON)

# Start local api emulator in background
async-start-api: $(ENVS_JSON) .aws-sam/build
	@$(VALIDATE_VENV)
	@[ -e .start/start-api.pid ] && echo -e "$(orange)Local API was allready started$(normal)" && exit
	mkdir -p .start
	nohup sam local start-api --env-vars $(ENVS_JSON) >.start/start-api.log 2>&1 &
	echo $$! >.start/start-api.pid
	sleep 0.5
	tail .start/start-api.log
	echo -e "$(orange)Local API started$(normal)"

# Stop local api emulator in background
async-stop-api:
	@$(VALIDATE_VENV)
	@[ -e .start/start-api.pid ] && kill `cat .start/start-api.pid` || true && echo -e "$(green)Local API stopped$(normal)"
	rm -f .start/start-api.pid

.PHONY: api
## Print API URL
api:
	@grep -oh 'https://$${ServerlessRestApi}[^"]*' template.yaml | \
	sed 's/https:..$${ServerlessRestApi}.*\//http:\/\/locahost:3000\//g'

## Invoke local API (eg. make build api-About)
api-%:
	@$(VALIDATE_VENV)
	GET_POST=$$(jq -r '.httpMethod' events/$*_event.json)
	ops=$*
	if [[ $$GET_POST == "GET" ]]
	then
		curl -H "Accept: text/zinc" \
			"http://localhost:3000/$${ops,}"$(PARAMS)
	else
		# Add trailing CR
		BODY="$$(jq -r '.body' <events/Read_event.json)"$$'\n'
		curl -H "Accept:text/zinc" \
			-H "Content-Type:text/zinc" \
			-X POST \
			--data-binary "$${BODY}" \
			"http://localhost:3000/$${ops,}"$(PARAMS)
	fi


.PHONY: start-lambda async-start-lambda async-stop-lambda
## Start lambda local emulator
start-lambda: $(ENVS_JSON) .aws-sam/build
	@$(VALIDATE_VENV)
	[ -e .start/start-lambda.pid ] && $(MAKE) async-stop-lambda || true
	AWS_DEFAULT_PROFILE=$(AWS_PROFILE) sam local start-lambda --env-vars $(ENVS_JSON)
	sleep 2

# Start lambda local emulator in background
async-start-lambda: $(ENVS_JSON) .aws-sam/build
	@$(VALIDATE_VENV)
	[ -e .start/start-lambda.pid ] && echo -e "$(orange)Local Lambda was allready started$(normal)" && exit
	mkdir -p .start
	nohup sam local start-lambda --env-vars $(ENVS_JSON) >.start/start-lambda.log 2>&1 &
	echo $$! >.start/start-lambda.pid
	sleep 2
	tail .start/start-lambda.log
	echo -e "$(orange)Local Lambda was started$(normal)"

# Stop lambda local emulator in background
async-stop-lambda:
	@$(VALIDATE_VENV)
	[ -e .start/start-lambda.pid ] && kill `cat .start/start-lambda.pid` >/dev/null || true && echo -e "$(green)Local Lambda stopped$(normal)"
	rm -f .start/start-lambda.pid

# -------------------------------------- Minio
# https://min.io/
# See https://docs.min.io/docs/how-to-use-aws-sdk-for-python-with-minio-server.html
.minio:
	mkdir -p .minio

start-minio: $(ENVS_JSON) .minio
	docker run -p 9000:9000 \
	-e "MINIO_ACCESS_KEY=$(AWS_ACCESS_KEY)" \
	-e "MINIO_SECRET_KEY=$(AWS_SECRET_KEY)" \
	-v  "$(MINIO_HOME):/data" \
	minio/minio server /data

async-stop-minio:
	@$(VALIDATE_VENV)
	[ -e .start/start-minio.pid ] && kill `cat .start/start-minio.pid` >/dev/null || true && echo -e "$(green)Local Minio stopped$(normal)"
	rm -f .start/start-minio.pid

async-start-minio: .minio .aws-sam/build
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
async-stop: async-stop-api async-stop-lambda async-stop-minio

# -------------------------------------- AWS
# Initialise okta with default values
#https://e6esmeduqa.execute-api.eu-west-3.amazonaws.com/Prod/about
# FIXME: init okta
ifeq ($(USE_OKTA),Y)
~/.okta_aws_login_config: .okta_aws_login_config
	@touch ~/.okta_aws_login_config
	grep -Fxq "[haystackapi]" ~/.aws/config || echo -e '[carbonapi]\nregion = $(AWS_REGION)' >>~/.aws/config
	grep -Fxq "[haystackapi]" ~/.aws/credentials || echo '[carbonapi]' >>~/.aws/credentials
	grep -Fxq "[haystackapi]" ~/.okta_aws_login_config || cat .okta_aws_login_config >>~/.okta_aws_login_config
	echo -e "$(green)Initialize ~/.okta_aws_login_config file$(normal)"
endif

ifeq ($(USE_OKTA),Y)
.PHONY: aws-update-token
# Update the AWS Token
aws-update-token: ~/.okta_aws_login_config
	@echo -e "$(green)Use AWS profile '$(AWS_PROFILE)$(normal)'"
	@aws sts get-caller-identity >/dev/null 2>/dev/null || gimme-aws-creds $(OKTA_USERNAME) --profile $(AWS_PROFILE)
endif

.PHONY: aws-deploy
## Deploy lambda functions
aws-deploy: .make-sam-validate
	$(VALIDATE_VENV)
ifeq ($(USE_OKTA),Y)
	gimme-aws-creds $(OKTA_USERNAME) --profile $(AWS_PROFILE)
endif
	sam deploy $(SAM_DEPLOY_PARAMETERS) \
	  --debug \
	  --profile $(AWS_PROFILE) \
	  --region $(AWS_REGION) \
	  $(SAM_TEMPLATE)  \
	  --no-confirm-changeset  \
	  --parameter-overrides 'HaystackProvider=$(HAYSTACK_PROVIDER) HaystackURL=$(HAYSTACK_URL) LOGLEVEL=$(LOGLEVEL)'
	echo -e "$(green)Lambdas are deployed$(normal)"

.PHONY: aws-clean-stack
## Remove AWS Stack
aws-clean-stack:
	aws cloudformation delete-stack --stack-name $(AWS_STACK) --region $(AWS_REGION)

##  Invoke lambda function via aws cli (ie. aws-invoke-About)
aws-invoke-%: .aws-sam/build
	$(VALIDATE_VENV)
	FUNCTION=$$(aws cloudformation describe-stack-resource \
		--stack-name $(AWS_STACK) \
		--profile $(AWS_PROFILE) \
		--region $(AWS_REGION) \
		--logical-resource-id $* \
		--query 'StackResourceDetail.PhysicalResourceId' --output text)
	aws lambda invoke --function-name $$FUNCTION \
		--payload file://events/$*_event.json \
		--profile $(AWS_PROFILE) \
		--region $(AWS_REGION) \
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

## Invoke API via AWS (eg. make aws-api-About)
aws-api-%:
	@GET_POST=$$(jq -r '.httpMethod' events/$*_event.json)
	ops=$*
	if [[ $$GET_POST == "GET" ]]
	then
		curl -H "Accept: text/zinc" \
			"$(AWS_API_HOME)/$${ops,}"
	else
		curl -H "Accept:text/zinc" \
			-H "Content-Type:text/zinc" \
			-X POST \
			--data-binary @<(jq -r '.body' <events/$*_event.json) \
			"$(AWS_API_HOME)/$${ops,}"
	fi

## Print AWS logs
aws-logs-%:
	@$(VALIDATE_VENV)
	sam $(SAM_TEMPLATE) logs --profile $(AWS_PROFILE) --region $(AWS_REGION) -n $* --stack-name $(AWS_STACK) --tail


## Print project variables
dump-params:
	@echo PRJ=$(PRJ)
	echo HAYSTACK_PROVIDER=$(HAYSTACK_PROVIDER)
	echo HAYSTACK_URL=$(HAYSTACK_URL)
	echo AWS_STACK=$(AWS_STACK)
	echo AWS_PROFILE=$(AWS_PROFILE)
	echo AWS_REGION=$(AWS_REGION)


## Print AWS stack info
aws-info:
	@$(VALIDATE_VENV)
	aws cloudformation describe-stacks --region $(AWS_REGION) --profile $(AWS_PROFILE) --stack-name $(AWS_STACK)
# -------------------------------------- Tests
.PHONY: unit-test
.make-unit-test: $(REQUIREMENTS) $(PYTHON_SRC) Makefile .env
	@$(VALIDATE_VENV)
	PYTHONPATH=./src python -m pytest -m "not functional" -s tests $(PYTEST_ARGS)
	date >.make-unit-test
## Run unit test
unit-test: .make-unit-test

.PHONY: functional-test
.make-functional-test: $(REQUIREMENTS) $(PYTHON_SRC) .aws-sam/build Makefile envs.json tests/data
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


.make-sam-validate:  aws-update-token template.yaml
	@echo -e "$(cyan)Validate template.yaml...$(normal)"
	@sam validate $(SAM_TEMPLATE)
	@date >.make-sam-validate

.PHONY: validate
.make-validate: .make-typing .make-lint .make-test .make-sam-validate
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

# TODO: Find how to use debugger
# See https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-using-debugging-python.html
debugging:
	@$(VALIDATE_VENV)
	# Install dependencies
	pip install -r src/requirements.txt -t build/
	pip install -r layers/base/requirements.txt -t build/
	pip install -r layers/parquet/requirements.txt -t build/
	# Install ptvsd library for step through debugging
	pip install ptvsd -t build/
	cp $(PRJ)/*.py build/
