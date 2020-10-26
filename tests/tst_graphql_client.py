import json

from graphqlclient import GraphQLClient

client = GraphQLClient('http://localhost:3000/graphql')
# client = GraphQLClient('https://w1pub81bkc.execute-api.us-east-2.amazonaws.com/dev/graphql')

result = client.execute('''
{ haystack {
    about
    {
        haystackVersion
        tz
        serverName
        serverTime
        serverBootTime
        productName
        productUri
        productVersion
        moduleName
        moduleVersion
    }
    ops
    {
        name
        summary
    }
    read(select: "id,dis" filter: "id", limit: 2)
    hisRead(id:"@elec-16514")
    pointWrite(id:"@elec-16514")
    {
        level
        levelDis
        val
        who
    }
} }
''')

# TODO: Voir batch query support
## https://github.com/graphql-python/flask-graphql
print(json.dumps(json.loads(result), indent=4, sort_keys=True))
