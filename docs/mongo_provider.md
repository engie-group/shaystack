# MongoDB Provider

This provider uses an ontology imported in Mongo database. Each entity is saved in a row in the JSON format.
Use `HAYSTACK_PROVIDER=shaytack.providers.db` or `HAYSTACK_PROVIDER=shaytack.providers.mongo`
to use this provider. Add the variable `HAYSTACK_DB` to describe the link to the root table.

```console
$ pip install 'shaystack[graphql,lambda]'
```

Install the corresponding database driver:

```console
$ pip install pymongo
```

You can use `shaystack_import_db` to import a Haystack files into the database, only if the entities are modified
(to respect the notion of _Version_ with this provider). The corresponding `hisURI` time-series files are uploaded too.

```bash
shaystack_import_db <haystack file url> <db url>
```

You can use the parameters:

* `--customer` to set the customer id for all imported records
* `--reset` to clean the oldest versions before import a new one
* `--no-time-series` if you don't want to import the time-series referenced in `hisURI` tags'

To demonstrate the usage with mongodb,

```console
$ # Demo
$ # - Install the components
$ pip install 'shaystack[flask]'
$ # - Install the mongodb driver
$ pip install mongodb
$ # - Import haystack file in DB
$ shaystack_import_db sample/carytown.zinc mongodb://localhost/haystackdb#haystack
$ # - Expose haystack with API
$ HAYSTACK_PROVIDER=shaystack.providers.db \
  HAYSTACK_DB=mongodb://localhost/haystackdb#haystack \
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

The Mongo url is in form: \<mongodb\[+srv]\>://\[\<user\>\[:\<password\>]@]\<host\>\[:\<port\>]/\<database
name\>\[?\<parameters=...>]\[#\<table name\>]
See [here](https://docs.mongodb.com/manual/reference/connection-string/)

Samples:

- `mongodb://localhost/haystackdb`
- `mongodb://localhost/haystackdb#haystack`
- `mongodb+srv://localhost/haystackdb?w=majority&wtimeoutMS=2500#haystack`

Inside the Mongo url, if the password is in form `'<...>'`, and you use AWS lambda,  
the password is retrieved from the service [`secretManagers`](https://aws.amazon.com/secrets-manager/). The password
must be in form `'<secret_id|key>'`. In the secret container `secret_id` at the key `key`, the database password must be
set.

After the deployment, you can use this provider like any others providers. The haystack filter was automatically
converted to MongoDB request. Three collections were created:

- <collection_name> (`haystack` by default)
- <collection_name>_meta_datas
- <collection_name>_ts
- and some index.

The column `entity` use a json version of haystack entity (
See [here](https://project-haystack.org/doc/docHaystack/Json)).

The time-series are saved in a table `<collection_name>_ts`. If you prefer to use a dedicated time-series database,
overload the method `hisRead()` (see [Timestream provider](timestream_provider.md))

<collection_name>

| _id  | customer_id | start_datetime | end_datetime | entity |
| ---- | ----------- | -------------- | ------------ | ------ |
| id   | str         | datetime       | datetime     | bson   |

<collection_name>_meta_datas

| _id | customer_id | start_datetime | end_datetime | metatdata | cols |
| --- | ----------- | -------------- | ------------ | --------- | ---- |
| id  | str         | datetime       | datetime     | bson      | bson |

<collection_name>_ts

| _id | id  | customer_id | date_time | val | 
| --- | --- | ----------- | --------- | --- | 
| id  | str | str         | datetime  | str | 

To manage the multi-tenancy, it's possible to use different approach:

- Overload the method `get_customer_id()` to return the name of the current customer, deduce by the current API caller
- Use different tables (change the table name, `...#haystack_customer1`, `...#haystack_customer2`)
  and publish different API, one by customer.

##### Limitations

- All entities used with this provider must have an `id` tag

