# Use AWS AppSync

With AWS AppSync, it's possible to merge the Haystack GraphQL API with another GraphQL API.

## Schema

The current GraphQL schema for Hystack is [here](../schema.graphql)

## Delegate part of global GraphQL to haystack GraphQL API

In AWS AppSync,

* Create a datasource `HaystackLambda` with an AWS Lambda function
    - Select the AWS Lambda for Haystack
    - Select the region
    - and a role
* Add haystack GraphQL API
    - Import schema or merge Haystack schema with another (remove the `query` part)
    - add a tag `haystack`
    - add a resolver for the tag `haystack`
    - select `HaystackLambda` datasource
    - Enable request mapping template with the file `request-filter.vm`
    - Update the parameter
    - Enable response mapping template with the file `response-filter.vm`
    - Save the resolver
* Test a query like `{ haystack { tagValues(tag:"dis") } }`