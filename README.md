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

On the server side, it also implements [Haystack Rest API](https://www.project-haystack.org/doc/Rest), useful to serve
Haystack data you host.

- We implemented two serving options See [API Server](.:#server-side-haystack-api-server): Flask and AWS Lambda
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

To see the similarities and differences between the two project, click [here](README_hszinc.md)

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
|No data, just testing|`export HAYSTACK_PROVIDER=haystackapi.providers.ping haystackapi`||
|Data on http server|`export HAYSTACK_PROVIDER=haystackapi.providers.url HAYSTACK_URL=http://... haystackapi`|[More...](README_url_provider.md)|
|Data on ftp server|`export HAYSTACK_PROVIDER=haystackapi.providers.url HAYSTACK_URL=ftp://... haystackapi`|[More...](README_url_provider.md)|
|Data on local filesystem|`export HAYSTACK_PROVIDER=haystackapi.providers.url HAYSTACK_URL=file://... haystackapi`|[More...](README_url_provider.md)|
|Data on AWS S3 Bucket|`export HAYSTACK_PROVIDER=haystackapi.providers.url HAYSTACK_URL=s3://... haystackapi`|Remember to install aws support and boto3 python module. [More...](README_url_provider.md)|
|Data in a SuperSQLite database|`export HAYSTACK_PROVIDER=haystackapi.providers.sql HAYSTACK_URL=sqlite3://... haystackapi`|Remember to install supersqlite python module. [More...](README_url_provider.md)|
|Data in a Postgresql database|`export HAYSTACK_PROVIDER=haystackapi.providers.sql HAYSTACK_URL=postgres://... haystackapi`|Remember to install psycopg2 python module. [More...](README_url_provider.md)|
|Data in a database and Time series in AWS Time Stream|`export HAYSTACK_PROVIDER=haystackapi.providers.sql_ts HAYSTACK_URL=postgres://... HAYSTACK_TS=timestream:://... haystackapi`|[More...](README_sql_ts_provider.md)|
|Custom|`export HAYSTACK_PROVIDER=haystackapi.providers.<your module name>`|Write your own subclass of `haystackapi.providers.HaystackInterface haystackapi`. Non implemented methods will be automatically excluded in [`ops`](https://project-haystack.org/doc/Ops#ops) operation output|

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

### Using GraphQL API

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

```
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

```
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

### Specification extension

To manage the history of ontologies, it's possible to add a parameter almost all request: `Version`
This parameter must have the datetime when you want to ask the ontology. The result is the *vue*
of these data at this time.

To return only some tag, it's possible to add a parameter `filter` in `read` request.

The syntax to analyse the daterange in `hisRead` is extended to accept a comma without value before or after (`date,`
, `,datetime`, etc.)

### Using AWS

Read [more...](README_aws.md)

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

## Using with Excel or PowerBI

Because the default negotiated format is CSV, you can call the REST API with PowerQuery or Excel. Try the sample file
['HaystackAPI.xlsm'](HaystackAPI.xlsm) and set a correct haystack url
(http://10.0.2.2:3000/haystack with a local virtual windows). You can load all the data inside Excel table.

# Optional part

Haystack component propose different optional parts.

| Option  | Feature                                         |
| ------- | ----------------------------------------------- |
| flask   | Expose API with Flask HTTP server               |
| graphql | Expose Graphql API with Flask HTTP server       |
| lambda  | Add compatibility with AWS Lambda and S3 bucket |

Use `pip install "haystackapi[_<options>_]"`, like:

- `pip install "haystackapi[flask,graphql,lambda]"`

# Data types

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

See [here](./README_Contribute.md)

# Resources

- [Haystack Project](https://www.project-haystack.org/)
- [Zappa](https://github.com/Miserlou/Zappa) framework

# License

See [LICENCE](LICENSE-2.0.txt) file

# TODO
- [ ] coverage
- [ ] MySQL
- [ ] Pypy (when pip install typed-ast running)
- [ ] Implements watch in GraphQL
- [ ] Implements *write* in GraphQL
- [ ] Docker images with ARM