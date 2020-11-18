# ReadHaystack AWS Lambda API

Haystackapi is a skeleton to implement [ReadHaystack Rest API](https://project-haystack.org/doc/Rest).
It's compatible with AWS Lambda or Flask server.

## Summary
This project contains source code and supporting files for a Haystack server application 
that you can deploy with `make aws-deploy` 

This implementation propose two API endpoint:
- Classical Haystack API
- GraphQL API

# Classical Haystack API
Theses API can negotiate:
- Request format (`Content-Type: text/zinc`, `application/json` or `text/csv`)
- Response format (`Accept: text/zinc, application/json, text/csv`)

The code implements all ReadHaystack [operations](https://project-haystack.org/doc/Rest):
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

# GraphQL Haystack API
This API use the `http://<host>:<port>/graphql` url and was conform to the schema
describe in file `schema.graphql`.

## Quick local installation
```bash
pip install haystackapi[flask,graphql]`
HAYSTACK_PROVIDER=haystackapi.providers.ping haystackapi
```

## Deploy server
- start the api
    - with flask and Haystack classical API, 
        - `pip install "haystackapi[flask]"`
        - `HAYSTACK_PROVIDER='<your provider module>' haystackapi`
    - with flask and Haystack+GraphQL API, 
        - `pip install "haystackapi[graphql]"`
        - `HAYSTACK_PROVIDER='<your provider module>' haystackapi`
    - with AWS Lambda
        - `pip install "haystackapi[graphql,lambda]"`
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
To create your custom ReadHaystack API
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

### Provider Ping
Use `HAYSTACK_PROVIDER=providers.ping` to use this provider.
It's a very simple provider, with a tiny implementation of all haystack operation.

### Provider URL
Use `HAYSTACK_PROVIDER=providers.url` to use this provider.
Add the variable `HAYSTACK_URL=<url>` to expose an ReadHaystack file via the ReadHaystack protocol.
The methods `/read` and `/hisRead` was implemented.
The `<url>` may have the classic form (`http://...`, `ftp://...`) or can reference an S3 file (`s3://...`).
The time series to manage history must be referenced in the entity, with the `hisURI` tag.
This URI may be relative and must be in parquet format.

You can use `import_s3` to import an Haystack file in s3 bucket, only if the file is modified
(to respect the notion of Version with this provider).
The corresponding `hisURI` time-series files are uploaded too.
```bash
python -m haystackapi.providers.import_s3 <haystack file url> <s3 url>
```
You can use the parameters: 
* `--no-compare` if you don't want to download the remote version and compare with the new version to detect an update
* `--no-time-series` if you don't want to upload the time-series referenced in `hisURI` tags'
* `--force` to force the upload, and create a new version for all files in the bucket.

Because this provider use a local cache with the parsing version of S3 file,
it's may be possible to see different versions if AWS use multiple instance of lambda.
To fixe that, the environment variable `REFRESH` can be set to delay cache refresh
(Default value is 15m). Every quarter of an hour, each lambda check the list
of version for this file, and refresh the cache in memory, at the same time.
If a new version is published juste before you start the lambda, it's may be possible
you can't see this version. You must wait the end of the current quarter.

If you limit the concurrency of lambda to 1, this synchronisation between lambda
is not activate. 

### Provider SQL
This provider use an ontology imported in SQL database. Each entity is saved in a row
in the JSON format.
Use `HAYSTACK_PROVIDER=providers.sql` to use this provider.
Add the variable `HAYSTACK_DB` to describe the link to the table. 
At this time, only Postgresql was supported.
```bash
HAYSTACK_PROVIDER=providers.sql
HAYSTACK_DB=postgresql://scott:tiger@localhost/mydatabase#haystack
HAYSTACK_DB=postgresql+psycopg2://scott:tiger@localhost/mydatabase
```
If the password is `secretManager`, and you use AWS lambda,  
the password is retrieved from the service `secretManager`, 
with the key, whose name is in the environment variable `SECRET_NAME`.

The methods `/read` was implemented.

You can use `import_db` to import an Haystack file in database. 
```bash
python -m haystackapi.providers.import_db <haystack file url> <db url>
```
You can use the parameters:
* `--customer` to set the customer id
* `--clean` to clean the oldest versions before import a new one
* `--no-time-series` if you don't want to upload the time-series referenced in `hisURI` tags'


After deployment, you can use this provider like any others providers. 
The haystack filter was automatically converted to Postgres SQL.
Two table was created:
- <table_name> (haystack by default)
- <table_name>_meta_datas
and some index.
The column `entity` use a json version of haystack entity 
(See [here](https://project-haystack.org/doc/Json)).

To manage the multi-tenancy, it's possible to use different approach:
- Overload the method `get_customer_id()` to return the name of customer, deduce by the user logging
- Use different table (change the table name, ...#haystack_customer1, ...#haystack_customer2)

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

### Invoke GraphQL API
To print the local GraphQL API URL:
```bash
make graphql-api
```

To test the GraphQL API, open this URL with a web browser
or use a GraphQL Client with this URL.

```GraphQL
{ haystack {
    about
    {
        haystackVersion
        tz
        serverName
        serverTime
        serverBootTime
        productName
        productUri
        productVersion
        moduleName
        moduleVersion
    }
    ops
    {
        name
        summary
    }
    versions
    entities(ids:["@elec-16514","@site-434051"])
    byid:entities(ids:["@elec-16514","@site-434051"])
    byfilter:entities(select: "id,dis" filter: "id", limit: 2)
    histories(ids:["@elec-397691","@elec-434051"])
    pointWrite(id:"@elec-16514")
    {
        level
        levelDis
        val
        who
    }
    country:values(tag:"geoCountry")
} }
```
#### Merge GraphQL API 
To integrate Haystack GraphQL API inside another GraphQL API,
- Extract the schema
```bash
make graphql-schema
```
- Insert this schema without the `Query`
- In you query, insert a link to app/graphql_model.py!ReadHaystack
- And deploy your application

#### Use AWS AppSync
It's possible to use AWS AppSync to integrate the Haystack GraphQL API.
Read the file `README.md` in the folder `aws appsync`.


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
