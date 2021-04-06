# Use AWS AppSync

<!--TOC-->

- [Use AWS AppSync](#use-aws-appsync)
  - [Schema](#schema)
  - [Delegate part of global GraphQL to haystack GraphQL API](#delegate-part-of-global-graphql-to-haystack-graphql-api)

<!--TOC-->

With AWS AppSync, it's possible to merge the Haystack GraphQL API with another GraphQL API.

## Schema

The current GraphQL schema for Haystack
is [here](https://raw.githubusercontent.com/engie-group/shaystack/develop/schema.graphql)

## Delegate part of global GraphQL to haystack GraphQL API

This sample demonstrates how it's possible to delegate a part of GraphQL request to Haystack GraphQL API with AWS
AppSync.

In the AWS AppSync console:

* First, deploy your AWS Lambda function with Haystack GraphQL API
* In AppSync, build from scratch a new GraphQL API with the name `SHaystack`
* Create a datasource `HaystackLambda` with an AWS Lambda function
  - Select "Lambda Function"
  - Select the AWS Lambda for Haystack
  - Select the region
  - and a role

![alt New Data Source][newDataSource]

* Create a function
  - Choose the data source `SHaystackLambda`
  - Function name `SHaystackWrapper`
  - Description `Delegate part of Graphql request to Haystack GraphQL API`
  - import the body
    of [`request-filter.json`](https://raw.githubusercontent.com/engie-group/shaystack/develop/AWS_appsync/request-filter.json)
    inside the
    `Configure the request mapping template`
  - import the body
    of [`response-filter.json`](https://raw.githubusercontent.com/engie-group/shaystack/develop/AWS_appsync/response-filter.json)
    inside the
    `Configure the response mapping template`
  - ask the API URL (`zappa status --json | jq -r '."API Gateway URL"'`).
  - You must receive something like `https://jihndyzv6h.execute-api.us-east-2.amazonaws.com/dev`. Extract only the host
    name.
  - Inside the request filter:
    - The prefix must be set in the variable `$apiId` (`#set($apiId = "jihndyzv6h"))
    - Update the variable `$region` (`#set($region = "us-east-2")`)

![alt New Data Source][newFunction]

* Import the schema
  - Copy the body of [`schema.graphql`](https://raw.githubusercontent.com/engie-group/shaystack/develop/schema.graphql)
    in the schema of AppSync
  - Save the schema
  - At the end of the Resolver list, attach a resolver for the filed `haystack`

![alt Attach Resolver][attachResolver]

- select the datasource `HaystackLambda`
- Convert to pipeline resolver and add the function `SHaystackWrapper`
- Create and save the resolver

![alt Create Pipeline Resolver][createPipelineResolver]

* Test a query
  - like `{ haystack { tagValues(tag:"dis") } }`

![alt Query][query]

Now, you can **extend** the AppSync schema and attach others API in the endpoint.

[newDataSource]: New_Data_Source.png "New Data Source"

[newFunction]: New_Function.png "New Function"

[attachResolver]: Attach_Resolver.png "Attach Resolver"

[createPipelineResolver]: Create_Pipeline_Resolver.png "Create Pipeline resolver"

[query]: Queries.png "Query"