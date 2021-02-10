# Using with Amazon AWS

This module offers two layers to use AWS cloud. It's possible to publish the haystack files in a bucket, and use the URL
provider to expose an API (REST and GraphQL)
and it's possible to use the AWS Lambda to publish the API.

To import the dependencies:

```console
$ pip install haystackapi[lambda]
```

## AWS Bucket

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

## AWS Lambda

The code is compatible with AWS Lambda. Install this option (`pip install "haystackapi[lambda]"`)
and create a file `zappa_settings.json` with something like this:

```json
{
  "dev": {
    "profile_name": "default",
    "aws_region": "us-east-2",
    "app_function": "app.__init__.app",
    "project_name": "my_haystackapi",
    "s3_bucket": "my_haystackapi-zappa",
    "runtime": "python3.8",
    "aws_environment_variables": {
      "LOG_LEVEL": "INFO",
      "TLS_VERIFY": "False",
      "HAYSTACK_PROVIDER": "haystackapi.providers.url",
      "HAYSTACK_URL": "s3://haystackapi/carytown.zinc",
      "HAYSTACK_DB": "",
      "HAYSTACK_TS": ""
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
$ xdg-open "$HAYSTACK_ROOT_API/haystack"
$ # Try the Graphql API
$ xdg-open "$HAYSTACK_ROOT_API/graphql"
```

## AWS AppSync

Appsync is a technology to aggregate different API in one GraphQL API. It's possible to merge the haystack GraphQL with
other GraphQL API with AppSync. To do that, read [this](AppSync.md).

