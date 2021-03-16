db.![Shift-Haystack](logo.png)

| The API is not stable and can be changed without any notice. |
| --------------------------------------------------------- |

| This is a pre-release version |
| ----------------------------- |

To use the release candidate package hosted in **test.pypi.org**, use

```bash
export PIP_INDEX_URL=https://test.pypi.org/simple
export PIP_EXTRA_INDEX_URL=https://pypi.org/simple
```

Shift-for-Haystack is a set of API to implement [Haystack project specification](https://project-haystack.org/). It's
compatible with moderne Python with typing, Flask server in data center, Edge (Raspberry?) or in AWS Lambda function.

## About Haystack, and who is it for

[Haystack project]((https://project-haystack.org/)) is an open source initiative to standardize semantic data models for
Internet Of Things. It enables interoperability between any IoT data producer and consumer, mainly in the Smart Building
area.

Haystack core data model is the Grid, it can be serialized in many formats,
mainly [Zinc](https://www.project-haystack.org/doc/Zinc),
[Trio](https://www.project-haystack.org/doc/Trio)
[Json](https://www.project-haystack.org/doc/Json)
and [Csv](https://www.project-haystack.org/doc/Csv)

## About this project

This project implements client side haystack code. Useful to parse or dump Haystack files
([Zinc](https://www.project-haystack.org/doc/Zinc),
[Json](https://www.project-haystack.org/doc/Json),
[Trio](https://www.project-haystack.org/doc/Trio)
and [Csv](https://www.project-haystack.org/doc/Csv)).

On the server side, it also implements [Haystack Rest API](https://www.project-haystack.org/doc/Rest), useful to serve
Haystack data you host.

- We implemented different serving options See [API Server](.:#server-side-haystack-api-server)
    - Each offering two API endpoints:
        - Classical REST Haystack API
        - GraphQL API
- We introduced and implemented the *Provider* concept, which handles various options in terms on haystack data
  location:
    - Local or remote file system (including AWS S3)
    - Local or remote relational database
    - Local or remote Mongo database
    - Can be extends with optional AWS Time Stream use for Time Series
    - Other custom data location can be handled by extending
      `shaystack.providers.HaystackInterface`

# History

This project is a fork of [hszinc](https://github.com/widesky/hszinc)
(Thanks to the team). The proposed evolutions were too big to be accepted in a pull request.

To see the similarities and differences between the two project, click [here](hszinc.md)

# Client side: Haystack client python module

To try the client side python module included in this project, the best way is to download a sample of haystack files.
First, create a working directory.

```console
$ mkdir $TMP/haystack
$ cd $TMP/haystack
```

Download and
unzip [sample zip file](https://downgit.github.io/#/home?url=https://github.com/pprados/shaystack/tree/develop/sample)
in this directory.

```console
$ unzip sample
```

The directory `sample` now contains:

- `carytown.[csv|jon|zinc|trio]`: A public reference haystack ontology
- `p:demo:*.zinc`: A sample of time series data (`ts`,`val` zinc format)

Create a virtual environment

```console
$ virtualenv -p python3.8 venv
$ source venv/bin/activate
```

Then, install the module with all options

```console
$ pip install "shaystack[flask,graphql,lambda]"
```

## Inspect the datas with code

[`haystack.ipynb`](https://github.com/pprados/shaystack/blob/develop/haystack.ipynb) jupyter notebook contains code to
read, filter, manipulate and print `Grid` objects containing haystack data.

# Python API

The [documentation of the API is here](api/shaystack/).

# Data science

It's easy to convert a grid to a dataframe.

```python
import shaystack
import panda

with open("file.zinc") as f:
    grid = shaystack.parse(f.read(), shaystack.MODE_ZINC)

df = panda.DataFrame(grid.filter("point and co2e"))  # Convert grid to data frame
```

# Features

Shift-4-Haystack is agile and can be deployed in different scenarios. Choose an option for each feature.

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

| Haystack backend                  |
| --------------------------------- |
| local file                        |
| url                               |
| S3 bucket without version         |
| S3 bucket with version            |
| Sqlite database                   |
| Postgres database                 |
| Mongo database                    |
| haystack backend + AWS Timestream |

| Multi tenancy                 |
| ----------------------------- |
| Single tenancy                |
| Multiple, shared SQL table    |
| Multiple, dedicated SQL table |

| API                                               |
| ------------------------------------------------- |
| Haystack REST API                                 |
| Standalone GraphQL API                            |
| GraphQL API integrated inside another via AppSync |

| Serverless  | Technologies               |
| ----------- | -------------------------- |
| No          | VM, Docker, Postgres, etc. |
| Yes         | AWS Lambda, Aurora         |

and you can extend these proposed scenario. You can see below, how to install these different scenarios.

# Server Side: Haystack API Server

This implementation can offer two API endpoints:

- Classical [REST Haystack](https://www.project-haystack.org/doc/Rest)
    - Available on `http://<host>:<port>/haystack`
- GraphQL
    - Available on `http://<host>:<port>/graphql` and compliant
      with [`schema.graphql`](https://github.com/pprados/shaystack/blob/develop/schema.graphql)

This API can negotiate:

- Request format (`Content-Type: text/zinc`, `text/trio`, `application/json` or `text/csv`)
- Response format (`Accept: text/zinc, text/trio, application/json, text/csv`)

These [operations](https://project-haystack.org/doc/Rest) are implemented in both endpoints:

- [about](https://project-haystack.org/doc/Ops#about)
- [ops](https://project-haystack.org/doc/Ops#ops)
- [formats](https://project-haystack.org/doc/Ops#formats)
- [read](https://project-haystack.org/doc/Ops#read)
- [hisRead](https://project-haystack.org/doc/Ops#hisRead)
- [nav](https://project-haystack.org/doc/Ops#nav)
- [invokeAction](https://project-haystack.org/doc/Ops#invokeAction)

These [operations](https://project-haystack.org/doc/Rest) are implemented only in classical endpoint, with real-time
datas:

- [watchSub](https://project-haystack.org/doc/Ops#watchSub)
- [watchUnsub](https://project-haystack.org/doc/Ops#watchUnsub)
- [watchPoll](https://project-haystack.org/doc/Ops#watchPoll)
- [pointWrite](https://project-haystack.org/doc/Ops#pointWrite)
- [hisWrite](https://project-haystack.org/doc/Ops#hisWrite)

## API Server deployment

This layer implement the standard HaystackAPI with different providers (URL, S3, Postgres, MongoDB, etc.)

### Installing

Using `pip install`. You can add the support of some options:

- `pip install "shaystack[flask]"` allows you to use a local [Flask](https://flask.palletsprojects.com/en/1.1.x/)
  server
- `pip install "shaystack[aws]"` allows you to:
    - Serve the API in an AWS Lambda function
    - Expose haystack data located in an AWS S3 Bucket
- `pip install "shaystack[flask,graphql]"` allows you to:
    - Expose the `/graphql` endpoint in addition to the classical `/haystack` endpoint

You can mix two or more options, if you need them all, use `pip install "shaystack[flask,graphql,aws]"`

### Choosing and configuring your provider

Depending on where and how your haystack data is stored, you need to choose an existing Provider or implement your own
by extending `shaystack.providers.HaystackInterface`

|Where is data stored|Shell command|Miscellaneous|
|---|---|---|
|No data, just testing|`HAYSTACK_PROVIDER=shaystack.providers.ping \`<br/>` shaystack`||
|Data on http server|`HAYSTACK_PROVIDER=shaystack.providers.db \`<br/>` HAYSTACK_DB=http://... \`<br/>` shaystack`|[More...](url_provider.md)|
|Data on ftp server|`HAYSTACK_PROVIDER=shaystack.providers.db \`<br/>` HAYSTACK_DB=ftp://... \`<br/>` shaystack`|[More...](url_provider.md)|
|Data on local filesystem|`HAYSTACK_PROVIDER=shaystack.providers.db \`<br/>` HAYSTACK_DB=file://... \`<br/>` shaystack`|[More...](url_provider.md)|
|Data on AWS S3 Bucket|`HAYSTACK_PROVIDER=shaystack.providers.db \`<br/>` HAYSTACK_DB=s3://... \`<br/>` shaystack`|Remember to install aws support and boto3 python module. [More...](url_provider.md)|
|Data in a SuperSQLite database|`HAYSTACK_PROVIDER=shaystack.providers.db \`<br/>` HAYSTACK_DB=sqlite3://... \`<br/>` shaystack`|Remember to install supersqlite python module. [More...](sql_provider.md)|
|Data in a Postgresql database|`HAYSTACK_PROVIDER=shaystack.providers.db \`<br/>` HAYSTACK_DB=postgres://... \`<br/>` shaystack`|Remember to install psycopg2 python module. [More...](sql_provider.md)|
|Data in a MongoDB|`HAYSTACK_PROVIDER=shaystack.providers.db\`<br/>`HAYSTACK_DB=mongodb+srv:://...\`<br/>` shaystack`|Remember to install pymongo python module. [More...](mongo_provider.md)|
|Data in a database and Time series in AWS Time Stream|`HAYSTACK_PROVIDER=shaystack.providers.timestream\`<br/>`HAYSTACK_DB=postgres://...\`<br/>`HAYSTACK_TS=timestream:://...\<br /> shaystack`|[More...](timestream_provider.md)|
|Custom|`HAYSTACK_PROVIDER=shaystack.providers.<your module name>`|Write your own subclass of `shaystack.providers.HaystackInterface shaystack`.|

Note: Existing providers are not connected to IOT for simplicity. If you want to connect the haystack API with IOT, you
must implement a custom provider.

### Starting the server

Set some environment variables, and use the command `shaystack` (check `shaystack --help` for parameters)

We propose different providers, with the objective in mind:

- Expose the haystack files and historical data with an API
- and manage the evolution of these files with the notion of `version`.

To demonstrate this scenario, we want to publish the sample from `sample/` files from S3 bucket or from an SQL database.
We must import this ontology and time-series inside the bucket or database before to use. To manage the different
versions of files, you must use a dedicated tool, to import only the difference between versions.

### Using Haystack API with UI

Now, it's time to manipulate the ontology.

For the demonstration,

```console
$ # Demo
$ # - Install components
$ pip install 'shaystack[graphql]'
$ # - Expose haystack with GraphQL API
$ HAYSTACK_PROVIDER=shaystack.providers.db \
  HAYSTACK_DB=sample/carytown.zinc \
  shaystack
```

In another shell

```console
$ # - Open the GraphQL console
$ xdg-open http://localhost:3000/haystack
```

A javascript console is proposed to ask the datas. It's possible to add several API to merge the result from different
sources of data.

![Haystack UI](haystack-ui.png)

For example, one datasource comes from a ETL to expose the ontology of the inventory and energy bills from the
accounting department in a S3 bucket. The second datasource is the BMS (Building Management System)
compatible with Haystack, with the real-time data. If the entities use the same `id`, all the information were merged.
The same filter was apply for each API.

### Using GraphQL API

All the providers can be invoked with a GraphQL API in place of the standard Haystack Rest API. After installing the
component with the good option (`pip install 'shaystack[graphql]'`), start the provider and use the url
`http://localhost:3000/graphql`. You can see an interface to use the ontology.

For the demonstration,

```console
$ # Demo
$ # - Install components
$ pip install 'shaystack[graphql]'
$ # - Expose haystack with GraphQL API
$ HAYSTACK_PROVIDER=shaystack.providers.db \
  HAYSTACK_DB=sample/carytown.zinc \
  shaystack
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

### Specification limitation

At this time, in a filter, it's only possible to compare with a number.

- `geoPostalCode > 50000` // Ok
- `curVal > 38°` // Ok
- `date > 2010-03-11T23:55:00-05:00` // Not implemented
- `name > "hello"` // Not implemented

The specification is not clear.

### Specification extension

To manage the history of ontologies, it's possible to add a parameter almost all request: `Version`
This parameter must have the datetime when you want to ask the ontology. The result is the *vue*
of these data at this time.

To return only some tag, it's possible to add a parameter `select` in `read` request.

```python
grid.select("id,dis")
grid.select("!hisURL")
```

The syntax to analyse the daterange in `hisRead` is extended to accept a comma without value before or after (`date,`
, `,datetime`, etc.)

### Haystack filter

A big part of the code is to convert the haystack *filter* to database request. We implemented a conversion to different
languages:

- python
- sqlite
- postegresl
- mongodb

For the developer point of view, it may be interesting to analyse the translation. We propose a tool for that.

```console
$ shaystack_repl
(Cmd) ?

Documented commands (type help <topic>):
========================================
help

Undocumented commands:
======================
bye  mongo  pg  python  sqlite

(Cmd) 
```

Enter the language followed by the haystack filter.

```console
(Cmd) python site or point
def _gen_hsfilter_0(_grid, _entity):
  return ((id(_get_path(_grid, _entity, ['site'])) !=  id(NOT_FOUND)) or (id(_get_path(_grid, _entity, ['point'])) !=  id(NOT_FOUND)))

(Cmd) pg site or point
-- site or point
SELECT t1.entity
FROM haystack as t1
WHERE
'2020-10-01T00:00:00+00:00' BETWEEN t1.start_datetime AND t1.end_datetime
AND t1.customer_id='customer'
AND t1.entity ?| array['site', 'point']
LIMIT 1
```

### Add Haystack API to an existing project

The flexibility of the project allows many integration scenarios.
![path for integration](integration-shaystack.svg)

Add features from left to right. At differents levels, you can publish an API. The shortest way is to export a haystack
file to an s3 bucket and publish it via an API.

### Using AWS

Read [more...](AWS.md)

### Docker

The `Dockerfile` can be used to generate an image with a set of parameter.

```console
$ # Get docker file
$ wget https://github.com/pprados/shaystack/blob/develop/Dockerfile
$ # Build the image
$ docker build -t shaystack .
$ # Run and customize the image
$ docker run -p 3000:3000 \
  -e HAYSTACK_PROVIDER=shaystack.providers.db \
  -e HAYSTACK_DB=https://shaystack.s3.eu-west-3.amazonaws.com/carytown.zinc \
  -e REFRESH=15 \
  shaystack 
```

## Using with Excel or PowerBI

Because the default negotiated format is CSV, you can call the REST API with PowerQuery or Excel. Try the sample file
['SHaystack.xlsm'](SHaystack.xlsm) and set a correct haystack API url
(http://10.0.2.2:3000/haystack with a local virtual windows). You can load all the data inside Excel table.

# Optional part

Haystack component propose different optional parts.

| Option  | Feature                                         |
| ------- | ----------------------------------------------- |
| flask   | Expose API with Flask HTTP server               |
| graphql | Expose Graphql API with Flask HTTP server       |
| lambda  | Add compatibility with AWS Lambda and S3 bucket |

Use `pip install "shaystack[_<options>_]"`, like:

- `pip install "shaystack[flask,graphql,lambda]"`

# Data types

Shift-4-haystack converts the common Python data types:

### `Null`, `Boolean`, `Date`, `Time`, `Date/Time` and `strings`.

In the case of Date/Time, the `tzinfo` parameter is set to the equivalent timezone provided by the `pytz` library where
possible.

### `Numbers`

Numbers without a unit are represented as `float` objects. Numbers with a unit are represented by
the `shaystack.Quantity` custom type which has two attributes: `value` and `unit`. The unit use
the [Pint](https://pint.readthedocs.io/en/stable/) framework to manage and convert unit.

### `Marker` and `Remove`

These are singletons, represented by `shaystack.MARKER` and `shaystack.REMOVE`. They behave and are intended to be used
like the `None` object.

### `Bin` and `XBin`

These are represented bytes array with specific MIME type. Accept `hex` or `b64` to encode and decode the bytes array.

### `Uri`

This is a classical `Uri` for Haystack

### `Ref`

Represented by the custom type `shaystack.Ref` which has `name` (`str`)
and `value` attributes. The `name` must be conforme with the haystack specification.

### `Coordinate`

Represented by the custom type `shaystack.Coordinate`, which has `latitude` and
`longitude` types (both `float`)

### Collection `List`, `Dict` or `Grid`

A tag may be a list, a dict or another grid (recursive grid). To be used with care.

# Contributing

See [here](contributing.md)

# Resources

- [Haystack Project](https://www.project-haystack.org/)
- [Zappa](https://github.com/Miserlou/Zappa) framework

# License

See [LICENCE](LICENSE) file

# TODO

- [X] S3
- [X] Sqlite
- [X] Postgres
- [ ] MySQL
- [X] MongoDB
- [ ] Implements watch in GraphQL
- [ ] Implements *write* in GraphQL
- [ ] A version with FastAPI
- [ ] Pypy (when pip install typed-ast running)
- [ ] Docker images with ARM