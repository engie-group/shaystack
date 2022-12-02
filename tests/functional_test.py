import json
import textwrap

import requests


def client_graphql():
    q = textwrap.dedent("""
        {
            haystack
                {
                with_hist: entities(filter: "his" select: "id,dis" limit: 1)
                with_ids: entities(ids:["p_demo_r_23a44701-1af1bca9"] select: "id,dis")
                entities(filter: "id==@p_demo_r_23a44701-1af1bca9" select: "id,dis" )
                histories(ids: ["@p_demo_r_23a44701-1af1bca9"],
                    datesRange: "2020-07-01,2021-12-01",
                    version: "2022-10-13T14:40:04.613738+00:00 UTC") {ts float}
                }
        }
        """)

    resp = requests.post("http://localhost:3000/graphql", params={'query': q})

    json_resp = json.loads(json.dumps(resp.text))
    expected = json.loads(json.dumps({
                "data": {
                    "haystack": {
                        "with_hist": [
                            {
                                "dis": "s:Tariff His",
                                "id": "r:p_demo_r_23a44701-bbc36976 Tariff His"
                            }
                        ],
                        "with_ids": [
                            {
                                "dis": "s:Weather in Richmond",
                                "id": "r:p_demo_r_23a44701-1af1bca9 Richmond weather"
                            }
                        ],
                        "entities": [
                            {
                                "dis": "s:Weather in Richmond",
                                "id": "r:p_demo_r_23a44701-1af1bca9 Richmond weather"
                            }
                        ],
                        "histories": [
                            [
                                {"ts": "2020-07-01T00:00:00+00:00 UTC", "float": 20.0},
                                {"ts": "2020-08-01T00:00:00+00:00 UTC", "float": 18.0},
                                {"ts": "2020-09-01T00:00:00+00:00 UTC", "float": 16.0},
                                {"ts": "2020-10-01T00:00:00+00:00 UTC", "float": 11.0},
                                {"ts": "2020-11-01T00:00:00+00:00 UTC", "float": 10.0},
                                {"ts": "2020-12-01T00:00:00+00:00 UTC", "float": 6.0}
                            ]
                        ]
                    }
                }
            }))
    assert json.loads(json_resp) == expected

if __name__ == '__main__':
    client_graphql()
