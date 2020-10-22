import json

from graphqlclient import GraphQLClient

client = GraphQLClient('http://localhost:3000/graphql/')

result = client.execute('''
query
{
    # haystack(select: "id,dis"ids: ["@customer-913"])
    haystack 
    {
        about 
        {
            name
            value
        }
#         ops 
#         {
#             name
#             value
#         }
#         read(select: "id,dis" filter: "id", limit: 2)
# #        read
#         { 
#             name
#             value
#         }
#         hisRead(id:"@elec-16514")
#         {
#             name
#             value
#         }
#         pointWrite(id:"@elec-16514")
#         {
#             name
#             value
#         }
    }
}
''')

# TODO: Voir batch query support
## https://github.com/graphql-python/flask-graphql
print(json.dumps(json.loads(result), indent=4, sort_keys=True))
