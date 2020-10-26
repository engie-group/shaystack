import json

from graphqlclient import GraphQLClient

client = GraphQLClient('http://localhost:3000/graphql')

result = client.execute('''
query
{
    # haystack(select: "id,dis"ids: ["@customer-913"])
    haystack 
    {
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
    }
}
''')

# TODO: Voir batch query support
## https://github.com/graphql-python/flask-graphql
print(json.dumps(json.loads(result), indent=4, sort_keys=True))
