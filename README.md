# alpha-carbon-api

Haystackapi is a skeleton AWS Lambda API to implement [Haystack Rest API](https://project-haystack.org/doc/Rest).
Theses API can negotiate:
- Request format (`Content-Type: text/zinc` or `application/json`)
- Request encoding (`Content-Encoding: gzip`)
- Response format (`Accept: text/zinc, application/json`)
- Response encoding (`Accept-Encoding: gzip`)

The code implements all Haystack [operations](https://project-haystack.org/doc/Rest):
- [about](https://project-haystack.org/doc/Ops#about)
- [ops](https://project-haystack.org/doc/Ops#ops)
- [formats](https://project-haystack.org/doc/Ops#formats)
- [read](https://project-haystack.org/doc/Ops#read)
- [nav](https://project-haystack.org/doc/Ops#nav)
- [watchSub](https://project-haystack.org/doc/Ops#watchSub)
- [watchUnsub](https://project-haystack.org/doc/Ops#watchUnsub)
- [watchPoll](https://project-haystack.org/doc/Ops#watchPoll)
- [pointWrite](https://project-haystack.org/doc/Ops#pointWrite)
- [hisRead](https://project-haystack.org/doc/Ops#hisRead)
- [hisWrite](https://project-haystack.org/doc/Ops#hisWrite)
- [invokeAction](https://project-haystack.org/doc/Ops#invokeAction)

## Summary
This project contains source code and supporting files for a Haystack application 
that you can deploy with the [SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam.html). 

To create your custom Haystack API:
- fork this projet,
- checkout an new branch
- update the file `Project.variables` 
- and/or create a new provider.

You can update the code with a `git rebase`.

The project includes the following files and folders:
- src - Code for the application's Lambda function.
- src/providers - Sample of providers.
- events - Invocation events that you can use to invoke the function.
- tests - Unit tests for the application code. 
- hszinc - Git submodule to extend the hszinc project. 
- layers - A lamdda layers shared with other lambdas 
- `template.yaml` - A template that defines the application's AWS resources.
- `Makefile` - All tools to manage the project (Use 'make help')

You can add some environement variable in `.env` file.

The application uses several AWS resources, including Lambda functions and an API Gateway. 
These resources are defined in the `template.yaml` file. 

## Providers
Different sample of provider are proposed. You can add a new one with a subclass of `providers.HaystackInterface`.
Then, you can implement only the method you want. The others methods are automatically exclude in 
the [`../ops`](https://project-haystack.org/doc/Ops#ops) operation.

To select a provider, add the environment variable `HAYSTACK_PROVIDER` in the lambda context.

To add a new provider, *fork the project* and add a provider in the `providers` directory. You can update others 
parameters in `Project.variables` (`HAYSTACK_PROVIDER`, `AWS_STACK`, AWS_PROFILE`, `AWS_REGION` `AWS_STACK`, ...)

### Provider
Use `HAYSTACK_PROVIDER=providers.ping.Provider` to use this provider.
It's a very simple provider, with a tiny implementation of all haystack operation.

### Provider
Use `HAYSTACK_PROVIDER=providers.url.Provider` to use this provider.
Add the variable `HAYSTACK_URL=<url>` to expose an Haystack file via the Haystack protocol.
The methods `/read` and `/his_read` was implemented.
The `<url>` may have the classic form (`http://...`, `ftp://...`) or can reference an S3 file (`s3://`).
The time series to manage history must be referenced in the entity, with the `hisURI` tag.
This URI may be relative and must be in parquet format.

## Build the application
This project use a `Makefile` (>4.0) for integrate all tools, docker
and [Conda](https://docs.conda.io/projects/conda/en/latest/index.html
to manage dependencies and others tools.

To initialise the Conda environment, use `make configure` and activate the conda environment.
Then, it's possible to `test`, `build`, etc. See `make help` to print all major target.
```bash
git clone --recurse-submodules http://github.com/pprados/haystackapi.git 
make configure
conda activate haystackapi
make test
```

## Use the Makefile to build and test locally

Build your application with the `make build` command.
```bash
make build
```

To build a specific lambda, use `make build-<name>` command.
```bash
make build-Read
make build-BaseLayer
```

The build process install dependencies defined in `src/requirements.txt`,
`layouts/base/requirements.txt` and `layouts/parquet/requirements.txt` , 
creates some deployments packages and saves them in the `.aws-sam/build` folder.

Test a single function by invoking it directly with a test event. An event is a JSON document 
that represents the input that the function receives from the event source. 
Test events are included in the `events` folder in this project.

The SAM CLI can emulate the AWS Lambda API. Use the `make start-lambda` to run the Lambda server locally on port 3001.
```bash
make start-lambda
```
You can start Lambda server in background with `make async-start-lambda` and close it with `make async-stop-lambda`.

Run functions locally and invoke them with the `make invoke-<name>` command. The lambda server is started in background.
```bash
# Same as `sam local invoke --env-vars envs.json About -e events/About_event.json`
make invoke-About 
```

After deployed the lambda functions invoke the remote lambda with the `make aws-invoke-<name>` command.
```bash
make aws-invoke-About 
```


The SAM CLI can also emulate the application's API. Use the `make start-api` to run the API locally on port 3000.
You can use [Postman](https://www.postman.com/) and the file `CarbonAPI v2.0.postman_collection.json` to
test and invoke the local API.

You can also start API server in background with `make async-start-api` and close it with `make async-stop-api`.

```bash
make async-start-api
# curl http://localhost:3000/about
make build api-About
```

The SAM CLI reads the application template to determine the API's routes and the functions that they invoke. 
The `Events` property on each function's definition includes the route and method for each path.

```yaml
  Events:
    Read:
      Type: Api
      Properties:
        Path: /read
        Method: post
```

## Deploy the application

Before deploying the application, you must have:
- an admin account WITH password (Ask the Engie support +33977401002 to activate the « Okta Sync Flag » to 1
for your XXXX-A engie account)
- a token created by *Gimme aws cred*

For more information, read [this](https://confluence.tools.digital.engie.com/display/CDHA/AWS+CLI+installation+and+CDH+access+testing)

With command line, select the correct aws profile with:
```bash
export AWS_PROFILE=haystackapi
```

To build and deploy CarbonAPI run the following in your shell:
```bash
make aws-deploy
```
If you receive an Expired Token error, retry. The token will be updated (or use `make aws-update-token`)

To deploy a specific lambda function
```bash
make build-About deploy
```

## Add a resource to the application
Extend the `events/requirement.txt` and run `make build`.

## Lambda function logs
To simplify troubleshooting, use `make log-<name>`

```bash
make aws-logs-About
```

You can find more information and examples about filtering Lambda function logs in the 
[SAM CLI Documentation](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-logging.html).

## Tests

Tests are defined in the `tests` folder in this project. 
To run all tests, use `make test`. You can select unit or functional test with `make unit-test` 
or `make functional-test`. The functional-test call the API via a local lambda emulator, 
after starting lambda server in background (`make async-start-lambda`) or download s3 files.
```bash
make test
make unit-test
make functional-test
```

### Invoke local API
After started local api, to invoke api, use `make api-<Lambda name>`
```bash
make async-start-api
make api-About
make api-Read
```
To print the local API URL:
```bash
make api
```

### Invoke AWS lambda directly
After deployment, to invoke aws lambda, use `make aws-invoke-<Lambda name>`
```bash
make aws-invoke-About
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
Copy `.env.template` to `.env` and update your local variables
Theses variables are used in Makefile, when we start the api, etc.

## Cleanup
To cleanup the project, use `make clean`.

## Resources
See the [AWS SAM developer guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam.html) 
for an introduction to SAM specification, the SAM CLI, and serverless application concepts.
