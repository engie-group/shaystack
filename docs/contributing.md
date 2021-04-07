# Contributing

<!--TOC-->

- [Contributing](#contributing)
  - [Organization](#organization)
  - [Build the application](#build-the-application)
  - [Build in docker container](#build-in-docker-container)
  - [Windows WSL](#windows-wsl)
  - [Tests](#tests)
  - [Use the Makefile to test API locally](#use-the-makefile-to-test-api-locally)
    - [Invoke local API](#invoke-local-api)
    - [GraphQL API](#graphql-api)
  - [Deploy on Docker](#deploy-on-docker)
  - [Deploy the application on AWS Lambda](#deploy-the-application-on-aws-lambda)
  - [Update the application on AWS Lambda](#update-the-application-on-aws-lambda)
  - [Undeploy the application on AWS Lambda](#undeploy-the-application-on-aws-lambda)
  - [Lambda function logs](#lambda-function-logs)
    - [Invoke AWS API](#invoke-aws-api)
    - [Use AWS Time stream](#use-aws-time-stream)
    - [Customize environment variable](#customize-environment-variable)
  - [Cleanup](#cleanup)
- [Validate all the code before commit](#validate-all-the-code-before-commit)
  - [Release](#release)
- [Tips](#tips)
  - [Conversion between haystack filter to SQL](#conversion-between-haystack-filter-to-sql)
  - [Help](#help)
  - [OKTA](#okta)

<!--TOC-->

You are welcome to contribute.

## Organization

The project includes the following files and folders:

- `app` - Code for the application's Flask, GraphQL and Lambda function.
- `AWS_appsync` - Special parameters and information for AWS AppSync
- `docker` - Docker files
- `shaystack` - The generic wrapper between technology and implementation
- `shaystack/providers` - Sample of providers.
- `sample` - Sample haystack file
- `tests` - Unit tests for the application code.
- `*.postman*.json` - script to invoke API with postman
- `Makefile` - All tools to manage the project (Use `make help`)

You can add some environment variable in `.env` file (See `.env.template`).

## Build the application

This project use a `Makefile` (>4.0) to integrate all tools
and [Conda](https://docs.conda.io/projects/conda/en/latest/index.html)
to manage dependencies and others tools and gitflow (https://github.com/nvie/gitflow).

To initialise the Conda environment, use `make configure` and activate the conda environment. Then, it's possible
to `test`, `start-api`, etc. See `make help` to print all major target.

```console
$ git clone https://github.com/engie-group/shaystack.git  
$ cd shaystack
$ make configure
$ conda activate shaystack
$ make help
```

*WARNING: it's not possible to use only virtualenv. Use conda.*

## Build in docker container

For MAC users or for others contexts (CI/CD), it's possible to use a Docker container to build the project.

Use `make docker-build-dmake` to create the docker image `$USER/shaystack-dmake`. Then, you can start this image to
build the project inside a docker container. Add the proposed `alias` in your `.bash_aliases` or
equivalent (`make docker-alias-dmake`)
Now, use `dmake` (Docker make) in place of `make`.

```console
$ dmake test
```

You can use `dmake shell` to start a shell **inside** the container.

*Note: the conda environment is `docker-shaystack`.*

## Windows WSL

Windows WSL accept to use [Windows Docker](https://docs.docker.com/docker-for-windows/install/). Sometime, it's not
possible to invoke the database inside Docker (ping fail), but it's possible to communicate between Dockers. So, to
resolve that, build a new Docker Image, and use it in place of `make start-api`.

```console
$ make docker-build
$ make docker-run
```

## Tests

Tests are defined in the `tests` folder in this project. To run all tests, use `make test`.

```console
$ make test
```

The functional tests try to use the different versions of provider with the same data. To do that, it's necessary to
start different database in docker environment. The AWS token may be refreshed.

If you use OKTA technology, declare this in the environment

```console
$ echo "USE_OKTA=Y" >>.env
$ pip install gimme-aws-creds
```

then

```console
$ make functional-test
```

The tests with a connection with AWS are excluded. To run explicitly these tests, use `make test-aws`.

## Use the Makefile to test API locally

Use the `make start-api` to run the API locally on port 3000 with Flask and the current parameters.

```console
$ HAYSTACK_PROVIDER=shaystack.providers.ping make start-api
```

You can use [Postman](https://www.postman.com/) and the files `SHaystack.postman_collection.json`
and `SHaystack.postman_environment.json` to test and invoke the local API.

You can also start API server in background with `make async-start-api` and close it with `make async-stop-api`.

```console
$ make async-start-api
$ curl http://localhost:3000/haystack/about
$ make async-stop-api
```

### Invoke local API

After started local api, to invoke use `make api-<ops>`

```console
$ make async-start-api
$ make api-about
$ make api-ops
$ make READ_PARAM=?filter=site&limit=1 api-read
$ make HISREAD_PARAMS=?id=@p:demo:r:23a44701-3a62fd7a api-hisRead
$ make async-stop-api
```

To print the local API URL:

```console
$ make api
```

### GraphQL API

To print the local GraphQL API URL:

```console
$ make graphql-api
```

To test the GraphQL API, open this URL with a web browser or use a GraphQL Client with this URL.

```console
$ xdg-open $(make graphql-api)
```

#### Merge GraphQL API

To integrate Haystack GraphQL API inside another GraphQL API,

- Extract the schema

```console
$ make graphql-schema
```

- Insert this schema without the `Query` in you global query,
- insert a link to `app/graphql_model.py!ReadHaystack`
- and deploy your application

#### Use AWS AppSync

It's possible to use AWS AppSync to integrate the Haystack GraphQL API. Read the page [`AppSync.md`](AppSync.md).

## Deploy on Docker

- To build the image use `make docker-build`.
- To run the docker use `make docker-run`
- To start the docker in background use `make async-docker-start` and stop with `make async-docker-stop`
- To remove the image use `make docker-rm`

## Deploy the application on AWS Lambda

To build and deploy application in AWS, run the following in your shell:

```console
$ make aws-deploy
```

## Update the application on AWS Lambda

To build and deploy application in AWS, run the following in your shell:

```console
$ make aws-update
```

## Undeploy the application on AWS Lambda

To undeploy application in AWS, run the following in your shell:

```console
$ make aws-undeploy
```

## Lambda function logs

To simplify troubleshooting, use `make aws-log`

```console
$ make aws-logs
```

### Invoke AWS API

After the deployment, to invoke aws api, use `make aws-api-<path suffix>`

```console
$ make aws-api-about
```

To print the AWS API URL:

```console
$ make aws-api
```

### Use AWS Time stream

You can create a database in *AWS Time Stream* and use the provider
`shaytack.providers.timestream`.

### Customize environment variable

Copy `.env.template` to `.env` and update your local variables These variables are used in `Makefile`, when we start the
api, etc.

## Cleanup

To clean the project, use `make clean`.

# Validate all the code before commit

To validate all the code, use `make validate`. This target check the unit test, the lint, the typing, etc.

## Release

Before to release a version,
You must be capable to sign the package. Create a GPG key and select this key with the variable SIGN_IDENTITY.
```shell
$ gpg --full-generate-key
...
$ export SIGN_IDENTITY=$USER
```

Then, add a new tag for this release candidate (4 numbers and finish with `rc`).

```shell
$ # Commit the version
$ git commit -a
$ # Add a tag for the release candidate
$ git tag vX.Y.Z.0rc
$ # Validate the module
$ make check-twine
```

Then, two solutions:

```shell
$ # Publish the module in test twine repository (https://test.pypi.org/legacy/):
$ make test-twine
```

or push the tag.

```shell
$ git push orgin vX.Y.Z.0rc
```

The github action publish the release in TestPypi if the tag is in form: `vX.Y.Zrc`

It's possible to test a last time all the project, with this release candidate. To do this:

```bash
export PIP_INDEX_URL=https://test.pypi.org/simple
export PIP_EXTRA_INDEX_URL=https://pypi.org/simple
```

Then, you can test the usage with this release candidate.

```shell
$ mkdir $TMP/demo
$ cd $TMP/demo
$ virtualenv -p python3.8 venv
$ source venv/bin/activate
$ pip install 'shaystack[graphql,lambda]'
$ python
import shaystack
...
```

To release a new official public version:

Then
```shell
$ # Commit
$ git commit -a
$ # Start release
$ git flow release start vX.Y.Z
$ ...
$ # Stop the release
$ git flow release stop vX.Y.Z
$ # Publish the release
$ make release
```

# Tips

## Conversion between haystack filter to SQL

The SQL provider must convert the Haystack request to SQL. Because the usage of JSON inside SQL is not normalized, each
database use a different approach. A dedicated conversion is applied for SQLite, Postgres, MySQL and Mongo.

To test the different conversion, you can use a REPL tools.

```console
$ shaystack_repr
```

Then, you can test the conversion for Postgres (`pg`), Sqlite (`sqlite`), MySQL (`mysql`), MongoDB (`mongo`) or
Python (`python`)

```console
Documented commands (type help <topic>):
========================================
help

Undocumented commands:
======================
bye  pg  mysql sqlite mongo

(Cmd) pg site or point
-- site or point
SELECT t1.entity
FROM haystack as t1
WHERE
'2020-10-01T00:00:00+00:00' BETWEEN t1.start_datetime AND t1.end_datetime
AND t1.customer_id='customer'
AND t1.entity ?| array['site', 'point']
LIMIT 1

(Cmd) sqlite site or point
-- site or point
SELECT t1.entity
FROM haystack as t1
WHERE
((datetime('2020-10-01T00:00:00+00:00') BETWEEN datetime(t1.start_datetime) AND datetime(t1.end_datetime)
AND t1.customer_id='customer')
AND (json_extract(json(t1.entity),'$.site') IS NOT NULL
OR json_extract(json(t1.entity),'$.point') IS NOT NULL
)
)
LIMIT 1
(cmd) bye
```

## Help

Don't forget to try `make help`.

## OKTA

If you use Okta technology, you can set in `.env`

```bash
echo USE_OKTA=Y >>.env
```

and customize the file `~/.okta_aws_login_config` with:

* `okta_username = XXXX`
* `preferred_mfa_type = push`
* `write_aws_creds = True`