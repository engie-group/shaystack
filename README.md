# Python Haystack API

| This is a pre-release version |
| --- |

To use the release candidate package present in **test.pypi.org**, use

```bash
export PIP_INDEX_URL=https://test.pypi.org/simple
export PIP_EXTRA_INDEX_URL=https://pypi.org/simple
```

Haystackapi is a set of API to implement [Haystack project specification](https://project-haystack.org/). It's
compatible with Flask server in data center, edge or in AWS Lambda function.

## Summary

This project contains source code to parse or dump Haystack files
([Zinc](https://www.project-haystack.org/doc/Zinc),
[Json](https://www.project-haystack.org/doc/Json),
[Csv](https://www.project-haystack.org/doc/Csv)).

To implement the [Haystack Rest API](https://www.project-haystack.org/doc/Rest), extend the class `HaystackInterface`
and publish an AWS Lambda or start a Flash server
(See [Server API](#server-api)).

This implementation propose two API endpoint:

- Classical [REST Haystack API](https://www.project-haystack.org/doc/Rest)
- GraphQL API

# History

This project is a fork of [hszinc](https://github.com/widesky/hszinc)
(Thanks to the team). The proposed evolutions were too big to be accepted in a pull request.

To see the similarities and differences between the two version, clic [here](hszinc.md)

# Try it

To try this module, the best way is to download a sample of haystack file. First, create a directory to work.

```console
$ mkdir $TMP/haystack
$ cd $TMP/haystack
```

Download [here](https://downgit.github.io/#/home?url=https://github.com/pprados/haystackapi/tree/develop/sample)
and unzip the `sample.zip` in this directory.

```console
$ unzip sample
```

The directory `sample` now has examples files.

- `carytown.[csv|jon|zinc]`  : The haystack ontology
- `p:demo:*.zinc` : sample of time series

Inside this directory, create a virtual environment

```console
$ virtualenv -p python3.8 venv
$ source venv/bin/activate
```

Then, install the module with all options

```console
$ pip install 'haystackapi[flask,graphql,lambda]'
```

It's time to try to manipulate a grid. Start Python

```python-repl
Python 3.7.8 | packaged by conda-forge | (default, Jul 31 2020, 02:25:08) 
Type 'copyright', 'credits' or 'license' for more information
IPython 7.18.1 -- An enhanced Interactive Python. Type '?' for help.

In [1]: import haystackapi
In [2]: import datetime
In [3]: g = haystackapi.Grid()
In [4]: g.metadata['aMarker'] = haystackapi.MARKER
In [5]: g.metadata['today'] = datetime.date.today()
In [6]: g.column['firstColumn'] = {'metaData':'in no particular order', 'abc': 123}
In [7]: g.column['secondColumn'] = {}
In [8]: g.extend([
...:     {'firstColumn': haystackapi.Quantity(154, 'kg'), 'secondColumn': 'and counting'},
...:     {'firstColumn': haystackapi.MARKER, 'secondColumn': 'supported on Python 3.7+'},
...:     {'firstColumn': haystackapi.Coordinate(-27.4725,153.003), 
...:          'secondColumn': 'Made in Australia from local and imported ingredients'},
...:     ])
Out[8]: 
<Grid>
        Version: 3.0
        Metadata: MetadataObject{'aMarker'=MARKER, 'today'=datetime.date(2020, 12, 16)}
        Columns:
                firstColumn: {'metaData': 'in no particular order', 'abc': 123}
                secondColumn
        Row    0:
        firstColumn=PintQuantity(154, 'kg')
        secondColumn='and counting'
        Row    1:
        firstColumn=MARKER
        secondColumn='supported on Python 3.7+'
        Row    2:
        firstColumn=Coordinate(-27.4725, 153.003)
        secondColumn='Made in Australia from local and imported ingredients'
</Grid>

In [9]: print(haystackapi.dump(g))
ver:"3.0" aMarker today:2020-12-16
firstColumn metaData:"in no particular order" abc:123,secondColumn
154kg,"and counting"
M,"supported on Python and 3.7+"
C(-27.472500,153.003000),"Made in Australia from local and imported ingredients"

In [10]: print(haystackapi.dump(g,mode=haystackapi.MODE_JSON))
{"meta": {"aMarker": "m:", "today": "d:2020-12-16", "ver": "3.0"}, "cols": [{"metaData": "s:in no particular order", "abc": "n:123.000000", "name": "firstColumn"}, {"name": "secondColumn"}], "rows": [{"firstColumn": "n:154.000000 kg", "secondColumn": "s:and counting"}, {"firstColumn": "m:", "secondColumn": "s:supported on Python 2.7 and 3.x"}, {"firstColumn": "c:-27.472500,153.003000", "secondColumn": "s:Made in Australia from local and imported ingredients"}]}

In [11]: # Load haystack file
In [12]: import io
In [13]: with open("sample/carytown.zinc") as f:
...:         g = haystackapi.parse(f.read(),haystackapi.MODE_ZINC)
...: 
In [14]: # Filter some entity
In [15]: site = g.filter("site")[0]
In [16]: site
Out[16]: 
{'tz': 'New_York',
 'regionRef': Ref('p:demo:r:23a44701-67faf4db', 'Richmond', True),
 'occupiedStart': datetime.time(10, 0),
 'geoStreet': '3504 W Cary St',
 'geoAddr': '3504 W Cary St, Richmond, VA',
 'occupiedEnd': datetime.time(20, 0),
 'phone': '804.552.2222',
 'weatherRef': Ref('p:demo:r:23a44701-1af1bca9', 'Richmond, VA', True),
 'yearBuilt': 1996.0,
 'store': MARKER,
 'id': Ref('p:demo:r:23a44701-a89a6c66', 'Carytown', True),
 'geoState': 'VA',
 'area': PintQuantity(3149.0, 'ft²'),
 'storeNum': 1.0,
 'geoPostalCode': '23221',
 'geoCoord': Coordinate(37.555385, -77.486903),
 'metro': 'Richmond',
 'site': MARKER,
 'geoCountry': 'US',
 'primaryFunction': 'Retail Store',
 'dis': 'Carytown',
 'geoCity': 'Richmond'}

In [17]: # Read time-series
In [18]: with_his = g.filter("his")[0]
In [19]: ts_uri = "sample/" + with_his["hisURI"]
In [20]: with open(ts_uri) as f:
...:         ts = haystackapi.parse(f.read(),haystackapi.MODE_ZINC)
...:         print(ts)  # Print associated time-series
...: 
<Grid>
        Version: 3.0
        Metadata: MetadataObject{'hisStart'=datetime.datetime(2020, 1, 1, 0, 0, tzinfo=<StaticTzInfo 'Etc/UTC'>), 'hisEnd'=datetime.datetime(2020, 12, 1, 0, 0, tzinfo=<StaticTzInfo 'Etc/UTC'>)}
        Columns:
                ts
                val
        Row    0:
        ts=datetime.datetime(2020, 2, 1, 0, 0, tzinfo=<StaticTzInfo 'Etc/UTC'>)
        val=86.0
        Row    1:
        ts=datetime.datetime(2020, 3, 1, 0, 0, tzinfo=<StaticTzInfo 'Etc/UTC'>)
        val=83.0
</Grid>
In [21]: # Save grid
In [22]: with open("ontology.csv","w") as f:
    ...:         f.write(haystackapi.dump(g,haystackapi.MODE_CSV))
    ...: 
In [23]: with open("ontology.json","w") as f:
    ...:         f.write(haystackapi.dump(g,haystackapi.MODE_JSON))
    ...: 
```

# Data science

It's easy to convert a grid to a dataframe.

```python
with open("file.zinc") as f:
    grid = haystackapi.parse(f.read(), haystackapi.MODE_ZINC)

df = pd.DataFrame(grid.filter("point and co2e"))  # Convert grid to data frame
```

# Features

Haystackapi is agile and can be deployed in different scenarios. Choose an option for each features.

| Python |
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

| Backend                   |
| ------------------------- |
| local file                |
| url                       |
| S3 bucket without version |
| S3 bucket with version    |
| Sqlite database           |
| Postgres database         |

| Multi tenancy                 |
| ----------------------------- |
| Single                        |
| Multiple, share the SQL table |
| Multiple, dedicated SQL table |

| API                                               |
| ------------------------------------------------- |
| Haystack REST API                                 |
| GraphQL API alone                                 |
| GraphQL API integrated inside another via AppSync |

| Cost        | Technologies               |
| ----------- | -------------------------- |
| With server | VM, Docker, Postgres, etc. |
| Server less | AWS Lambda, Aurora         |

and you can extend these proposed scenario. You can read later, how to implement these different scenarios.

# Server API

This implementation propose two API endpoint:

- Classical [REST Haystack API](https://www.project-haystack.org/doc/Rest)
- GraphQL API

## Classical REST Haystack API

This API use the `http://<host>:<port>/haystack` url.

These API can negotiate:

- Request format (`Content-Type: text/zinc`, `application/json` or `text/csv`)
- Response format (`Accept: text/zinc, application/json, text/csv`)

The code implements all [operations](https://project-haystack.org/doc/Rest):

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

## GraphQL Haystack API

This API use the `http://<host>:<port>/graphql` url and is conforms to the schema describe in file `schema.graphql`.

### Deploy a Web server
- start the api
    - with [Flask](https://flask.palletsprojects.com/en/1.1.x/) and Haystack classical API,
        - `pip install "haystackapi[flask]"`
        - `HAYSTACK_PROVIDER='<your provider module>' haystackapi`
    - with Flask and Haystack+GraphQL API,
        - `pip install "haystackapi[flask,graphql]"`
        - `HAYSTACK_PROVIDER='<your provider module>' haystackapi`

The command line `haystackapi` accept parameters (use `haystackapi --help`)
### Providers

Different sample of provider are proposed. You can add a new one with a subclass of
`haystackapi.providers.HaystackInterface`. Then, you can implement only the method you want. The others methods are
automatically excluded in the [`../ops`](https://project-haystack.org/doc/Ops#ops) operation.

To select a provider, add the environment variable `HAYSTACK_PROVIDER`.

To create your custom Haystack API

- create a project
- In a module, create a subclass of `haystackapi.providers.HaystackInterface`
  with the name `Provider`
- add a parameter `HAYSTACK_PROVIDER` with the name of the module

We propose different providers, with the objective in mind:

- Expose the haystack files and historical data with an API
- and manage the evolution of these files with the notion of `version`.

If you want to connect the haystack API with IOT, you must extend a provider. The current providers are not connected to
IOT for simplicity.

To demonstrate this scenario, we want to publish the sample from `sample/` files from S3 bucket or from an SQL database.
We must import this ontology and time-series inside the bucket or database before to use. To manage the different
versions of files, you must use a dedicated tool, to import only the difference between versions.

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
air,phone,sensor,occupied,store,damper,enum,temp,tz,tariffHis,sp,area,site,weatherRef,elecCost,hisMode,kwSite,summary,fan,siteRef,primaryFunction,kind,cmd,geoCountry,elec,lights,geoStreet,occupiedEnd,yearBuilt,siteMeter,geoCoord,regionRef,occupiedStart,effective,equip,sitePoint,cool,ahu,hvac,costPerHour,unit,lightsGroup,discharge,zone,power,geoCity,rooftop,navName,outside,point,dis,energy,elecMeterLoad,id,geoAddr,cur,geoState,geoPostalCode,equipRef,meter,pressure,heat,return,storeNum,his,metro,stage,hisURI
,"804.552.2222",,,✓,,,,"New_York",,,3149.0ft²,✓,"@p:demo:r:23a44701-1af1bca9 Richmond, VA",,,,,,,"Retail Store",,,"US",,,"3504 W Cary St",20:00:00,1996.0,,"C(37.555385,-77.486903)",@p:demo:r:23a44701-67faf4db Richmond,10:00:00,,,,,,,,,,,,,"Richmond",,,,,"Carytown",,,@p:demo:r:23a44701-a89a6c66 Carytown,"3504 W Cary St, Richmond, VA",,"VA","23221",,,,,,1.0,,"Richmond",,
```

#### Provider SQL

This provider use an ontology imported in SQL database. Each entity is saved in a row in the JSON format.
Use `HAYSTACK_PROVIDER=haytackapi.providers.sql` to use this provider. Add the variable `HAYSTACK_DB` to describe the
link to the root table. At this time, only SuperSQLite and Postgresql was supported.

```console
$ pip install 'haystackapi[graphql,lambda]'
```

Install the corresponding database driver:

| Database | Driver                    |
| -------- | ------------------------- |
| sqlite   | `pip install supersqlite` |
| postgres | `pip install psycopg2`    |

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
air,phone,sensor,occupied,store,damper,enum,temp,tz,tariffHis,sp,area,site,weatherRef,elecCost,hisMode,kwSite,summary,fan,siteRef,primaryFunction,kind,cmd,geoCountry,elec,lights,geoStreet,occupiedEnd,yearBuilt,siteMeter,geoCoord,regionRef,occupiedStart,effective,equip,sitePoint,cool,ahu,hvac,costPerHour,unit,lightsGroup,discharge,zone,power,geoCity,rooftop,navName,outside,point,dis,energy,elecMeterLoad,id,geoAddr,cur,geoState,geoPostalCode,equipRef,meter,pressure,heat,return,storeNum,his,metro,stage,hisURI
,"804.552.2222",,,✓,,,,"New_York",,,3149.0ft²,✓,"@p:demo:r:23a44701-1af1bca9 Richmond, VA",,,,,,,"Retail Store",,,"US",,,"3504 W Cary St",20:00:00,1996.0,,"C(37.555385,-77.486903)",@p:demo:r:23a44701-67faf4db Richmond,10:00:00,,,,,,,,,,,,,"Richmond",,,,,"Carytown",,,@p:demo:r:23a44701-a89a6c66 Carytown,"3504 W Cary St, Richmond, VA",,"VA","23221",,,,,,1.0,,"Richmond",,
```

The SQL url is in form: <dialect\[+<driver>]>://\[<user>\[:<password>]@><host>\[:<port>]/<databasename>\[#<table name>]

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

_Because this provider use a local cache with the parsing version of S3 file, it's may be possible to see different
versions if AWS use multiple instances of lambda. To fix that, the environment variable `REFRESH` can be set to delay
the cache refresh (Default value is 15m). Every quarter of an hour, each lambda instance check the list of version for
this file, and refresh the cache in memory, at the same time. If a new version is published just before you start the
lambda, it's may be possible you can't see this new version. You must wait the end of the current quarter, redeploy the
lambda or update the `REFRESH`
parameter._

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

# TODO

- [ ] coverage
- [ ] MySQL
- [ ] Pypy (when pip install typed-ast running)