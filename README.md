# alpha-carbon-api

CarbonAPI is an API to add CO2e in a [Haystack Grid](https://project-haystack.org/doc/Grids).
Theses API can negotiate:
- Request format (`Content-Type: zinc` or `json`)
- Request encoding (`Content-Encoding: gzip`)
- Response format (`Accept: zinc, json`)
- Response encoding (`Accept-Encoding: gzip`)

The code implements theses Haystack [operations](https://project-haystack.org/doc/Rest):
- [About](https://project-haystack.org/doc/Ops#about)
- [Ops](https://project-haystack.org/doc/Ops#ops)
- [Formats](https://project-haystack.org/doc/Ops#formats)

and add one specific operation
- extend_with_co2e

This new operation receive a grid, and extend this grid with CO2e when it's possible.

## Summary
This project contains source code and supporting files for a CarbonAPI application 
that you can deploy with the SAM CLI. It includes the following files and folders.

- carbonapi - Code for the application's Lambda function.
- events - Invocation events that you can use to invoke the function.
- tests - Unit tests for the application code. 
- hszinc - Git submodule to patch the hszinc project. 
- layer - A lamb    da layer shared by other lambdas 
- template.yaml - A template that defines the application's AWS resources.
- Makefile - All tools to manage the project (Use 'make help')

The application uses several AWS resources, including Lambda functions and an API Gateway API. 
These resources are defined in the `template.yaml` file in this project. 


## Build the application
This project use a `Makefile` (>4.0) for integrate all tools and [Conda](https://docs.conda.io/projects/conda/en/latest/index.html
to manage dependencies and tools.

To initialise the Conda environment, use `make configure`. Then activate the conda environment.
Then, it's possible to test, build, etc. See `make help` to print all major target.
```bash
git clone --recurse-submodules http://github.tools.digital.engie.com/PR6075/alpha-carbon-api.git 
make configure
conda activate carbonapi
make test
```
## Use the Makefile to build and test locally

Build your application with the `make build` command.
```bash
make build
```

To build a specific lambda, use `make build-<name>` command.
```bash
make build-ExtendWithCO2e
make build-BaseLayer
```

The build process installs dependencies defined in `carnonapi/requirements.txt`
and `layout/requirements.txt`, creates some deployments packages 
and saves it in the `.aws-sam/build` folder.

Test a single function by invoking it directly with a test event. An event is a JSON document 
that represents the input that the function receives from the event source. 
Test events are included in the `events` folder in this project.

Run functions locally and invoke them with the `make invoke-<name>` command.
```bash
# Same as `sam local invoke --env-vars envs.json About -e events/About_event.json`
make invoke-About 
```

Run functions remotelly and invoke them with the `make aws-invoke-<name>` command.
```bash
make aws-invoke-About 
```

The SAM CLI can also emulate your application's API. Use the `make start-api` to run the API locally on port 3000.
You can use [Postman](https://www.postman.com/) and the file `CarbonAPI v2.0.postman_collection.json` to
test and invoke the local API.

TODO: util ? refresh ? You can start API server in background with `make async-start-api` and close with `make async-stop-api`.

```bash
make async-start-api
curl http://localhost:3000/about
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

## Deploy the application

Before deploying the application, you must have:
- an admin account WITH password (Ask the support +33977401002 to activate the « Okta Sync Flag » to 1
for your XXXX-A account)
- a token created by Gimme aws cred

For more information, read [this](https://confluence.tools.digital.engie.com/display/CDHA/AWS+CLI+installation+and+CDH+access+testing)

With command line, select the correct aws profile with:
```bash
export AWS_DEFAULT_PROFILE=CarbonAPI
```

To build and deploy CarbonAPI run the following in your shell:
```bash
make deploy
```
If you receive an Expired Token error, retry. The token will be updated

To deploy a specific lambda function
```bash
make build-About deploy
```

## Add a resource to the application
Extend the `events/requirement.txt` and run `make build`.

## Lambda function logs
To simplify troubleshooting, use `make log-<name>`

```bash
make logs-About
```

You can find more information and examples about filtering Lambda function logs in the 
[SAM CLI Documentation](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-logging.html).

## Tests

Tests are defined in the `tests` folder in this project. 
To run all tests, use `make test`. You can select unit or functional test with `make unit-test` 
or `make functional-test`. The functional-test call the API via a local lambda emulator, 
after starting lambda server in background (`make async-start-lambda`).
```bash
make test
make unit-test
make functional-test
```

### Invoke local API
After started local api, to invoke api, use `make api-<path suffix>`
```bash
make async-start-api
make api-about
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



## Cleanup
To cleanup the project, use `make clean`.

## Resources
See the [AWS SAM developer guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam.html) 
for an introduction to SAM specification, the SAM CLI, and serverless application concepts.

## TO TRY
- Use only one lambda function with differents URL