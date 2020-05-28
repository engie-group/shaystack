# alpha-carbon-api

CarbonAPI is an API to add CO2e in a [Haystack Grid](https://project-haystack.org/doc/Grids).
Theses API can negotiate:
- Request format (zinc or json)
- Request encoding (`Content-Encoding: gzip`)
- Response format (`Accept: zinc, json`)
- Compressed format (`Accept-Encoding: gzip`)

implements theses Haystack [operations](https://project-haystack.org/doc/Rest):
- [About](https://project-haystack.org/doc/Ops#about)
- [Ops](https://project-haystack.org/doc/Ops#ops)
- [Formats](https://project-haystack.org/doc/Ops#formats)

and add one operation
- extend_with_co2e

This new operation receive a grid, and extend this grid with CO2e when it's possible. Then, return this extended grid.

## Summary
This project contains source code and supporting files for a CarbonAPI application 
that you can deploy with the SAM CLI. It includes the following files and folders.

- carbonapi - Code for the application's Lambda function.
- events - Invocation events that you can use to invoke the function.
- tests - Unit tests for the application code. 
- template.yaml - A template that defines the application's AWS resources.
- Makefile - All tools to manage the project (Use 'make help')

The application uses several AWS resources, including Lambda functions and an API Gateway API. 
These resources are defined in the `template.yaml` file in this project. 

## Deploy the application

The Serverless Application Model Command Line Interface (SAM CLI) is an extension of the AWS CLI that 
adds functionality for building and testing Lambda applications. It uses Docker to run your functions 
in an Amazon Linux environment that matches Lambda. It can also emulate your application's 
build environment and API.

To use the SAM CLI, you need the following tools.

* SAM CLI - [Install the SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
* [Python 3 installed](https://www.python.org/downloads/)
* Docker - [Install Docker community edition](https://hub.docker.com/search/?type=edition&offering=community)

To build and deploy your application for the first time, run the following in your shell:

```bash
sam build --use-container
sam deploy --guided
```

The first command will build the source of your application. The second command will package and deploy your application to AWS, with a series of prompts:

* **Stack Name**: The name of the stack to deploy to CloudFormation. This should be unique to your account and region, and a good starting point would be something matching your project name.
* **AWS Region**: The AWS region you want to deploy your app to.
* **Confirm changes before deploy**: If set to yes, any change sets will be shown to you before execution for manual review. If set to no, the AWS SAM CLI will automatically deploy application changes.
* **Allow SAM CLI IAM role creation**: Many AWS SAM templates, including this example, create AWS IAM roles required for the AWS Lambda function(s) included to access AWS services. By default, these are scoped down to minimum required permissions. To deploy an AWS CloudFormation stack which creates or modified IAM roles, the `CAPABILITY_IAM` value for `capabilities` must be provided. If permission isn't provided through this prompt, to deploy this example you must explicitly pass `--capabilities CAPABILITY_IAM` to the `sam deploy` command.
* **Save arguments to samconfig.toml**: If set to yes, your choices will be saved to a configuration file inside the project, so that in the future you can just re-run `sam deploy` without parameters to deploy changes to your application.

You can find your API Gateway Endpoint URL in the output values displayed after deployment.

## Use the Makefile to build and test locally

Build your application with the `make build` command.

```bash
$ make build
```

To build a specific lambda, use `make build-<name>` command.

```bash
$ make build-ExtendWithCO2e
$ make build-CarbonAPILayer
```

The SAM CLI installs dependencies defined in `carnonapi/requirements.txt`, creates a deployment package, 
and saves it in the `.aws-sam/build` folder.

Test a single function by invoking it directly with a test event. An event is a JSON document 
that represents the input that the function receives from the event source. 
Test events are included in the `events` folder in this project.

Run functions locally and invoke them with the `make invoke-<name>` command.

```bash
$ # Same as `sam local invoke --env-vars envs.json About -e events/About_event.json`
$ make invoke-About 
```

The SAM CLI can also emulate your application's API. Use the `make start-api` to run the API locally on port 3000.
TODO: util ? refresh ? You can start API server in background with `make async-start-api` and close with `make async-stop-api`.

```bash
$ make async-start-api
$ curl http://localhost:3000/
```

The SAM CLI reads the application template to determine the API's routes and the functions that they invoke. 
The `Events` property on each function's definition includes the route and method for each path.

```yaml
      Events:
        ExtendWithCO2e:
          Type: Api
          Properties:
            Path: /extend_with_co2e
            Method: post
```

## Add a resource to the application
Extend the `carbonapi/requirement.txt` and run `make build`.

## Fetch, tail, and filter Lambda function logs
To simplify troubleshooting, SAM CLI has a command called `sam logs`. `sam logs` lets you fetch logs generated 
by your deployed Lambda function from the command line. In addition to printing the logs on the terminal, 
this command has several nifty features to help you quickly find the bug.

`NOTE`: This command works for all AWS Lambda functions; not just the ones you deploy using SAM.

```bash
$ sam logs -n ExtendWithCO2e --stack-name alpha-carbon-api --tail
```

You can find more information and examples about filtering Lambda function logs in the 
[SAM CLI Documentation](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-logging.html).

## Unit tests

Tests are defined in the `tests` folder in this project. 
To run all tests, use `make test`. You can select unit or functional test with `make unit-test` 
or `make functional-test`. The functional-test call the API via a local lambda emulator, 
after starting lamnda server in background (`make async-start-lambda`).

```bash
$ make test
```

## Cleanup

To cleanup the project, use `make clean`.

## Resources

See the [AWS SAM developer guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam.html) 
for an introduction to SAM specification, the SAM CLI, and serverless application concepts.

