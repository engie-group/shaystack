Welcome to haystackAPI's documentation!
=======================================

`Haystack project`_ is an open source initiative to standardize semantic data models for
Internet Of Things. It enables interoperability between any IoT data producer and consumer, mainly in the Smart Building
area.

Haystack core data model is the Grid, it can be serialized in many formats,
mainly `Zinc`_, `Json`_ and `Csv`_.

About this project
------------------

This project implements client side haystack code. Useful to parse or dump Haystack files
(`Zinc`_, `Json`_ and `Csv`_).

On the server side, it also implements
`Haystack Rest API`_, useful to serve Haystack data you host.

- We implemented two serving options (See [API Server](#Server Side Haystack)): Flask and AWS Lambda
    - Each offering two API endpoints:
        - Classical REST Haystack API
        - GraphQL API
- We introduced and implemented the *Provider* concept, which handles various options in terms on haystack data location:
    - Local or remote file system (including AWS S3)
    - Local or remote relational database, with optional AWS Time Stream use for Time Series
    - Other custom data location can be handled by extending `haystackapi.providers.HaystackInterface`

History
-------

This project is a fork of `hszinc`_ (Thanks to the team). The proposed evolutions were too big to be accepted in a pull request.

To see the similarities and differences between the two project, click [here](README_hszinc.md)


.. toctree::
    :maxdepth: 2
    :caption: Contents:

    README
    README_hszinc
    README_url_provider
    README_sql_provider
    README_sql_ts_provider
    README_aws
    modules
    haystackapi
    haystackapi.providers
    README_Contribute
    CHANGELOG


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


.. _Haystack project: https://project-haystack.org/
.. _Zinc: https://www.project-haystack.org/doc/Zinc
.. _Json: https://www.project-haystack.org/doc/Json
.. _Csv: https://www.project-haystack.org/doc/Csv
.. _Haystack Rest API: https://www.project-haystack.org/doc/Rest
.. _hszinc: https://github.com/widesky/hszinc
