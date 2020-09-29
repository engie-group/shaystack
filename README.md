# Haystack AWS Lambda API

Haystackapi is a skeleton to implement [Haystack Rest API](https://project-haystack.org/doc/Rest).
It's compatible with AWS Lambda or Flask server.

Theses API can negotiate:
- Request format (`Content-Type: text/zinc`, `application/json` or `text/csv`)
- Request encoding (`Content-Encoding: gzip`)
- Response format (`Accept: text/zinc, application/json, text/csv`)
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
that you can deploy with `make aws-deploy` 

## Quick local installation
```bash
pip install haystackapi[flask]`
HAYSTACK_PROVIDER=haystackapi.providers.ping haystackapi
```

## Deploy server
- start the api
    - with flask, `HAYSTACK_PROVIDER='<your provider module> haystackapi`
        - `pip install "haystackapi[flask]"`
    - with AWS Lambda
        - `pip install "haystackapi[lambda]"`
        - create a file zappa_settings.json with
```json
{
  "dev": {
    "profile_name": "default",
    "aws_region": "us-east-2",
    "app_function": "app.__init__.app",
    "project_name": "my_haystackapi",
    "s3_bucket": "zappa",
    "runtime": "python3.8",
    "aws_environment_variables": {
      "HAYSTACK_PROVIDER": "haystackapi.providers.ping",
      "HAYSTACK_URL": "s3://my_bucket/haystack_file.json"
    }
  }
}
```        
        - update the parameters
        - `zappa deploy`

# Custom provider
To create your custom Haystack API
- create a project
- In a module, create a subclass of `HaystackInterface` with the name `Provider`
- add parameter `HAYSTACK_PROVIDER` with the name of the package 

# Organization
The project includes the following files and folders:
- `app` - Code for the application's Flask and Lambda function.
- `haystackapi` - The generic wrapper between technology and implementation
- `haystackapi/providers` - Sample of providers.
- `tests` - Unit tests for the application code. 
- `hszinc` - Git submodule to extend the hszinc project. 
- `*.postman*.json` - script to invoke API with postman
- `Makefile` - All tools to manage the project (Use `make help`'`)

You can add some environment variable in `.env` file.

## Providers
Different sample of provider are proposed. You can add a new one with a subclass of 
`haystackapi.providers.HaystackInterface`.
Then, you can implement only the method you want. The others methods are automatically exclude in 
the [`../ops`](https://project-haystack.org/doc/Ops#ops) operation.

To select a provider, add the environment variable `HAYSTACK_PROVIDER` in the environment.

To add a new provider, *fork the project* and add a provider in the `providers` directory. You can update others 
parameters in `Project.variables` (`HAYSTACK_PROVIDER`, `AWS_STACK`, `AWS_PROFILE`, `AWS_REGION`, ...)

### Provider ping
Use `HAYSTACK_PROVIDER=providers.ping` to use this provider.
It's a very simple provider, with a tiny implementation of all haystack operation.

### Provider url
Use `HAYSTACK_PROVIDER=providers.url` to use this provider.
Add the variable `HAYSTACK_URL=<url>` to expose an Haystack file via the Haystack protocol.
The methods `/read` and `/hisRead` was implemented.
The `<url>` may have the classic form (`http://...`, `ftp://...`) or can reference an S3 file (`s3://...`).
The time series to manage history must be referenced in the entity, with the `hisURI` tag.
This URI may be relative and must be in parquet format.

### Using with Excel or PowerBI
Because the default negotiated format is CSV, you can call theses API with PowerQuery/

## Build the application
This project use a `Makefile` (>4.0) to integrate all tools
and [Conda](https://docs.conda.io/projects/conda/en/latest/index.html)
to manage dependencies and others tools.

To initialise the Conda environment, use `make configure` and activate the conda environment.
Then, it's possible to `test`, `start-api`, etc. See `make help` to print all major target.
```bash
git clone --recurse-submodules http://github.com/pprados/haystackapi.git 
make configure
conda activate haystackapi
make test
```

## Tests
Tests are defined in the `tests` folder in this project. 
To run all tests, use `make test`.
```bash
make test
```

## Use the Makefile to test API locally
Use the `make start-api` to run the API locally on port 3000 with Flask.

You can use [Postman](https://www.postman.com/) and the files `HaystackAPI.postman_collection.json` 
and `HaystackAPI.postman_environment.json` to test and invoke the local API.

You can also start API server in background with `make async-start-api` and close it with `make async-stop-api`.

```bash
make async-start-api
curl http://localhost:3000/about
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
Copy `.env.template` to `.env` and update your local variables
Theses variables are used in `Makefile`, when we start the api, etc.

The project variable are in `Project.variables` file.

## Cleanup
To cleanup the project, use `make clean`.

## Tips
If you use Okta technology, you can set in `.env`
GIMME="echo 0 | gimme-aws-creds --username XXXX"

## Resources
[Zappa](https://github.com/Miserlou/Zappa) framework