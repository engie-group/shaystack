import json

import requests


def client_graphql():
    q = """
        {
          haystack
          {
            with_hist:entities(filter:"his" select:"id,dis" limit:1)
            with_ids:entities(ids:["@p:demo:r:23a44701-3a62fd7a"] select:"id,dis" )
            entities(filter:"id==@p:demo:r:23a44701-3a62fd7a" select:"id,dis" )
            histories(ids:["@p:demo:r:23a44701-3a62fd7a"],
              datesRange:"2020-02-01,2020-04-01"
              version:"2021-01-01T00:00:00 UTC") { ts  float }
          }
        }
        """

    resp = requests.post("http://localhost:3000/graphql", params={'query': q})

    json_resp = json.loads(resp.text)
    assert json_resp == \
           {'data': {
               'haystack':
                   {'with_hist': [{'dis': 's:Tariff His', 'id': 'r:p:demo:r:23a44701-bbc36976 Tariff His'}],
                    'with_ids': [{'id': 'r:p:demo:r:23a44701-3a62fd7a Carytown RTU-1 Heat-2'}],
                    'entities': [{'id': 'r:p:demo:r:23a44701-3a62fd7a Carytown RTU-1 Heat-2'}],
                    'histories': [
                        [{'ts': '2020-07-01T00:00:00+00:00 UTC', 'float': 91.0},
                         {'ts': '2020-08-01T00:00:00+00:00 UTC', 'float': 89.0},
                         {'ts': '2020-09-01T00:00:00+00:00 UTC', 'float': 87.0},
                         {'ts': '2020-10-01T00:00:00+00:00 UTC', 'float': 82.0},
                         {'ts': '2020-11-01T00:00:00+00:00 UTC', 'float': 85.0},
                         {'ts': '2020-12-01T00:00:00+00:00 UTC', 'float': 89.0}]]}}}


if __name__ == '__main__':
    client_graphql()
