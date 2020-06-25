import inspect
import json

import pytest
from botocore.client import BaseClient

import hszinc
from carbonapi import haystackapi_lambda
from hszinc import Grid
from lambda_types import LambdaProxyEvent, LambdaContext, LambdaEvent
from test_tools import boto_client


@pytest.fixture()
def apigw_event():
    with open('events/Formats_event.json') as json_file:
        return json.load(json_file)


@pytest.fixture()
def lambda_client() -> BaseClient:
    return boto3.client('lambda',
                        endpoint_url="http://127.0.0.1:3001",
                        use_ssl=False,
                        verify=False,
                        config=Config(signature_version=UNSIGNED,
                                      read_timeout=10,
                                      retries={'max_attempts': 0}))


def test_formats_with_zinc(apigw_event: LambdaProxyEvent):
    # GIVEN
    context = LambdaContext()
    context.function_name = "Formats"
    context.aws_request_id = inspect.currentframe().f_code.co_name
    grid: Grid = hszinc.Grid()
    mime_type = "text/zinc"
    apigw_event["headers"]["Content-Type"] = mime_type
    apigw_event["headers"]["Accept"] = mime_type
    # apigw_event["body"] = hszinc.dump(grid, mode=hszinc.MODE_ZINC)

    # WHEN
    response = haystackapi_lambda.formats(apigw_event, context)

    # THEN
    assert response["statusCode"] == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    format_grid: Grid = hszinc.parse(response["body"], hszinc.MODE_ZINC)[0]
    assert format_grid[0]["mime"] == "text/zinc"
    assert format_grid[0]["receive"] == hszinc.MARKER
    assert format_grid[0]["send"] == hszinc.MARKER
    assert format_grid[1]["mime"] == "application/json"
    assert format_grid[1]["receive"] == hszinc.MARKER
    assert format_grid[1]["send"] == hszinc.MARKER


# ------------------------------------------

@pytest.mark.functional
def test_formats(apigw_event: LambdaEvent, lambda_client: BaseClient) -> None:
    # WHEN
    boto_response = lambda_client.invoke(
        FunctionName="Formats",
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
    format_grid: Grid = hszinc.parse(response["body"], hszinc.MODE_ZINC)[0]
    assert format_grid[0]["mime"] == "text/zinc"
    assert format_grid[0]["receive"] == hszinc.MARKER
    assert format_grid[0]["send"] == hszinc.MARKER
    assert format_grid[1]["mime"] == "application/json"
    assert format_grid[1]["receive"] == hszinc.MARKER
    assert format_grid[1]["send"] == hszinc.MARKER
