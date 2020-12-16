# ReadHaystack AWS Lambda API

Haystackapi is set of API to implement [Haystack project specification](https://project-haystack.org/). It's compatible
with AWS Lambda or Flask server.

## Summary

This project contains source code to parse or dump Haystack files
([Zinc](https://www.project-haystack.org/doc/Zinc),
[Json](https://www.project-haystack.org/doc/Json),
[Csv](https://www.project-haystack.org/doc/Csv)).

To implement the [Haystack Rest API](https://www.project-haystack.org/doc/Rest), extend the class `HaystackInterface`
and publish an AWS Lambda or start a Flash server (See [Server API](#server-api).

This implementation propose two API endpoint:

- Classical [REST Haystack API](https://www.project-haystack.org/doc/Rest)
- GraphQL API

# Try it

To try this module, the best way is to download a sample of haystack file. In an empty directory,

```bash
git clone --depth 1 https://github.com/pprados/haystackapi.git sample ; \
cd sample ; \
git filter-branch --prune-empty --subdirectory-filter sample HEAD ; \
cd ..
```

The directory `sample` now has examples files.

- carytown.[csv|jon|zinc]  : The haystack ontology
- p:demo:*.zinc : sample of time series

Create a virtual environement

```bash
$ virtualenv -p python3.8 venv
source venv/bin/activate
```

Then, install the module with all options

```
$ pip install 'haystackapi[graphql,lambda]'
```

It's time to try to manipulate a grid. Start IPython or Python

```
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
...:     {'firstColumn': haystackapi.MARKER, 'secondColumn': 'supported on Python 2.7 and 3.x'},
...:     {'firstColumn': haystackapi.Coordinate(-27.4725,153.003), 'secondColumn': 'Made in Australia from local and imported ingredients'},
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
        secondColumn='supported on Python 2.7 and 3.x'
        Row    2:
        firstColumn=Coordinate(-27.4725, 153.003)
        secondColumn='Made in Australia from local and imported ingredients'
</Grid>

In [9]: print(haystackapi.dump(g))
ver:"3.0" aMarker today:2020-12-16
firstColumn metaData:"in no particular order" abc:123,secondColumn
154kg,"and counting"
M,"supported on Python 2.7 and 3.x"
C(-27.472500,153.003000),"Made in Australia from local and imported ingredients"

In [10]: print (haystackapi.dump(g,mode=haystackapi.MODE_JSON))
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
In [18]: his = g.filter("his")[0]
In [19]: ts_uri = "sample/" + his["hisURI"]
In [20]: with open(ts_uri) as f:
...:         ts = haystackapi.parse(f.read(),haystackapi.MODE_ZINC)
...:         print(ts)
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

# Server API

This implementation propose two API endpoint:

- Classical [REST Haystack API](https://www.project-haystack.org/doc/Rest)
- GraphQL API

## Classical REST Haystack API

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

This API use the `http://<host>:<port>/graphql` url and was conforms to the schema describe in file `schema.graphql`.

### Deploy a Web server
- start the api
    - with [Flask](https://flask.palletsprojects.com/en/1.1.x/) and Haystack classical API,
        - `pip install "haystackapi[flask]"`
        - `HAYSTACK_PROVIDER='<your provider module>' haystackapi`
    - with Flask and Haystack+GraphQL API,
        - `pip install "haystackapi[flask,graphql]"`
        - `HAYSTACK_PROVIDER='<your provider module>' haystackapi`

## Custom provider

To create your custom Haystack API

- create a project
- In a module, create a subclass of `haystackapi.providers.HaystackInterface`
  with the name `Provider`
- add parameter `HAYSTACK_PROVIDER` with the name of the package

### Providers

Different sample of provider are proposed. You can add a new one with a subclass of
`haystackapi.providers.HaystackInterface`. Then, you can implement only the method you want. The others methods are
automatically excluded in the [`../ops`](https://project-haystack.org/doc/Ops#ops) operation.

To select a provider, add the environment variable `HAYSTACK_PROVIDER` in the environment.

To create your custom Haystack API

- create a project
- In a module, create a subclass of `haystackapi.providers.HaystackInterface`
  with the name `Provider`
- add parameter `HAYSTACK_PROVIDER` with the name of the package

You can update others parameters (`HAYSTACK_PROVIDER`, `AWS_STACK`, `AWS_PROFILE`, `AWS_REGION`, ...)

#### Provider Ping

Use `HAYSTACK_PROVIDER=providers.ping` to use this provider. It's a very simple provider, with a tiny implementation of
all haystack operation.

```bash
$ HAYSTACK_PROVIDER=providers.ping haystackapi
```

In another console

```bash
$ curl http://localhost:3000/haystack/about
```

#### Provider URL

Use `HAYSTACK_PROVIDER=haystackapi.providers.url` to use this provider. Add the variable `HAYSTACK_URL=<url>` to expose
an ReadHaystack file via the ReadHaystack protocol. The methods `/read` and `/hisRead` was implemented. The `<url>` may
have the classic form (`http://...`, `ftp://...`) or can reference an S3 file (`s3://...`). The time series to manage
history must be referenced in the entity, with the `hisURI` tag. This URI may be relative and must be in parquet format.

```bash
$ # Demo
$ HAYSTACK_PROVIDER=haystackapi.providers.url \
  HAYSTACK_URL=sample/carytown.zinc \
  haystackapi
```

in another shell

```bash
$ curl 'http://localhost:3000/haystack/read?filter=site'
temp,tz,regionRef,occupiedStart,geoStreet,hisMode,lightsGroup,geoAddr,power,kwSite,ahu,sp,occupiedEnd,heat,phone,lights,tariffHis,weatherRef,his,zone,siteMeter,yearBuilt,kind,store,id,navName,geoState,rooftop,area,equipRef,elec,storeNum,air,outside,energy,return,geoPostalCode,unit,damper,geoCoord,metro,site,cur,point,geoCountry,summary,sitePoint,elecCost,fan,enum,pressure,hvac,stage,primaryFunction,sensor,effective,meter,occupied,discharge,dis,cmd,elecMeterLoad,geoCity,costPerHour,siteRef,cool,equip,hisURI
,"New_York",@p:demo:r:23a44701-67faf4db Richmond,10:00:00,"3504 W Cary St",,,"3504 W Cary St, Richmond, VA",,,,,20:00:00,,"804.552.2222",,,"@p:demo:r:23a44701-1af1bca9 Richmond, VA",,,,1996.0,,✓,@p:demo:r:23a44701-a89a6c66 Carytown,,"VA",,3149.0ft²,,,1.0,,,,,"23221",,,"C(37.555385,-77.486903)","Richmond",✓,,,"US",,,,,,,,,"Retail Store",,,,,,"Carytown",,,"Richmond",,,,,
```

You can use `import_s3` to import an Haystack file in s3 bucket, only if the file is modified
(to respect the notion of Version with this provider). The corresponding `hisURI` time-series files are uploaded too.

```bash
python -m haystackapi.providers.import_s3 <haystack file url> <s3 url>
```

You can use the parameters:

* `--no-compare` if you don't want to download the remote version and compare with the new version to detect an update
* `--no-time-series` if you don't want to upload the time-series referenced in `hisURI` tags'
* `--force` to force the upload, and create a new version for all files in the bucket.

Because this provider use a local cache with the parsing version of S3 file, it's may be possible to see different
versions if AWS use multiple instances of lambda. To fixe that, the environment variable `REFRESH` can be set to delay
cache refresh
(Default value is 15m). Every quarter of an hour, each lambda check the list of version for this file, and refresh the
cache in memory, at the same time. If a new version is published just before you start the lambda, it's may be possible
you can't see this version. You must wait the end of the current quarter.

#### Provider SQL

This provider use an ontology imported in SQL database. Each entity is saved in a row in the JSON format.
Use `HAYSTACK_PROVIDER=haytackapi.providers.sql` to use this provider. Add the variable `HAYSTACK_DB` to describe the
link to the table. At this time, only SuperSQLite and Postgresql was supported.

Install the corresponding driver:

| Database | Driver                    |
| -------- | ------------------------- |
| sqlite   | `pip install supersqlite` |
| postgres | `pip install psycopg2`    |

You can use `import_db` to import a Haystack file in database, only if the entities are modified
(to respect the notion of Version with this provider). The corresponding `hisURI` time-series files are uploaded too.

```bash
python -m haystackapi.providers.import_db <haystack file url> <db url>
```

You can use the parameters:

* `--customer` to set the customer id
* `--clean` to clean the oldest versions before import a new one
* `--no-time-series` if you don't want to upload the time-series referenced in `hisURI` tags'

To demonstrate the usage with sqlite,

```bash
$ # Demo
$   # Import haystack file in DB
$ python -m haystackapi.providers.import_db sample/carytown.zinc sqlite3://localhost/test.db#haystack
$   # Expose haystack with API
$ HAYSTACK_PROVIDER=haytackapi.providers.sql \
  HAYSTACK_DB=sqlite3:///test.db#haystack \
  haystackapi
```

in another shell

```bash
$ curl 'http://localhost:3000/haystack/read?filter=site'
temp,tz,regionRef,occupiedStart,geoStreet,hisMode,lightsGroup,geoAddr,power,kwSite,ahu,sp,occupiedEnd,heat,phone,lights,tariffHis,weatherRef,his,zone,siteMeter,yearBuilt,kind,store,id,navName,geoState,rooftop,area,equipRef,elec,storeNum,air,outside,energy,return,geoPostalCode,unit,damper,geoCoord,metro,site,cur,point,geoCountry,summary,sitePoint,elecCost,fan,enum,pressure,hvac,stage,primaryFunction,sensor,effective,meter,occupied,discharge,dis,cmd,elecMeterLoad,geoCity,costPerHour,siteRef,cool,equip,hisURI
,"New_York",@p:demo:r:23a44701-67faf4db Richmond,10:00:00,"3504 W Cary St",,,"3504 W Cary St, Richmond, VA",,,,,20:00:00,,"804.552.2222",,,"@p:demo:r:23a44701-1af1bca9 Richmond, VA",,,,1996.0,,✓,@p:demo:r:23a44701-a89a6c66 Carytown,,"VA",,3149.0ft²,,,1.0,,,,,"23221",,,"C(37.555385,-77.486903)","Richmond",✓,,,"US",,,,,,,,,"Retail Store",,,,,,"Carytown",,,"Richmond",,,,,
```

Inside the SQL url, if the password is empty and you use AWS lambda,  
the password is retrieved from the service [`secretManagers`](https://aws.amazon.com/secrets-manager/), with the key,
whose name is in the environment variable `HAYSTACK_DB_SECRET`. Use the key `password` to save the password.

After deployment, you can use this provider like any others providers. The haystack filter was automatically converted
to SQL. Three table was created:

- <table_name> (`haystack` by default)
- <table_name>_meta_datas
- <table_name>_ts and some index. The column `entity` use a json version of haystack entity
  (See [here](https://project-haystack.org/doc/Json)).

The time-series are save in table <table_name>_ts. If you prefer to use a dedicated time-series database, overload the
method `hisRead()`

To manage the multi-tenancy, it's possible to use different approach:

- Overload the method `get_customer_id()` to return the name of customer, deduce by the user logging
- Use different tables (change the table name, ...#haystack_customer1, ...#haystack_customer2)

# Using GraphQL API

All the providers can use invoked with a GraphQL API in place of standard Haystack Rest API. After installing the
component with the option, start the provider and use the url
`http://localhost:3000/graphql`. You can see an interface to use the ontology.

```GraphQL
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
        byid:entities(ids:["@elec-16514","@site-434051"])
        byfilter:entities(select: "id,dis" filter: "id", limit: 2)
        histories(ids:["@car-1","@bicycle-100"])
        {
            ts
            val
            coord { lat long }
        }
        country:tagValues(tag:"geoCountry")
    }
}
```

## Using with Excel or PowerBI

Because the default negotiated format is CSV, you can call these API with PowerQuery. TODO: importer le fichier sample

## Using with AWS Lambda

The code is compatible with AWS Lambda. Install this option (`pip install "haystackapi[graphql,lambda]"`)
and create a file `zappa_settings.json` with

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

update the parameters use `zappa deploy`. Then, you can the Lambda API to invoke the REST or GraphQL API.

# Data types

`haystackapi` converts the common Python data types:

## `Null`, `Boolean`, `Date`, `Time`, `Date/Time` and `strings`.

Standard Python types. In the case of Date/Time, the `tzinfo` parameter is set to the equivalent timezone provided by
the `pytz` library where possible.

## `Numbers`

Numbers without a unit are represented as `float` objects. Numbers with a unit are represented by
the `haystackapi.Quantity` custom type which has two attributes: `value` and `unit`.

## `Marker` and `Remove`

These are singletons, represented by `haystackapi.MARKER` and `haystackapi.REMOVE`. They behave and are intended to be
used like the `None` object.

## `Bin` and `XBin`

These are represented bytes array.

## `Uri`

This is an classical `Uri` for Haystack

## `Ref`

Represented by the custom type `haystackapi.Ref` which has `name` (`str`),
`has_value` (`bool`) and `value` (any type) attributes.

## `Coordinate`

Represented by the custom type `haystackapi.Coordinate`, which has `latitude` and
`longitude` types (both `float`)

## Collection `List`, `Dict` or `Grid`

A tag may be a list, a dict or another grid.

# Contribute

See [here](./Contibute.md)

# Resources

[Haystack Project](https://www.project-haystack.org/)
[Zappa](https://github.com/Miserlou/Zappa) framework
