# Contribute

You are welcome to contribute.

## Organization

The project includes the following files and folders:

- `app` - Code for the application's Flask, GraphQL and Lambda function.
- `aws appsync` - Special parameter and information for AWS AppSync
- `haystackapi` - The generic wrapper between technology and implementation
- `haystackapi/providers` - Sample of providers.
- `sample` - Sample haystack file
- `tests` - Unit tests for the application code.
- `*.postman*.json` - script to invoke API with postman
- `Makefile` - All tools to manage the project (Use `make help`'`)

You can add some environment variable in `.env` file (See `.env.template`).

## Build the application

This project use a `Makefile` (>4.0) to integrate all tools
and [Conda](https://docs.conda.io/projects/conda/en/latest/index.html)
to manage dependencies and others tools.

To initialise the Conda environment, use `make configure` and activate the conda environment. Then, it's possible
to `test`, `start-api`, etc. See `make help` to print all major target.

```bash
git clone --recurse-submodules http://github.com/pprados/haystackapi.git 
make configure
conda activate haystackapi
make test
```

## Tests

Tests are defined in the `tests` folder in this project. To run all tests, use `make test`.

```bash
make test
```

The functional tests, try to use the different versions of provider with the same data. To do that, it's necessary to
start different database in docker environment. Use `make functional-test`

```bash
make functional-test
```

## Use the Makefile to test API locally

Use the `make start-api` to run the API locally on port 3000 with Flask.

You can use [Postman](https://www.postman.com/) and the files `HaystackAPI.postman_collection.json`
and `HaystackAPI.postman_environment.json` to test and invoke the local API.

You can also start API server in background with `make async-start-api` and close it with `make async-stop-api`.

```bash
make async-start-api
curl http://localhost:3000/haystack/about
```

### Invoke local API

After started local api, to invoke api, use `make api-<ops>`

```bash
make async-start-api
make api-about
make api-read
```

To print the local API URL:

```bash
make api
```

### GraphQL API

To print the local GraphQL API URL:

```bash
make graphql-api
```

To test the GraphQL API, open this URL with a web browser or use a GraphQL Client with this URL.

#### Merge GraphQL API

To integrate Haystack GraphQL API inside another GraphQL API,

- Extract the schema

```bash
make graphql-schema
```

- Insert this schema without the `Query`
- In you query, insert a link to `app/graphql_model.py!ReadHaystack`
- And deploy your application

#### Use AWS AppSync

It's possible to use AWS AppSync to integrate the Haystack GraphQL API. Read the file `README.md` in the
folder `aws appsync`.

## Deploy the application on AWS Lambda

To build and deploy application in AWS, run the following in your shell:

```bash
make aws-deploy
```

## Update the application on AWS Lambda

To build and deploy application in AWS, run the following in your shell:

```bash
make aws-update
```

## Undeploy the application on AWS Lambda

To undeploy application in AWS, run the following in your shell:

```bash
make aws-undeploy
```

## Lambda function logs

To simplify troubleshooting, use `make aws-log`

```bash
make aws-logs
```

### Invoke AWS API

After deployment, to invoke aws api, use `make aws-api-<path suffix>`

```bash
make aws-api-about
```

To print the AWS API URL:

```bash
make aws-api
```

### Customize environment variable

Copy `.env.template` to `.env` and update your local variables These variables are used in `Makefile`, when we start the
api, etc.

## Cleanup

To clean the project, use `make clean`.

## Tips

If you use Okta technology, you can set in `.env`

```bash
GIMME="echo 0 | gimme-aws-creds --username XXXX"
```
