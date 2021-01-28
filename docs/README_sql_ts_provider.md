# Provider SQL + AWS Time stream

This provider extends the [SQL Provider](README_sql_provider.md) to manage time-series with
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
$ HAYSTACK_PROVIDER=haystackapi.providers.sql_ts \
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

