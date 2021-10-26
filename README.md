![Logo](https://github.com/engie-group/shaystack/blob/develop/docs/logo.png?raw=true)

# Shift-4-Haystack


The [full documentation is here](https://engie-group.github.io/shaystack/)

# About Haystack, and who is it for

[Haystack project](https://project-haystack.org/) is an open source initiative to standardize semantic data models for
Internet Of Things. It enables interoperability between any IoT data producer and consumer, mainly in the Smart Building
area.

Haystack core data model is the Grid, it can be serialized in many formats,
mainly [Zinc](https://www.project-haystack.org/doc/docHaystack/Zinc),
[Trio](https://www.project-haystack.org/doc/docHaystack/Trio)
[Json](https://www.project-haystack.org/doc/docHaystack/Json)
and [Csv](https://www.project-haystack.org/doc/docHaystack/Csv)

# About this project

This project implements client side haystack code. Useful to parse or dump Haystack files
([Zinc](https://www.project-haystack.org/doc/docHaystack/Zinc),
[Json](https://www.project-haystack.org/doc/docHaystack/Json),
[Trio](https://www.project-haystack.org/doc/docHaystack/Trio)
and [Csv](https://www.project-haystack.org/doc/docHaystack/Csv)).

On the server side, it also implements [Haystack HTTP API](https://project-haystack.org/doc/docHaystack/HttpApi), useful
to serve Haystack data you host.

- We implemented different serving options See [API Server](#server-side-haystack-api-server)
    - Each offering two API endpoints:
      - Classical Haystack HTTP API
      - GraphQL API
- We introduced and implemented the *Provider* concept, which handles various options in terms on haystack data
  location:
    - Local or remote file system (including AWS S3)
    - Local or remote relational database
    - Local or remote Mongo database
    - Can be extends with optional AWS Time Stream use for Time Series
    - Other custom data location can be handled by extending `shaystack.providers.HaystackInterface`

# Table of contents

- [Quick link](https://engie-group.github.io/shaystack#quick-link)
- [About Haystack, and who is it for](https://engie-group.github.io/shaystack#about-haystack-and-who-is-it-for)
- [About this project](https://engie-group.github.io/shaystack#about-this-project)
- [History](https://engie-group.github.io/shaystack#history)
- [Client side: Haystack client python module](https://engie-group.github.io/shaystack#client-side-haystack-client-python-module)
  - [Inspect the data with code](https://engie-group.github.io/shaystack#inspect-the-data-with-code)
  - [Python API](https://engie-group.github.io/shaystack#python-api)
  - [Data science](https://engie-group.github.io/shaystack#data-science)
- [Features](https://engie-group.github.io/shaystack#features)
- [Server Side: Haystack API Server](https://engie-group.github.io/shaystack#server-side-haystack-api-server)
  - [API Server deployment](https://engie-group.github.io/shaystack#api-server-deployment)
    - [Installing](https://engie-group.github.io/shaystack#installing)
    - [Choosing and configuring your provider](https://engie-group.github.io/shaystack#choosing-and-configuring-your-provider)
    - [Starting the server](https://engie-group.github.io/shaystack#starting-the-server)
- [Using Haystack API with UI](https://engie-group.github.io/shaystack#using-haystack-api-with-ui)
- [Using GraphQL API](https://engie-group.github.io/shaystack#using-graphql-api)
- [Specification extension](https://engie-group.github.io/shaystack#specification-extension)
- [Haystack filter](https://engie-group.github.io/shaystack#haystack-filter)
- [Add Haystack API to an existing project](https://engie-group.github.io/shaystack#add-haystack-api-to-an-existing-project)
- [Using AWS](https://engie-group.github.io/shaystack#using-aws)
- [Docker](https://engie-group.github.io/shaystack#docker)
- [Using with Excel or PowerBI](https://engie-group.github.io/shaystack#using-with-excel-or-powerbi)
- [Optional part](https://engie-group.github.io/shaystack#optional-part)
- [Data types](https://engie-group.github.io/shaystack#data-types)
  - [`Null`, `Boolean`, `Date`, `Time`, `Date/Time` and `strings`.](https://engie-group.github.io/shaystack#null-boolean-date-time-datetime-and-strings)
  - [`Numbers`](https://engie-group.github.io/shaystack#numbers)
  - [`Marker` and `Remove`](https://engie-group.github.io/shaystack#marker-and-remove)
  - [`Bin` and `XBin`](https://engie-group.github.io/shaystack#bin-and-xbin)
  - [`Uri`](https://engie-group.github.io/shaystack#uri)
  - [`Ref`](https://engie-group.github.io/shaystack#ref)
  - [`Coordinate`](https://engie-group.github.io/shaystack#coordinate)
  - [Collection `List`, `Dict` or `Grid`](https://engie-group.github.io/shaystack#collection-list-dict-or-grid)
- [Contributing](https://engie-group.github.io/shaystack#contributing)
- [Resources](https://engie-group.github.io/shaystack#resources)
- [License](https://engie-group.github.io/shaystack#license)
- [TODO](#todo)

[Try it with colab?](https://colab.research.google.com/github/pprados/shaystack/blob/develop/haystack.ipynb)


[Try it with AWS Lambda?](https://skz7riv2yk.execute-api.us-east-2.amazonaws.com/dev)

and the [documentation of API is here](https://engie-group.github.io/shaystack/api/shaystack/index.html)
