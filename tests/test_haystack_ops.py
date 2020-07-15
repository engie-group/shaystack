import inspect
import json
from unittest.mock import patch

import pytest
from botocore.client import BaseClient

import hszinc
from hszinc import Grid
from lambda_types import LambdaProxyEvent, LambdaContext, LambdaEvent
from src import haystackapi_lambda
from test_tools import boto_client


@pytest.fixture()
def apigw_event():
    with open('events/Ops_event.json') as json_file:
        return json.load(json_file)


@pytest.fixture()
def lambda_client() -> BaseClient:
    return boto_client()


@patch.dict('os.environ', {'PROVIDER': 'providers.ping.PingProvider'})
def test_ops_with_zinc(apigw_event: LambdaProxyEvent):
    # GIVEN
    context = LambdaContext()
    context.function_name = "Ops"
    context.aws_request_id = inspect.currentframe().f_code.co_name
    grid: Grid = hszinc.Grid()
    mime_type = "text/zinc"
    apigw_event["headers"]["Content-Type"] = mime_type
    apigw_event["headers"]["Accept"] = mime_type
    # apigw_event["body"] = hszinc.dump(grid, mode=hszinc.MODE_ZINC)

    # WHEN
    response = haystackapi_lambda.ops(apigw_event, context)

    # THEN
    assert response["statusCode"] == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    ops_grid: Grid = hszinc.parse(response["body"], hszinc.MODE_ZINC)[0]
    assert ops_grid[0]["name"] == "about"
    assert ops_grid[1]["name"] == "ops"


# ------------------------------------------

@pytest.mark.functional
def test_ops(apigw_event: LambdaEvent, lambda_client: BaseClient) -> None:
    # WHEN
    boto_response = lambda_client.invoke(
        FunctionName="Ops",
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
    ops_grid: Grid = hszinc.parse(response["body"], hszinc.MODE_ZINC)[0]
    assert ops_grid[0]["name"] == "about"
    assert ops_grid[1]["name"] == "ops"
