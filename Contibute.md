# Contribute

You are welcome to contribute.

## Organization

The project includes the following files and folders:

- `app` - Code for the application's Flask, GraphQL and Lambda function.
- `aws appsync` - Special parameters and information for AWS AppSync
- `docker` - Docker files
- `haystackapi` - The generic wrapper between technology and implementation
- `haystackapi/providers` - Sample of providers.
- `sample` - Sample haystack file
- `tests` - Unit tests for the application code.
- `*.postman*.json` - script to invoke API with postman
- `Makefile` - All tools to manage the project (Use `make help`)

You can add some environment variable in `.env` file (See `.env.template`).

## Build the application

This project use a `Makefile` (>4.0) to integrate all tools
and [Conda](https://docs.conda.io/projects/conda/en/latest/index.html)
to manage dependencies and others tools.

To initialise the Conda environment, use `make configure` and activate the conda environment. Then, it's possible
to `test`, `start-api`, etc. See `make help` to print all major target.

Before,

```console
apt install build-essential
```console
$ git clone http://github.com/pprados/haystackapi.git 
$ cd haystackapi
$ make configure
$ conda activate haystackapi
$ make help
```

*WARNING: it's not possible to use only virtualenv.*

## Build in docker container

For MAC users, it's possible to use a Docker container to build the project.

Use `make docker-make-image` to create the image `$USER/haystackapi-make`. Then, you can start this image to build the
project inside a docker container. Then, add the proposed `alias` in your `.bash_aliases` or equivalent.

use `dmake` (Docker make) in place of `make`.

```console
$ dmake test
```

You can use `dmake shell` to start a shell **inside** the container.

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
$ HAYSTACK_PROVIDER=haystackapi.providers.ping make start-api
```

You can use [Postman](https://www.postman.com/) and the files `HaystackAPI.postman_collection.json`
and `HaystackAPI.postman_environment.json` to test and invoke the local API.

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
$ make api-read  # Use READ_PARAM
$ make api-hisRead  # Use HISREAD_PARAM
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

It's possible to use AWS AppSync to integrate the Haystack GraphQL API. Read the
file [`AppSync.md`](aws%20appsync/AppSync.md)
in the folder `aws appsync`.

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
`haytackapi.providers.sql_ts`.

### Customize environment variable

Copy `.env.template` to `.env` and update your local variables These variables are used in `Makefile`, when we start the
api, etc.

## Cleanup

To clean the project, use `make clean`.

# Validate all the code before commit

To validate all the code, use `make validate`. This target check the unit test, the lint, the typing, etc.

## Release

Before to release a version, you must create a new tag for this release candidate.

```shell
$ # Commit the version
$ git commit -a
$ # Add a tag for the release candidate
$ git tag vX.Y.Z-rc
$ # Publish the module in test twine repository (https://test.pypi.org/legacy/):
$ make test-twine
```

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
$ pip install 'haystackapi[graphql,lambda]'
$ python
import haystackapi
...
```

To release a new official public version:

```shell
$ # Commit
$ git commit -a
$ # Tag the version
$ git tag vX.Y.Z
$ # Publish the tag
$ git push origin vX.Y.Z
$ # Publish the release
$ make release
```

# Travis

Travis is configured to track the project. See [here](https://travis-ci.com/github/pprados/haystackapi)

# Tips

## Conversion between haystack filter to SQL

The SQL provider must convert the Haystack request to SQL. Because the usage of JSON inside SQL is not normalized, each
database use a different approach. A dedicated conversion is apply for SQLite and Postgres.

To test the different conversion, you can use a REPL tools.

```console
$ python tests/repl_db.py
```

Then, you can test the conversion for Postgres (`pg`) or Sqlite (`sqlite`)

```console
Documented commands (type help <topic>):
========================================
help

Undocumented commands:
======================
bye  pg  sqlite

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
USE_OKTA=Y
GIMME="echo 0 | gimme-aws-creds --username XXXX"
```
