# Provider + AWS Time stream

This provider extends the `DBProvider` to manage time-series with
[AWS Time stream](https://docs.aws.amazon.com/timestream/). Use `HAYSTACK_PROVIDER=shaytack.providers.timestream` to use
this provider. Add the variable `HAYSTACK_DB` to describe the link to the backend to read the ontology and `HAYSTACK_TS`
to describe the link to *AWS Time stream*. The format of `HAYSTACK_TS` is :

`timestream://\<database\>[?mem_ttl=<memory retention in hour>&mag_ttl=<magnetic retention in day>][#<tablename>]`

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

```console
$ HAYSTACK_PROVIDER=shaystack.providers.timestream \
  HAYSTACK_DB=sample/carytown.zinc \
  HAYSTACK_TS=timestream://SHaystackDemo/?mem_ttl=1&mag_ttl=100#haystack \
  shaystack
```

With this provider, all the time-series are inserted in AWS Time Stream. You can use `shaystack_import_db` with a third
parameter to describe the link to the time-series database:

```console
$ shaystack_import_db sample/carytown.zinc \
    sample/carytown.zinc \
    timestream://SHaystackDemo
```

##### Limitation

- The entities with history must have a tag `kind` to describe the type of values and a tag `id`
- AWS Time stream refuse to import a data outside the memory windows delays.
  See [here](https://docs.aws.amazon.com/timestream/latest/developerguide/API_RejectedRecord.html)

