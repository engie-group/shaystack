# Delegate part of top GraphQL query with AWS AppSync

## Print the current haystack schema

```bash
python app/blueprint_graphql.py
```

## Delegate part of global GraphQL to haystack GraphQL API
In AWS AppSync, 
* import the full schema or inject the partial schema
in another schema.
* Create a datasource `HaystackLambda` with AWS Lambda function
    - Select the AWS Lambda for Haystack
    - Select the region
    - and a role
* Add haystack GraphQL API
    - Import schema or merge Haystack schema with another
    - add a resolver in the tag `haystack'
    - select `HaystackLambda` datasource
    - Enable request mapping template with the file `request-filter.json`
    - Update the parameter
    - Enable response mapping template with the file `response-filter.json`
    - Save the resolver
* Test a query like `{ haystack { about } }`  # FIXME