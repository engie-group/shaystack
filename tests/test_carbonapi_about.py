import inspect
import json

import hszinc
import pytest
from botocore.client import BaseClient
from hszinc import Grid

from carbonapi import haystackapi
from lambda_types import LambdaContext, LambdaEvent
from test_tools import boto_client


@pytest.fixture()
def apigw_event() -> LambdaEvent:
    with open('events/About_event.json') as json_file:
        return json.load(json_file)

@pytest.fixture()
def lambda_client() -> BaseClient:
    return boto_client()


def test_about_with_zinc(apigw_event: LambdaEvent) -> None:
    # GIVEN
    context = LambdaContext()
    context.function_name = "About"
    context.aws_request_id = inspect.currentframe().f_code.co_name
    grid:Grid = hszinc.Grid()
    mime_type = "text/zinc"
    apigw_event["headers"]["Content-Type"] = mime_type
    apigw_event["headers"]["Accept"] = mime_type
    # apigw_event["body"] = hszinc.dump(grid, mode=hszinc.MODE_ZINC)

    # WHEN
    response = haystackapi.about(apigw_event, context)

    # THEN
    assert response["statusCode"] == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    about_grid:Grid = hszinc.parse(response["body"], hszinc.MODE_ZINC)[0]
    assert about_grid[0]["haystackVersion"] == '3.0'



# ------------------------------------------

@pytest.mark.functional
def test_about(apigw_event: LambdaEvent, lambda_client: BaseClient) -> None:
    # WHEN
    boto_response = lambda_client.invoke(
        FunctionName="About",
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
    about_grid:Grid = hszinc.parse(response["body"], hszinc.MODE_ZINC)[0]
    assert about_grid[0]["haystackVersion"] == '3.0'