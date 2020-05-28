import base64
import gzip
import inspect
import json

import hszinc
import pytest
from botocore.client import BaseClient
from hszinc import Grid

from carbonapi import haystackapi
from haystackapi import NO_COMPRESS
from lambda_types import LambdaProxyEvent, LambdaContext, LambdaEvent
from tests.test_tools import boto_client


@pytest.fixture()
def apigw_event():
    with open('events/ExtendWithCO2e_event.json') as json_file:
        return json.load(json_file)

@pytest.fixture()
def lambda_client() -> BaseClient:
    return boto_client()

def test_extend_with_co2e_with_zinc(apigw_event: LambdaProxyEvent):
    # GIVEN
    context = LambdaContext()
    context.function_name = "ExtendWithCO2e"
    context.aws_request_id = inspect.currentframe().f_code.co_name
    grid:Grid = hszinc.Grid(columns={'id': {}, "val": {}})
    grid.append({"id": "@me", "val": "sample"})
    mime_type = "text/zinc"
    apigw_event["headers"]["Content-Type"] = mime_type
    apigw_event["headers"]["Accept"] = mime_type
    apigw_event["body"] = hszinc.dump(grid, mode=hszinc.MODE_ZINC)

    # WHEN
    response = haystackapi.extend_with_co2e(apigw_event, context)

    # THEN
    assert response["statusCode"] == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    hszinc.parse(response["body"], hszinc.MODE_ZINC)
    assert response["body"] == apigw_event["body"]


def test_extend_with_co2e_with_json(apigw_event: LambdaProxyEvent):
    # GIVEN
    context = LambdaContext()
    context.function_name = "ExtendWithCO2e"
    context.aws_request_id = inspect.currentframe().f_code.co_name
    grid:Grid = hszinc.Grid(columns={'id': {}, "val": {}})
    grid.append({"id": "@me", "val": "sample"})
    mime_type = "application/json"
    apigw_event["headers"]["Content-Type"] = mime_type
    apigw_event["headers"]["Accept"] = mime_type
    apigw_event["body"] = hszinc.dump(grid, mode=hszinc.MODE_JSON)

    # WHEN
    response = haystackapi.extend_with_co2e(apigw_event, context)

    # THEN
    assert response["statusCode"] == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    hszinc.parse(response["body"], hszinc.MODE_JSON)
    assert response["body"] == apigw_event["body"]


def test_extend_with_co2e_zinc_without_content_type(apigw_event: LambdaProxyEvent):
    # GIVEN
    context = LambdaContext()
    context.function_name = "ExtendWithCO2e"
    context.aws_request_id = inspect.currentframe().f_code.co_name
    grid:Grid = hszinc.Grid(columns={'id': {}})
    mime_type = "text/zinc"
    del apigw_event["headers"]["Content-Type"]
    apigw_event["headers"]["Accept"] = mime_type
    apigw_event["body"] = hszinc.dump(grid, mode=hszinc.MODE_ZINC)

    # WHEN
    response = haystackapi.extend_with_co2e(apigw_event, context)

    # THEN
    assert response["statusCode"] == 400
    assert response.headers["Content-Type"].startswith(mime_type)
    error_grid:Grid = hszinc.parse(response["body"], hszinc.MODE_ZINC)
    assert "err" in error_grid[0].metadata


def test_extend_with_co2e_json_without_content_type(apigw_event: LambdaProxyEvent):
    # GIVEN
    context = LambdaContext()
    context.function_name = "ExtendWithCO2e"
    context.aws_request_id = inspect.currentframe().f_code.co_name
    grid:Grid = hszinc.Grid(columns={'id': {}})
    mime_type = "application/json"
    apigw_event["headers"]["Accept"] = mime_type
    apigw_event["body"] = hszinc.dump(grid, mode=hszinc.MODE_JSON)

    # WHEN
    response = haystackapi.extend_with_co2e(apigw_event, context)

    # THEN
    assert response["statusCode"] == 400
    assert response.headers["Content-Type"].startswith(mime_type)
    error_grid:Grid = hszinc.parse(response["body"], hszinc.MODE_JSON)
    assert "err" in error_grid.metadata


def test_extend_with_co2e_json_with_unknown_content_type(apigw_event: LambdaProxyEvent):
    # GIVEN
    context = LambdaContext()
    context.function_name = "ExtendWithCO2e"
    context.aws_request_id = inspect.currentframe().f_code.co_name
    grid:Grid = hszinc.Grid(columns={'id': {}})
    mime_type = "text/zinc"
    apigw_event["headers"]["Accept"] = mime_type
    apigw_event["headers"]["Content-Type"] = "text/html"
    apigw_event["body"] = hszinc.dump(grid, mode=hszinc.MODE_JSON)

    # WHEN
    response = haystackapi.extend_with_co2e(apigw_event, context)

    # THEN
    assert response["statusCode"] == 400
    assert response.headers["Content-Type"].startswith(mime_type)
    error_grid:Grid = hszinc.parse(response["body"], hszinc.MODE_ZINC)[0]
    assert "err" in error_grid.metadata


def test_extend_with_co2e_without_accept(apigw_event: LambdaProxyEvent):
    # GIVEN
    context = LambdaContext()
    context.function_name = "ExtendWithCO2e"
    context.aws_request_id = inspect.currentframe().f_code.co_name
    grid:Grid = hszinc.Grid(columns={'id': {}})
    mime_type = "text/zinc"
    del apigw_event["headers"]["Accept"]
    apigw_event["headers"]["Content-Type"] = mime_type
    apigw_event["body"] = hszinc.dump(grid, mode=hszinc.MODE_ZINC)

    # WHEN
    response = haystackapi.extend_with_co2e(apigw_event, context)

    # THEN
    assert response["statusCode"] == 200
    assert response.headers["Content-Type"].startswith("text/zinc")  # Default value
    assert response["body"] == apigw_event["body"]


def test_extend_with_co2e_with_invalide_accept(apigw_event: LambdaProxyEvent):
    # GIVEN
    context = LambdaContext()
    context.function_name = "ExtendWithCO2e"
    context.aws_request_id = inspect.currentframe().f_code.co_name
    grid:Grid = hszinc.Grid(columns={'id': {}})
    mime_type = "text/zinc"
    apigw_event["headers"]["Accept"] = "Accept:text/html"
    apigw_event["headers"]["Content-Type"] = mime_type
    apigw_event["body"] = hszinc.dump(grid, mode=hszinc.MODE_ZINC)

    # WHEN
    response = haystackapi.extend_with_co2e(apigw_event, context)

    # THEN
    assert response["statusCode"] == 400
    assert response.headers["Content-Type"].startswith(mime_type)
    error_grid:Grid = hszinc.parse(response["body"], hszinc.MODE_ZINC)
    assert "err" in error_grid[0].metadata

def test_extend_with_co2e_with_navigator_accept(apigw_event: LambdaProxyEvent):
    # GIVEN
    context = LambdaContext()
    context.function_name = "ExtendWithCO2e"
    context.aws_request_id = inspect.currentframe().f_code.co_name
    grid:Grid = hszinc.Grid(columns={'id': {}})
    mime_type = "text/zinc"
    apigw_event["headers"]["Accept"] = "Accept:text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
    apigw_event["headers"]["Content-Type"] = mime_type
    apigw_event["body"] = hszinc.dump(grid, mode=hszinc.MODE_ZINC)

    # WHEN
    response = haystackapi.extend_with_co2e(apigw_event, context)

    # THEN
    assert response["statusCode"] == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    hszinc.parse(response["body"], hszinc.MODE_ZINC)


def test_extend_with_co2e_with_complex_accept(apigw_event: LambdaProxyEvent):
    # GIVEN
    context = LambdaContext()
    context.function_name = "ExtendWithCO2e"
    context.aws_request_id = inspect.currentframe().f_code.co_name
    grid:Grid = hszinc.Grid(columns={'id': {}})
    mime_type = "text/zinc"
    apigw_event["headers"]["Accept"] = "text/json;q=0.9,text/zinc;q=1"
    apigw_event["headers"]["Content-Type"] = mime_type
    apigw_event["body"] = hszinc.dump(grid, mode=hszinc.MODE_ZINC)

    # WHEN
    response = haystackapi.extend_with_co2e(apigw_event, context)

    # THEN
    assert response["statusCode"] == 200
    assert response.headers["Content-Type"].startswith(mime_type)

def test_extend_with_co2e_with_zinc_to_json(apigw_event: LambdaProxyEvent):
    # GIVEN
    context = LambdaContext()
    context.function_name = "ExtendWithCO2e"
    context.aws_request_id = inspect.currentframe().f_code.co_name
    grid:Grid = hszinc.Grid(columns={'id': {}})
    apigw_event["headers"]["Accept"] = "application/json"
    apigw_event["headers"]["Content-Type"] = "text/zinc"
    apigw_event["body"] = hszinc.dump(grid, mode=hszinc.MODE_ZINC)

    # WHEN
    response = haystackapi.extend_with_co2e(apigw_event, context)

    # THEN
    assert response["statusCode"] == 200
    assert response.headers["Content-Type"].startswith("application/json")
    hszinc.parse(response["body"], hszinc.MODE_JSON)


def test_extend_with_gzip_encoding_for_result(apigw_event: LambdaProxyEvent):
    # GIVEN
    context = LambdaContext()
    context.function_name = "ExtendWithCO2e"
    context.aws_request_id = inspect.currentframe().f_code.co_name
    grid:Grid = hszinc.Grid(columns={'id': {}})
    mime_type = "text/zinc"
    apigw_event["headers"]["Accept"] = "text/zinc"
    apigw_event["headers"]["Content-Type"] = mime_type
    apigw_event["headers"]["Accept-Encoding"] = "gzip, deflate, sdch"
    apigw_event["body"] = hszinc.dump(grid, mode=hszinc.MODE_ZINC)

    # WHEN
    response = haystackapi.extend_with_co2e(apigw_event, context)

    # THEN
    assert response["statusCode"] == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    if not NO_COMPRESS:
        assert response.headers["Content-Encoding"] == "gzip"
        assert response.isBase64Encoded
        body = gzip.decompress(base64.b64decode(response["body"])).decode("utf-8")
    else:
        body = response["body"]
    hszinc.parse(body, hszinc.MODE_ZINC)

def test_extend_with_gzip_encoding_for_request(apigw_event: LambdaProxyEvent):
    # GIVEN
    context = LambdaContext()
    context.function_name = "ExtendWithCO2e"
    context.aws_request_id = inspect.currentframe().f_code.co_name
    grid:Grid = hszinc.Grid(columns={'id': {}})
    mime_type = "text/zinc"
    apigw_event["headers"]["Accept"] = "text/zinc"
    apigw_event["headers"]["Content-Type"] = mime_type
    apigw_event["headers"]["Content-Encoding"] = "gzip"
    body = hszinc.dump(grid, mode=hszinc.MODE_ZINC)
    apigw_event["body"] = base64.b64encode(gzip.compress(body.encode("utf-8")))
    apigw_event["isBase64Encoded"] = True

    # WHEN
    response = haystackapi.extend_with_co2e(apigw_event, context)

    # THEN
    assert response["statusCode"] == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    hszinc.parse(response["body"], hszinc.MODE_ZINC)

def test_extend_with_xxx_encoding_for_request(apigw_event: LambdaProxyEvent):
    # GIVEN
    context = LambdaContext()
    context.function_name = "ExtendWithCO2e"
    context.aws_request_id = inspect.currentframe().f_code.co_name
    grid:Grid = hszinc.Grid(columns={'id': {}})
    mime_type = "text/zinc"
    apigw_event["headers"]["Accept"] = "text/zinc"
    apigw_event["headers"]["Content-Type"] = mime_type
    apigw_event["headers"]["Content-Encoding"] = "xxx"
    body = hszinc.dump(grid, mode=hszinc.MODE_ZINC)
    apigw_event["body"] = base64.b64encode(gzip.compress(body.encode("utf-8")))
    apigw_event["isBase64Encoded"] = True

    # WHEN
    response = haystackapi.extend_with_co2e(apigw_event, context)

    # THEN
    assert response["statusCode"] == 400
    assert response.headers["Content-Type"].startswith(mime_type)
    error_grid:Grid = hszinc.parse(response["body"], hszinc.MODE_ZINC)
    assert "err" in error_grid[0].metadata

# ------------------------------------------

@pytest.mark.functional
def test_extend_with_co2e(apigw_event: LambdaEvent, lambda_client: BaseClient) -> None:
    # GIVEN
    apigw_event["headers"]["Accept-Encoding"] = "gzip, deflate, sdch"
    # WHEN
    boto_response = lambda_client.invoke(
        FunctionName="ExtendWithCO2e",
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

    hszinc.parse(body, hszinc.MODE_ZINC)
    assert body == apigw_event["body"]
