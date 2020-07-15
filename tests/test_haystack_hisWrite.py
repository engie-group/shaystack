import base64
import gzip
import inspect
import json
from unittest.mock import patch

import pytest
from botocore.client import BaseClient

import hszinc
from haystackapi_lambda import NO_COMPRESS
from hszinc import Grid
from lambda_types import LambdaProxyEvent, LambdaContext, LambdaEvent
from src import haystackapi_lambda
from test_tools import boto_client


@pytest.fixture()
def apigw_event():
    with open('events/HisWrite_event.json') as json_file:
        return json.load(json_file)


@pytest.fixture()
def lambda_client() -> BaseClient:
    return boto_client()


@patch.dict('os.environ', {'PROVIDER': 'providers.ping.PingProvider'})
def test_hisWrite_with_zinc(apigw_event: LambdaProxyEvent):
    # GIVEN
    context = LambdaContext()
    context.function_name = "HisWrite"
    context.aws_request_id = inspect.currentframe().f_code.co_name
    grid = hszinc.Grid(columns={'id': {}})
    grid.append({"id": 1234})
    mime_type = "text/zinc"
    apigw_event["headers"]["Content-Type"] = mime_type
    apigw_event["headers"]["Accept"] = mime_type
    apigw_event["body"] = hszinc.dump(grid, mode=hszinc.MODE_ZINC)

    # WHEN
    response = haystackapi_lambda.hisWrite(apigw_event, context)

    # THEN
    assert response["statusCode"] == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    read_grid: Grid = hszinc.parse(response["body"], hszinc.MODE_ZINC)[0]
    assert not len(read_grid)


# ------------------------------------------
@pytest.mark.functional
def test_hisWrite(apigw_event: LambdaEvent, lambda_client: BaseClient) -> None:
    # GIVEN
    apigw_event["headers"]["Accept-Encoding"] = "gzip, deflate, sdch"
    grid = hszinc.Grid(columns={'id': {}})
    grid.append({"id": 1234})
    mime_type = "text/zinc"
    apigw_event["headers"]["Content-Type"] = mime_type
    apigw_event["headers"]["Accept"] = mime_type
    apigw_event["body"] = hszinc.dump(grid, mode=hszinc.MODE_ZINC)

    # WHEN
    boto_response = lambda_client.invoke(
        FunctionName="HisWrite",
        InvocationType="RequestResponse",
        ClientContext="",
        Payload=json.dumps(apigw_event)
    )

    # GIVEN
    assert boto_response["StatusCode"] == 200
    response = json.loads(boto_response['Payload'].read())
    if 'errorType' in response:
        print(response["errorMessage"])
    assert 'errorType' not in response, response["errorMessage"]
    assert response["statusCode"] == 200
    assert response["headers"]["Content-Type"].startswith("text/zinc")
    if not NO_COMPRESS:
        assert response["isBase64Encoded"]
        body = gzip.decompress(base64.b64decode(response["body"])).decode("utf-8")
    else:
        body = response["body"]

    assert hszinc.parse(body, hszinc.MODE_ZINC)
