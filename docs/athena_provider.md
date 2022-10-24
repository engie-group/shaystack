# Provider + AWS Athena

This provider extends the `DBProvider` to manage time-series with
[AWS Athena](https://docs.aws.amazon.com/athena/). 

Use `HAYSTACK_PROVIDER=shaytack.providers.athena` to use
this provider. Add the variable `HAYSTACK_DB` to describe the link to the backend to read the ontology and `HAYSTACK_TS`
to describe required elements to run Athena queries. 

The format of `HAYSTACK_TS` is :

    athena://shaystack?output_bucket_name=<S3 bucket name>&output_folder_name=<output folder>
- **output_bucket_name [REQUIRED]**: The name of the bucket in which Athena will store the query results
- **output_folder_name [REQUIRED]**: The folder name in which Athena will store the query results

### hisURI structure
**hisURI** in the ontology definition contains all the elements required to query Athena databases and retrieve time series data according to the information given inside **hisURI** whose structure should be as follows:
```
"hisURI": {
            "db_name": "data base name",
            "table_name": "table name",
            "partition_keys": "partition keys key1='value1'/key2='value2'/.../key(n)='value(n)",
            "hs_type": "type of timeseries (composit: dict or simple: float or string)",
            "hs_value_column": { 
                "column1": "float",
                "column2": "float",
                ...
                "column(n)": "float"
            },
            "hs_date_column": {
                "time": "%Y-%m-%d %H:%M:%S.%f"
            },
            "date_part_keys": {
                "year_col": "year",
                "month_col": "month",
                "day_col": "day"
            }
        }
```
- **db_name**: the name of the databases from the AWS data catalog
- **table_name**: the name of the table within the database
- **partition_keys**: one or more partition keys separated by "/" used
  to partition the data, could be partitioned by year, month, date, and hour `"partition_keys": "key1='val1'/key2='val2'"`
- **hs_type**: it could be:
  - **a composite type** like **dict** {"col1": value1, "col2": value2, ...}
  - **a simple type** like **float**, **int**, **string** or **bool**
- **hs_value_column**: if the type is **dict**, it should contain one or more column `names` and the `type` corresponding to each of them; if the type is simple, it should contain the column `name` and its `type`
- **hs_date_column**: the name of the column that represents the `timestamp` of the time series followed by ":" and the `datetime format`, for example: `"time": "%Y-%m-%d %H:%M:%S.%f"`
- **date_part_keys**: Time series can be partitioned by date elements such as year, month and day, and all partition keys used must be specified with their name used when creating the table  as follows:

      "date_part_keys":{
         "year_col": "year column name",
         "month_col": "month column name",
         "day_col": "day column name"
      }

You can create **Athena tables**, using *[AWS Glue](https://docs.aws.amazon.com/athena/latest/ug/creating-tables.html#:~:text=in%20Amazon%20S3.-,Creating%20tables%20using%20AWS%20Glue%20or%20the%20Athena%20console,-You%20can%20create)* or by running a *[DDL statement in the Athena query editor](https://docs.aws.amazon.com/athena/latest/ug/creating-tables.html#:~:text=To%20create%20a%20table%20using%20Hive%20DDL)*.

### Running Haystack Api 

```console
$ HAYSTACK_PROVIDER=shaystack.providers.athena \
  HAYSTACK_DB=sample/athena_sample.hayson.json \
  HAYSTACK_TS=athena://shaystack?output_bucket_name=bucket_name&output_folder_name=folder_name \
  shaystack
```

### Requirements
In order to use the **Athena provider**, ensure that the IAM role or another IAM principal has the required permissions to access the source data bucket and the query result bucket, as well as Athena permissions to execute Athena queries.
- **athena** – Allows principals access to Athena resources.
- **s3** – Allows the principal to write and read query results from Amazon S3, to read publically available Athena data examples that reside in Amazon S3, and to list buckets. This is required so that the principal can use Athena to work with Amazon S3.

**Example** – The following identity-based permissions policy allows actions that a user or other IAM principal requires to run queries that use Athena UDF statements

  ```{
      "Version": "2012-10-17",
      "Statement": [
          {
              "Sid": "VisualEditor0",
              "Effect": "Allow",
              "Action": [
                  "athena:StartQueryExecution",
                  "lambda:InvokeFunction",
                  "athena:GetQueryResults",
                  "s3:ListMultipartUploadParts",
                  "athena:GetWorkGroup",
                  "s3:PutObject",
                  "s3:GetObject",
                  "s3:AbortMultipartUpload",
                  "athena:StopQueryExecution",
                  "athena:GetQueryExecution",
                  "s3:GetBucketLocation"
              ],
              "Resource": [
                  "arn:aws:athena:*:MyAWSAcctId:workgroup/MyAthenaWorkGroup",
                  "arn:aws:s3:::MyQueryResultsBucket/*",
                  "arn:aws:lambda:*:MyAWSAcctId:function:OneAthenaLambdaFunction",
                  "arn:aws:lambda:*:MyAWSAcctId:function:AnotherAthenaLambdaFunction"
              ]
          },
          {
              "Sid": "VisualEditor1",
              "Effect": "Allow",
              "Action": "athena:ListWorkGroups",
              "Resource": "*"
          }
      ]
  }
  ```
Refer to this [link](https://docs.aws.amazon.com/athena/latest/ug/udf-iam-access.html) for more details on the Athena permissions policy requirements.






### Limitation
- The entities with history must have the following tags: `db_name`,`table_name`,`partition_keys`, `hs_type`,`hs_value_column`,`hs_date_column`, `date_part_keys` that will be used to build an Athena query
- Athena is a **multi tenant service** and not indeed not a low latency data store. All users are competing for resources, and your queries will get queued when there aren't enough resources available 
- More details [here](https://aws.amazon.com/athena/?whats-new-cards.sort-by=item.additionalFields.postDateTime&whats-new-cards.sort-order=desc)

