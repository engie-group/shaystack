# Python Haystack API

| The API is not stable and can be changed without any notice. |
| --------------------------------------------------------- |

| This is a pre-release version |
| ----------------------------- |

To use the release candidate package hosted in **test.pypi.org**, use

```bash
export PIP_INDEX_URL=https://test.pypi.org/simple
export PIP_EXTRA_INDEX_URL=https://pypi.org/simple
```

Haystackapi is a set of API to implement [Haystack project specification](https://project-haystack.org/). It's
compatible with Flask server in data center, Edge (Raspberry?) or in AWS Lambda function.

## About Haystack, and who is it for

[Haystack project]((https://project-haystack.org/)) is an open source initiative to standardize semantic data models for
Internet Of Things. It enables interoperability between any IoT data producer and consumer, mainly in the Smart Building
area.

Haystack core data model is the Grid, it can be serialized in many formats,
mainly [Zinc](https://www.project-haystack.org/doc/Zinc),
[Json](https://www.project-haystack.org/doc/Json)
and [Csv](https://www.project-haystack.org/doc/Csv)

## About this project

This project implements client side haystack code. Useful to parse or dump Haystack files
([Zinc](https://www.project-haystack.org/doc/Zinc),
[Json](https://www.project-haystack.org/doc/Json),
[Csv](https://www.project-haystack.org/doc/Csv)).

On the server side, it also implements 
[Haystack Rest API](https://www.project-haystack.org/doc/Rest), useful to serve Haystack data you host.

- We implemented two serving options (See [API Server](#Server Side Haystack)): Flask and AWS Lambda
    - Each offering two API endpoints:
        - Classical REST Haystack API
        - GraphQL API
- We introduced and implemented the *Provider* concept, which handles various options in terms on haystack data
  location:
    - Local or remote file system (including AWS S3)
    - Local or remote relational database, with optional AWS Time Stream use for Time Series
    - Other custom data location can be handled by extending
      `haystackapi.providers.HaystackInterface`

# History

This project is a fork of [hszinc](https://github.com/widesky/hszinc)
(Thanks to the team). The proposed evolutions were too big to be accepted in a pull request.

To see the similarities and differences between the two project, click [here](hszinc.md)

# Client side: Haystack client python module

To try the client side python module included in this project, the best way is to download a sample of haystack files. First, create a working directory.

```console
$ mkdir $TMP/haystack
$ cd $TMP/haystack
```

Download and unzip [`sample` zip file](https://downgit.github.io/#/home?url=https://github.com/pprados/haystackapi/tree/develop/sample)
in this directory.

```console
$ unzip sample
```

The directory `sample` now contains:

- `carytown.[csv|jon|zinc]`: A public reference haystack ontology
- `p:demo:*.zinc`: A sample of time series data (ts,val csv format)

Create a virtual environment

```console
$ virtualenv -p python3.8 venv
$ source venv/bin/activate
```

Then, install the module with all options

```console
$ pip install "haystackapi[flask,graphql,lambda]"
```

`sample.ipynb` jupyter notebook contains code to read, filter, manipulate
and print `Grid` objects containing haystack data.
It also contains code to create a `Pandas Dataframe` from a `Grid` object, which could be useful for a Data Science project.

Install and start a jupyter notebook server then open `sample.ipynb`

```console
$ pip install jupyter pandas
$ jupyter-notebook
```

[a relative link](other_file.md)

[Custom foo description](#foo)

# Features

Haystackapi is agile and can be deployed in different scenarios. Choose an option for each feature.

| Python version |
|:------:|
|   3.7  |
|   3.8  |
|   3.9  |

| Deployment              |
| ----------------------- |
| Internet Flask server   |
| Edge Flask server       |
| Docker Flask server     |
| Internet AWS Lambda API |

| Haystack data location       |
| ---------------------------- |
| local file                   |
| url                          |
| S3 bucket without version    |
| S3 bucket with version       |
| Sqlite database              |
| Postgres database            |
| SQL database + AWS Timesteam |

| Multi tenancy                 |
| ----------------------------- |
| Single                        |
| Multiple, shared SQL table |
| Multiple, dedicated SQL table |

| API                                               |
| ------------------------------------------------- |
| Haystack REST API                                 |
| Standalone GraphQL API                            |
| GraphQL API integrated inside another via AppSync |

| Serverless  | Technologies               |
| ----------- | -------------------------- |
| No  | VM, Docker, Postgres, etc. |
| Yes | AWS Lambda, Aurora         |

and you can extend these proposed scenario. You can read later, how to implement these different scenarios.

# Server Side: Haystack API Server

This implementation can offer two API endpoints:

- Classical [REST Haystack](https://www.project-haystack.org/doc/Rest)
  - Available on `http://<host>:<port>/haystack`
- GraphQL
  - Available on `http://<host>:<port>/graphql` and compliant with [`schema.graphql`](schema.graphql)

This API can negotiate:

- Request format (`Content-Type: text/zinc`, `application/json` or `text/csv`)
- Response format (`Accept: text/zinc, application/json, text/csv`)

These [operations](https://project-haystack.org/doc/Rest) are implemented in both endpoints:
- [about](https://project-haystack.org/doc/Ops#about)
- [ops](https://project-haystack.org/doc/Ops#ops)
- [formats](https://project-haystack.org/doc/Ops#formats)
- [read](https://project-haystack.org/doc/Ops#read)
- [hisRead](https://project-haystack.org/doc/Ops#hisRead)
- [nav](https://project-haystack.org/doc/Ops#nav)
- [invokeAction](https://project-haystack.org/doc/Ops#invokeAction)

These [operations](https://project-haystack.org/doc/Rest) are implemented only in classical endpoint:
- [watchSub](https://project-haystack.org/doc/Ops#watchSub)
- [watchUnsub](https://project-haystack.org/doc/Ops#watchUnsub)
- [watchPoll](https://project-haystack.org/doc/Ops#watchPoll)
- [pointWrite](https://project-haystack.org/doc/Ops#pointWrite)
- [hisWrite](https://project-haystack.org/doc/Ops#hisWrite)

## API Server deployment

### Installing
Using `pip install` you can add the support of some options:
- `pip install "haystackapi[flask]"` allows you to use a local [Flask](https://flask.palletsprojects.com/en/1.1.x/) server
- `pip install "haystackapi[aws]"` allows you to:
  - Serve the API in an AWS Lambda function
  - Expose haystack data located in an AWS S3 Bucket  
- `pip install "haystackapi[graphql]"` allows you to:
  - Expose the `/graphql` endpoint in addition to the classical `/haystack` endpoint

You can mix two or more options, if you need them all, use `pip install "haystackapi[flask,graphql,aws]"`

### Choosing and configuring your provider
Depending on where and how your haystack data is stored, you need to choose an existing Provider or implement your own by extending `haystackapi.providers.HaystackInterface` 

|Where is data stored|Configuration|Miscellaneous|
|---|---|---|
|No data, just testing|`export HAYSTACK_PROVIDER=haystackapi.providers.ping`||
|Data on http server|`export HAYSTACK_PROVIDER=haystackapi.providers.url HAYSTACK_URL=http://...`|[More...](README_url_provier.md)|
|Data on ftp server|`export HAYSTACK_PROVIDER=haystackapi.providers.url HAYSTACK_URL=ftp://...`|[More...](README_url_provier.md)|
|Data on local filesystem|`export HAYSTACK_PROVIDER=haystackapi.providers.url HAYSTACK_URL=file://...`|[More...](README_url_provier.md)|
|Data on AWS S3 Bucket|`export HAYSTACK_PROVIDER=haystackapi.providers.url HAYSTACK_URL=s3://...`|Remember to install aws support and boto3 python module. [More...](README_url_provier.md)|
|Data in a SuperSQLite database|`export HAYSTACK_PROVIDER=haystackapi.providers.sql HAYSTACK_URL=sqlite3://...`|Remember to install supersqlite python module. [More...](README_url_provier.md)|
|Data in a Postgresql database|`export HAYSTACK_PROVIDER=haystackapi.providers.sql HAYSTACK_URL=sqlite3://...`|Remember to install psycopg2 python module. [More...](README_url_provier.md)|
|Custom|`export HAYSTACK_PROVIDER=haystackapi.providers.<your class name>`|Write your own subclass of `haystackapi.providers.HaystackInterface`. Non implemented methods will be automatically excluded in [`ops`](https://project-haystack.org/doc/Ops#ops) operation output|

Note: Existing providers are not connected to IOT for simplicity.
If you want to connect the haystack API with IOT, you must implement a custom provider. 

### Starting the server
Use the command `haystackapi` (check `haystackapi --help` for parameters)


We propose different providers, with the objective in mind:

- Expose the haystack files and historical data with an API
- and manage the evolution of these files with the notion of `version`.



To demonstrate this scenario, we want to publish the sample from `sample/` files from S3 bucket or from an SQL database.
We must import this ontology and time-series inside the bucket or database before to use. To manage the different
versions of files, you must use a dedicated tool, to import only the difference between versions.

==================================================
#### Provider Ping

Use `HAYSTACK_PROVIDER=haystackapi.providers.ping` to use this provider. It's a very simple provider, with a tiny
implementation of all haystack operation. Read the code.

```console
$ HAYSTACK_PROVIDER=haystackapi.providers.ping haystackapi
```

In another console

```console
$ curl http://localhost:3000/haystack/about
```

#### Provider URL

Use `HAYSTACK_PROVIDER=haystackapi.providers.url` to use this provider. Add the variable `HAYSTACK_URL=<url>` to expose
an Haystack file via the Haystack protocol. The methods `/read` and `/hisRead` was implemented. The `<url>` may have the
classic form (`http://...`, `ftp://...`, `file://...`, etc.) or can reference an S3 file (`s3://...`). The time series
to manage history must be referenced in the entity, with the `hisURI` tag. This URI may be relative and must be in
haystack format.

All the file may be zipped. Reference the zipped version with the `.gz` suffix
(eg. `ontology.zinc.gz`)

```console
$ # Demo
$ HAYSTACK_PROVIDER=haystackapi.providers.url \
  HAYSTACK_URL=sample/carytown.zinc \
  haystackapi
```

in another shell

```console
$ curl 'http://localhost:3000/haystack/read?filter=site'
air,phone,sensor,occupied,store,damper,enum,temp,tz,tariffHis,sp,area,site,weatherRef,elecCost,hisMode,kwSite,summary,
fan,siteRef,primaryFunction,kind,cmd,geoCountry,elec,lights,geoStreet,occupiedEnd,yearBuilt,siteMeter,geoCoord,
regionRef,occupiedStart,effective,equip,sitePoint,cool,ahu,hvac,costPerHour,unit,lightsGroup,discharge,zone,power,
geoCity,rooftop,navName,outside,point,dis,energy,elecMeterLoad,id,geoAddr,cur,geoState,geoPostalCode,equipRef,meter,
pressure,heat,return,storeNum,his,metro,stage,hisURI
,"804.552.2222",,,✓,,,,"New_York",,,3149.0ft²,✓,"@p:demo:r:23a44701-1af1bca9 Richmond, VA",,,,,,,"Retail Store",,,
"US",,,"3504 W Cary St",20:00:00,1996.0,,"C(37.555385,-77.486903)",@p:demo:r:23a44701-67faf4db Richmond,10:00:00,
,,,,,,,,,,,,"Richmond",,,,,"Carytown",,,@p:demo:r:23a44701-a89a6c66 Carytown,"3504 W Cary St, Richmond, VA",,
"VA","23221",,,,,,1.0,,"Richmond",,
```

##### Limitations

Because this provider use a local cache with the parsing version of S3 file, it's may be possible to see different
versions if AWS use multiple instances of lambda. To fix that, the environment variable `REFRESH` can be set to delay
the cache refresh (Default value is 15m). Every quarter of an hour, each lambda instance check the list of version for
this file, and refresh the cache in memory, at the same time. If a new version is published just before you start the
lambda, it's may be possible you can't see this new version. You must wait the end of the current quarter, redeploy the
lambda or update the `REFRESH`
parameter.

#### Provider SQL

This provider use an ontology imported in SQL database. Each entity is saved in a row in the JSON format.
Use `HAYSTACK_PROVIDER=haytackapi.providers.sql` to use this provider. Add the variable `HAYSTACK_DB` to describe the
link to the root table. At this time, only SuperSQLite and Postgresql was supported.

```console
$ pip install 'haystackapi[graphql,lambda]'
```

Install the corresponding database driver:

| Database | Driver                                              |
| -------- | --------------------------------------------------- |
| sqlite   | `pip install supersqlite` (`apt install build-essential` before, and may take several minutes)|
| postgres | `pip install psycopg2`                              |
|          | or `pip install psycopg2-binary`                    |

You can use `haystackapi_import_db` to import a Haystack files into the database, only if the entities are modified
(to respect the notion of _Version_ with this provider). The corresponding `hisURI` time-series files are uploaded too.

```bash
haystackapi_import_db <haystack file url> <db url>
```

You can use the parameters:

* `--customer` to set the customer id for all imported records
* `--clean` to clean the oldest versions before import a new one
* `--no-time-series` if you don't want to import the time-series referenced in `hisURI` tags'

To demonstrate the usage with sqlite,

```console
$ # Demo
$ # - Install the components
$ pip install 'haystackapi[flask]'
$ # - Install the sqlite driver
$ pip install supersqlite
$ # - Import haystack file in DB
$ haystackapi_import_db sample/carytown.zinc sqlite3:///test.db#haystack
$ # - Expose haystack with API
$ HAYSTACK_PROVIDER=haystackapi.providers.sql \
  HAYSTACK_DB=sqlite3:///test.db#haystack \
  haystackapi
```

in another shell

```console
$ curl 'http://localhost:3000/haystack/read?filter=site'
air,phone,sensor,occupied,store,damper,enum,temp,tz,tariffHis,sp,area,site,weatherRef,elecCost,hisMode,kwSite,summary,
fan,siteRef,primaryFunction,kind,cmd,geoCountry,elec,lights,geoStreet,occupiedEnd,yearBuilt,siteMeter,geoCoord,
regionRef,occupiedStart,effective,equip,sitePoint,cool,ahu,hvac,costPerHour,unit,lightsGroup,discharge,zone,power,
geoCity,rooftop,navName,outside,point,dis,energy,elecMeterLoad,id,geoAddr,cur,geoState,geoPostalCode,equipRef,meter,
pressure,heat,return,storeNum,his,metro,stage,hisURI
,"804.552.2222",,,✓,,,,"New_York",,,3149.0ft²,✓,"@p:demo:r:23a44701-1af1bca9 Richmond, VA",,,,,,,"Retail Store",,,
"US",,,"3504 W Cary St",20:00:00,1996.0,,"C(37.555385,-77.486903)",@p:demo:r:23a44701-67faf4db Richmond,10:00:00,
,,,,,,,,,,,,"Richmond",,,,,"Carytown",,,@p:demo:r:23a44701-a89a6c66 Carytown,"3504 W Cary St, Richmond, VA",,
"VA","23221",,,,,,1.0,,"Richmond",,
```

The SQL url is in form: <dialect\[+\<driver\>]>://\[\<user\>\[:\<password\>]@>\<host\>\[:\<port\>]/\<database
name\>\[#\<table name\>]

Samples:
- `sqlite3:///test.db#haystack`
- `sqlite3://localhost/test.db`
- `sqlite3+supersqlite.sqlite3:///test.db#haystack`
- `postgres://postgres:password@172.17.0.2:5432/postgres`

Inside the SQL url, if the password is empty, and you use AWS lambda,  
the password is retrieved from the service [`secretManagers`](https://aws.amazon.com/secrets-manager/), with the key,
whose name is in the environment variable `HAYSTACK_DB_SECRET`. Use the key `password` in secret managers to protect the
database password.

After the deployment, you can use this provider like any others providers. The haystack filter was automatically
converted to SQL. Three table was created:

- <table_name> (`haystack` by default)
- <table_name>_meta_datas
- <table_name>_ts
- and some index.

The column `entity` use a json version of haystack entity (See [here](https://project-haystack.org/doc/Json)).

The time-series are saved in a table `<table_name>_ts`. If you prefer to use a dedicated time-series database, overload
the method `hisRead()`

To manage the multi-tenancy, it's possible to use different approach:

- Overload the method `get_customer_id()` to return the name of the current customer, deduce by the current API caller
- Use different tables (change the table name, `...#haystack_customer1`, `...#haystack_customer2`)
  and publish different API, one by customers.

##### Limitations

- All entities uses with this provider must have an `id` tag
- SQLite can not manage parentheses with SQL Request with `UNION` or `INTERSECT`. Some complexe haystack request can not
  generate a perfect translation to SQL.

#### Provider SQL + AWS Time stream

This provider extends the SQL Provider to manage time-series with
[AWS Time stream](https://docs.aws.amazon.com/timestream/). Use `HAYSTACK_PROVIDER=haytackapi.providers.sql_ts` to use
this provider. Add the variable `HAYSTACK_DB` to describe the link to the root table in SQL DB and `HAYSTACK_TS` to
describe the link to *AWS Time stream*. The format of `HAYSTACK_TS` is :

`timestream://<database>[?mem_ttl=<memory retention in hour>&mag_ttl=<magnetic retention in day>][#<tablename>]`

The parameters `mem_ttl` and `mag_ttl` are optionals and be used only to create the table.
Read [this](https://docs.aws.amazon.com/timestream/latest/developerguide/API_RetentionProperties.html)
for the maximum value. The default value for `mem_ttl` is 8766 (1y+6h) and 400d for `mag_ttl`.

The table schema is

```
id (varchar)            -- The haystack id
customer_id (varchar)   -- The associated customer_id
unit (varchar)          -- Unit, use only with time series of quantity
hs_type (varchar)       -- python type of the time serie
measure_name (varchar)  -- 'val'
time (timestamp)        -- The timestamp of the value is microseconds
measure_value::<double> -- The value (adapt the name with the type of value)
```

You can publish data in this table, via *[AWS IoT](https://aws.amazon.com/fr/iot/)* Core for example.

- Use the same `id` as for Haystack.
- Add eventually a value for `customer_id`
-

```console
$ HAYSTACK_PROVIDER=haystackapi.providers.sql \
  HAYSTACK_DB=sqlite3:///test.db#haystack \
  HAYSTACK_TS=timestream://HaystackAPIDemo/?mem_ttl=1&mag_ttl=100#haystack \
  haystackapi
```

With this provider, all the time-series are inserted in AWS Time Stream. You can use `haystackapi_import_db` with a
third parameter to describe the link to the time-series database:

```console
$ haystackapi_import_db sample/carytown.zinc \
    sqlite3:///test.db#haystack \
    timestream://HaystackAPIDemo
```

##### Limitation
- The entities with history must have a tag `kind` to describe the type of value and a tag `id`
- AWS Time stream refuse to import a data outside the memory windows delays.
  See [here](https://docs.aws.amazon.com/timestream/latest/developerguide/API_RejectedRecord.html)

# Using GraphQL API

All the providers can be invoked with a GraphQL API in place of the standard Haystack Rest API. After installing the
component with the good option (`pip install 'haystackapi[graphql]'`), start the provider and use the url
`http://localhost:3000/graphql`. You can see an interface to use the ontology.

For the demonstration,

```console
$ # Demo
$ # - Install components
$ pip install 'haystackapi[graphql]'
$ # - Expose haystack with GraphQL API
$ HAYSTACK_PROVIDER=haystackapi.providers.url \
  HAYSTACK_URL=sample/carytown.zinc \
  haystackapi
```

In another shell

```console
$ # - Open the GraphQL console
$ xdg-open http://localhost:3000/graphql
```

and use this request

```graphql
# Demo
{
    haystack {
        versions
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
        byid:entities(ids:["@p:demo:r:23a44701-3a62fd7a"])
        byfilter:entities(select: "id,dis" filter: "id", limit: 2)
        histories(ids:["@p:demo:r:23a44701-3a62fd7a"])
        {
            ts
            float
        }
        country:tagValues(tag:"geoCountry")
    }
}
```

Because Graphql use a schema and Haystack doesn't use one, it's not easy to manipulate the history result. To resolve
that, we propose different *cast* for the values.

```graphql
histories(ids:["@p:demo:r:23a44701-3a62fd7a"])
{
ts
val  # Haystack json scalar
float # cast to float
bool # cast to bool
...
}
```

You can select the format you want in the request.

## Using with Excel or PowerBI

Because the default negotiated format is CSV, you can call the REST API with PowerQuery or Excel. Try the sample file
['HaystackAPI.xlsm'](HaystackAPI.xlsm) and set a correct haystack url
(http://10.0.2.2:3000/haystack with a local virtual windows). You can load all the data inside Excel table.

## Using with Amazon AWS

This module offers two layers to use AWS cloud. It's possible to publish the haystack files in a bucket, and use the URL
provider to expose an API (REST and GraphQL)
and it's possible to use the AWS Lambda to publish the API.

To import the dependencies:

```console
$ pip install haystackapi[lambda]
```

### AWS Bucket

To export the haystacks files in a bucket, you must create one. If you add the _Version_ feature, it's possible to
update the files, and use the API to read an older version. The extended parameter `Version` in each request may be used
to ask some data, visible at a specific date.

You can use `haystackapi_import_s3` to import a Haystack file in s3 bucket, only if the file is modified
(to respect the notion of _Version_ with this provider).

```bash
haystackapi_import_s3 <haystack file url> <s3 url>
```

The corresponding `hisURI` time-series files are uploaded too. The current values before the first version of the new
file are added to maintain the history.

Set AWS profile before to use this tool.

```console
$ export AWS_PROFILE=default
```

You can update others parameters (`AWS_STACK`, `AWS_PROFILE`, `AWS_REGION`, ...)

Then, create an S3 bucket, and for the demo, set the variable `MY_BUCKET`

```console
$ export MY_BUCKET=<your bucket name>
```

You can import the datas inside this bucket

```console
$ haystackapi_import_s3 sample/carytown.zinc "s3://${MY_BUCKET}"
```

You can use the parameters:

* `--no-compare` if you don't want to download the remote version and compare with the new version to detect an update
* `--no-time-series` if you don't want to upload the time-series referenced in `hisURI` tags'
* `--force` to force the upload, and create a new version for all files in the bucket.

If the source and target are in different buckets in the same region, the copy was done from bucket to bucket.

Then, you can start a local Flash server:

```console
$ # Demo
$ HAYSTACK_PROVIDER=haystackapi.providers.url \
  HAYSTACK_URL=s3://${MY_BUCKET}/carytown.zinc \
  haystackapi
```

### AWS Lambda

The code is compatible with AWS Lambda. Install this option (`pip install "haystackapi[lambda]"`)
and create a file `zappa_settings.json` with something like this:

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
      "LOG_LEVEL": "INFO",
      "HAYSTACK_PROVIDER": "haystackapi.providers.url",
      "HAYSTACK_URL": "s3://my_bucket/carytown.zinc"
    }
  }
}
```        

Update the parameter values like `project_name`, `s3_bucket` or `HAYSTACK_URL`.

Then, use [zappa](https://github.com/Miserlou/Zappa) to deploy.

```console
$ virtualenv -p python3.8 venv
$ source venv/bin/activate
$ pip install "haystackapi[graphql,lambda]"
$ zappa deploy
```

You can use the Lambda API to invoke the REST or GraphQL API.

```console
$ # Extract the API URL
$ HAYSTACK_ROOT_API=$(zappa status --json | jq -r '."API Gateway URL"')
$ # Try the classic haystack API
$ curl $HAYSTACK_ROOT_API/haystack/about
$ # Try the Graphql API
$ xdg-open "$HAYSTACK_ROOT_API/graphql"
```

### AWS AppSync

Appsync is a technology to agregate differents API in one Graphql API. It's possible to merge the haystack GraphQL with
other GraphQL API with AppSync. To do that, read [this file](aws%20appsync/AppSync.md).

### Docker

The `Dockerfile` can be used to generate an image with a set of parameter.

```console
$ # Get docker file
$ wget https://github.com/pprados/haystackapi/blob/develop/Dockerfile
$ # Build the image
$ docker build -t haystackapi .
$ # Run and customize the image
$ docker run -p 3000:3000 \
  -e HAYSTACK_PROVIDER=haystackapi.providers.ping \
  -e HAYSTACK_URL=sample/carytown.zinc \
  -e HAYSTACK_DB=sqlite:///test.db#haystack \
  -e HAYSTACK_DB_SECRET= \
  -e REFRESH=15 \
  haystackapi 
```

# Optional part

Haystack component propose different optional parts.

| Option  | Feature                                         |
| ------- | ----------------------------------------------- |
| flask   | Expose API with Flask HTTP server               |
| graphql | Expose Graphql API with Flask HTTP server       |
| lambda  | Add compatibility with AWS Lambda and S3 bucket |

Use `pip install "haystackapi[_<options>_]"`, like:

- `pip install "haystackapi[flask,graphql,lambda]"`

## Data types

`haystackapi` converts the common Python data types:

### `Null`, `Boolean`, `Date`, `Time`, `Date/Time` and `strings`.

In the case of Date/Time, the `tzinfo` parameter is set to the equivalent timezone provided by the `pytz` library where
possible.

### `Numbers`

Numbers without a unit are represented as `float` objects. Numbers with a unit are represented by
the `haystackapi.Quantity` custom type which has two attributes: `value` and `unit`. The unit use
the [Pint](https://pint.readthedocs.io/en/stable/) framework to manage and convert unit.

### `Marker` and `Remove`

These are singletons, represented by `haystackapi.MARKER` and `haystackapi.REMOVE`. They behave and are intended to be
used like the `None` object.

### `Bin` and `XBin`

These are represented bytes array with specific MIME type. Accept `hex` or `b64` to encode and decode the bytes array.

### `Uri`

This is a classical `Uri` for Haystack

### `Ref`

Represented by the custom type `haystackapi.Ref` which has `name` (`str`),
`has_value` (`bool`) and `value` (any type) attributes. The value must be conforme with the haystack specification.

### `Coordinate`

Represented by the custom type `haystackapi.Coordinate`, which has `latitude` and
`longitude` types (both `float`)

### Collection `List`, `Dict` or `Grid`

A tag may be a list, a dict or another grid (recursive grid). To be used with care.

# Contribute

See [here](./Contibute.md)

# Resources

- [Haystack Project](https://www.project-haystack.org/)
- [Zappa](https://github.com/Miserlou/Zappa) framework

# License

See [LICENCE](LICENSE-2.0.txt) file

# TODO

- [ ] coverage
- [ ] MySQL
- [ ] Pypy (when pip install typed-ast running)