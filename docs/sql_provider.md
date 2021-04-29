# SQL Provider

This provider uses an ontology imported in SQL database. Each entity is saved in a row in the JSON format.
Use `HAYSTACK_PROVIDER=shaytack.providers.db` or `HAYSTACK_PROVIDER=shaytack.providers.sql`
to use this provider. Add the variable `HAYSTACK_DB` to describe the link to the root table. At this time, only
SuperSQLite, Postgresql, MySQL and Athena were supported.

```console
$ pip install 'shaystack[graphql,lambda]'
```

Install the corresponding database driver:

| Database | Driver                                              |
| -------- | --------------------------------------------------- |
| sqlite   | `pip install supersqlite` (`apt install build-essential` before, and may take several minutes)|
| postgres | `pip install psycopg2`                              |
|          | or `pip install psycopg2-binary`                    |
| mysql    | `pip install pymysql cryptography`                  |
| athena   | install the postgres or mysql driver                |

You can use `shaystack_import_db` to import a Haystack files into the database, only if the entities are modified
(to respect the notion of _Version_ with this provider). The corresponding `hisURI` time-series files are uploaded too.

```bash
shaystack_import_db <haystack file url> <db url>
```

You can use the parameters:

* `--customer` to set the customer id for all imported records
* `--reset` to clean the oldest versions before import a new one
* `--no-time-series` if you don't want to import the time-series referenced in `hisURI` tags'

To demonstrate the usage with sqlite,

```console
$ # Demo
$ # - Install the components
$ pip install 'shaystack[flask]'
$ # - Install the sqlite driver
$ pip install supersqlite
$ # - Import haystack file in DB
$ shaystack_import_db sample/carytown.zinc sqlite3:///test.db#haystack
$ # - Expose haystack with API
$ HAYSTACK_PROVIDER=shaystack.providers.db \
  HAYSTACK_DB=sqlite3:///test.db#haystack \
  shaystack
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

The SQL url is in form: <dialect\[+\<driver\>]>://\[\<user\>\[:\<password\>]@]\<host\>\[:\<port\>]/\<database
name\>\[#\<table name\>]

Samples:

- `sqlite3:///test.db#haystack`
- `sqlite3://localhost/test.db`
- `sqlite3+supersqlite.sqlite3:///test.db#haystack`
- `postgres://username:password@172.17.0.2:5432/postgres`
- `mysql://username:password@172.17.0.2:5432/haystackdb`

Inside the SQL url, if the password is in form `'<...>'`, and you use AWS lambda,  
the password is retrieved from the service [`secretManagers`](https://aws.amazon.com/secrets-manager/). The password
must be in form `'<secret_id|key>'`. In the secret container `secret_id` at the key `key`, the database password must be
set.

After the deployment, you can use this provider like any others providers. The haystack filter was automatically
converted to SQL. Three tables were created:

- <table_name> (`haystack` by default)
- <table_name>_meta_datas
- <table_name>_ts
- and some index.

The column `entity` use a json version of haystack entity (
See [here](https://project-haystack.org/doc/docHaystack/Json)).

The time-series are saved in a table `<table_name>_ts`. If you prefer to use a dedicated time-series database, overload
the method `hisRead()` (see [Timestream provider](timestream_provider.md))

<table_name>

| id  | customer_id | start_datetime | end_datetime | entity |
| --- | ----------- | -------------- | ------------ | ------ |
| str | str         | datetime       | datetime     | json   |

<table_name>_meta_datas

| customer_id | start_datetime | end_datetime | metatdata | cols |
| ----------- | -------------- | ------------ | --------- | ---- |
| str         | datetime       | datetime     | json      | json |

<table_name>_ts

| id  | customer_id | date_time | val | 
| --- | ----------- | --------- | --- | 
| str | str         | datetime  | str | 

To manage the multi-tenancy, it's possible to use different approach:

- Overload the method `get_customer_id()` to return the name of the current customer, deduce by the current API caller
- Use different tables (change the table name, `...#haystack_customer1`, `...#haystack_customer2`)
  and publish different API, one by customer.

##### Limitations

- All entities used with this provider must have an `id` tag
- SQLite can not manage parentheses with SQL Request with `UNION` or `INTERSECT`. Some complexe haystack request can not
  generate a perfect translation to SQL.

