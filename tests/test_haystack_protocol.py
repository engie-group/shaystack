import inspect
import json
from unittest.mock import patch

import pytest
from botocore.client import BaseClient

import hszinc
from hszinc import Grid
from lambda_types import LambdaProxyEvent, LambdaContext
from src import haystackapi_lambda
from test_tools import boto_client


@pytest.fixture()
def apigw_event():
    with open('events/Read_event.json') as json_file:
        return json.load(json_file)


@pytest.fixture()
def lambda_client() -> BaseClient:
    return boto_client()


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'providers.ping.Provider'})
def test_negociation_with_zinc(apigw_event: LambdaProxyEvent):
    # GIVEN
    context = LambdaContext()
    context.function_name = "Read"
    context.aws_request_id = inspect.currentframe().f_code.co_name
    grid = hszinc.Grid(columns={'filter': {}, "limit": {}})
    grid.append({"filter": "id==@me", "limit": 1})
    mime_type = "text/zinc"
    apigw_event["headers"]["Content-Type"] = mime_type
    apigw_event["headers"]["Accept"] = mime_type
    apigw_event["body"] = hszinc.dump(grid, mode=hszinc.MODE_ZINC)

    # WHEN
    response = haystackapi_lambda.read(apigw_event, context)

    # THEN
    assert response["statusCode"] == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    hszinc.parse(response["body"], hszinc.MODE_ZINC)[0]


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'providers.ping.Provider'})
def test_negociation_with_json(apigw_event: LambdaProxyEvent):
    # GIVEN
    context = LambdaContext()
    context.function_name = "Read"
    context.aws_request_id = inspect.currentframe().f_code.co_name
    grid = hszinc.Grid(columns={'filter': {}, 'limit': {}})
    grid.append({'filter': '', 'limit': -1})
    mime_type = "application/json"
    apigw_event["headers"]["Content-Type"] = mime_type
    apigw_event["headers"]["Accept"] = mime_type
    apigw_event["body"] = hszinc.dump(grid, mode=hszinc.MODE_JSON)

    # WHEN
    response = haystackapi_lambda.read(apigw_event, context)

    # THEN
    assert response["statusCode"] == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    hszinc.parse(response["body"], hszinc.MODE_JSON)


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'providers.ping.Provider'})
def test_negociation_zinc_without_content_type(apigw_event: LambdaProxyEvent):
    # GIVEN
    context = LambdaContext()
    context.function_name = "Read"
    context.aws_request_id = inspect.currentframe().f_code.co_name
    grid: Grid = hszinc.Grid(columns={'id': {}})
    mime_type = "text/zinc"
    del apigw_event["headers"]["Content-Type"]
    apigw_event["headers"]["Accept"] = mime_type
    apigw_event["body"] = hszinc.dump(grid, mode=hszinc.MODE_ZINC)

    # WHEN
    response = haystackapi_lambda.read(apigw_event, context)

    # THEN
    assert response["statusCode"] == 400
    assert response.headers["Content-Type"].startswith(mime_type)
    error_grid: Grid = hszinc.parse(response["body"], hszinc.MODE_ZINC)
    assert "err" in error_grid[0].metadata


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'providers.ping.Provider'})
def test_negociation_json_without_content_type(apigw_event: LambdaProxyEvent):
    # GIVEN
    context = LambdaContext()
    context.function_name = "Read"
    context.aws_request_id = inspect.currentframe().f_code.co_name
    grid: Grid = hszinc.Grid(columns={'id': {}})
    mime_type = "application/json"
    apigw_event["headers"]["Accept"] = mime_type
    apigw_event["body"] = hszinc.dump(grid, mode=hszinc.MODE_JSON)

    # WHEN
    response = haystackapi_lambda.read(apigw_event, context)

    # THEN
    assert response["statusCode"] == 400
    assert response.headers["Content-Type"].startswith(mime_type)
    error_grid: Grid = hszinc.parse(response["body"], hszinc.MODE_JSON)[0]
    assert "err" in error_grid.metadata


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'providers.ping.Provider'})
def test_negociation_json_with_unknown_content_type(apigw_event: LambdaProxyEvent):
    # GIVEN
    context = LambdaContext()
    context.function_name = "Read"
    context.aws_request_id = inspect.currentframe().f_code.co_name
    grid: Grid = hszinc.Grid(columns={'id': {}})
    mime_type = "text/zinc"
    apigw_event["headers"]["Accept"] = mime_type
    apigw_event["headers"]["Content-Type"] = "text/html"
    apigw_event["body"] = hszinc.dump(grid, mode=hszinc.MODE_JSON)

    # WHEN
    response = haystackapi_lambda.read(apigw_event, context)

    # THEN
    assert response["statusCode"] == 400
    assert response.headers["Content-Type"].startswith(mime_type)
    error_grid: Grid = hszinc.parse(response["body"], hszinc.MODE_ZINC)[0]
    assert "err" in error_grid.metadata


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'providers.ping.Provider'})
def test_negociation_without_accept(apigw_event: LambdaProxyEvent):
    # GIVEN
    context = LambdaContext()
    context.function_name = "Read"
    context.aws_request_id = inspect.currentframe().f_code.co_name
    grid = hszinc.Grid(columns={'filter': {}, 'limit': {}})
    grid.append({'filter': '', 'limit': -1})
    mime_type = "text/zinc"
    del apigw_event["headers"]["Accept"]
    apigw_event["headers"]["Content-Type"] = mime_type
    apigw_event["body"] = hszinc.dump(grid, mode=hszinc.MODE_ZINC)

    # WHEN
    response = haystackapi_lambda.read(apigw_event, context)

    # THEN
    assert response["statusCode"] == 200
    assert response.headers["Content-Type"].startswith("text/zinc")  # Default value


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'providers.ping.Provider'})
def test_negociation_with_invalide_accept(apigw_event: LambdaProxyEvent):
    # GIVEN
    context = LambdaContext()
    context.function_name = "Read"
    context.aws_request_id = inspect.currentframe().f_code.co_name
    grid: Grid = hszinc.Grid(columns={'id': {}})
    mime_type = "text/zinc"
    apigw_event["headers"]["Accept"] = "text/html"
    apigw_event["headers"]["Content-Type"] = mime_type
    apigw_event["body"] = hszinc.dump(grid, mode=hszinc.MODE_ZINC)

    # WHEN
    response = haystackapi_lambda.read(apigw_event, context)

    # THEN
    assert response["statusCode"] == 400
    assert response.headers["Content-Type"].startswith(mime_type)
    error_grid = hszinc.parse(response["body"], hszinc.MODE_ZINC)
    assert "err" in error_grid[0].metadata


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'providers.ping.Provider'})
def test_negociation_with_navigator_accept(apigw_event: LambdaProxyEvent):
    # GIVEN
    context = LambdaContext()
    context.function_name = "Read"
    context.aws_request_id = inspect.currentframe().f_code.co_name
    grid = hszinc.Grid(columns={'filter': {}, 'limit': {}})
    grid.append({'filter': '', 'limit': -1})
    mime_type = "text/zinc"
    apigw_event["headers"][
        "Accept"] = "Accept:text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
    apigw_event["headers"]["Content-Type"] = mime_type
    apigw_event["body"] = hszinc.dump(grid, mode=hszinc.MODE_ZINC)

    # WHEN
    response = haystackapi_lambda.read(apigw_event, context)

    # THEN
    assert response["statusCode"] == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    hszinc.parse(response["body"], hszinc.MODE_ZINC)


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'providers.ping.Provider'})
def test_negociation_with_complex_accept(apigw_event: LambdaProxyEvent):
    # GIVEN
    context = LambdaContext()
    context.function_name = "Read"
    context.aws_request_id = inspect.currentframe().f_code.co_name
    grid = hszinc.Grid(columns={'filter': {}, 'limit': {}})
    grid.append({'filter': '', 'limit': -1})
    mime_type = "text/zinc"
    apigw_event["headers"]["Accept"] = "text/json;q=0.9,text/zinc;q=1"
    apigw_event["headers"]["Content-Type"] = mime_type
    apigw_event["body"] = hszinc.dump(grid, mode=hszinc.MODE_ZINC)

    # WHEN
    response = haystackapi_lambda.read(apigw_event, context)

    # THEN
    assert response["statusCode"] == 200
    assert response.headers["Content-Type"].startswith(mime_type)


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'providers.ping.Provider'})
def test_negociation_with_zinc_to_json(apigw_event: LambdaProxyEvent):
    # GIVEN
    context = LambdaContext()
    context.function_name = "Read"
    context.aws_request_id = inspect.currentframe().f_code.co_name
    grid = hszinc.Grid(columns={'filter': {}, 'limit': {}})
    grid.append({'filter': '', 'limit': -1})
    apigw_event["headers"]["Accept"] = "application/json"
    apigw_event["headers"]["Content-Type"] = "text/zinc"
    apigw_event["body"] = hszinc.dump(grid, mode=hszinc.MODE_ZINC)

    # WHEN
    response = haystackapi_lambda.read(apigw_event, context)

    # THEN
    assert response["statusCode"] == 200
    assert response.headers["Content-Type"].startswith("application/json")
    hszinc.parse(response["body"], hszinc.MODE_JSON)

# TODO: Test encoding
# @patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'providers.ping.Provider'})
# def test_negociation_extend_with_gzip_encoding_for_result(apigw_event: LambdaProxyEvent):
#     # GIVEN
#     context = LambdaContext()
#     context.function_name = "Read"
#     context.aws_request_id = inspect.currentframe().f_code.co_name
#     grid = hszinc.Grid(columns={'filter': {}, 'limit': {}})
#     grid.append({'filter': '', 'limit': -1})
#     mime_type = "text/zinc"
#     apigw_event["headers"]["Accept"] = "text/zinc"
#     apigw_event["headers"]["Content-Type"] = mime_type
#     apigw_event["headers"]["Accept-Encoding"] = "gzip, deflate, sdch"
#     apigw_event["body"] = hszinc.dump(grid, mode=hszinc.MODE_ZINC)
#
#     # WHEN
#     response = haystackapi_lambda.read(apigw_event, context)
#
#     # THEN
#     assert response["statusCode"] == 200
#     assert response.headers["Content-Type"].startswith(mime_type)
#     if not NO_COMPRESS:
#         assert response.headers["Content-Encoding"] == "gzip"
#         assert response.isBase64Encoded
#         body = gzip.decompress(base64.b64decode(response["body"])).decode("utf-8")
#     else:
#         body = response["body"]
#     hszinc.parse(body, hszinc.MODE_ZINC)


# @patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'providers.ping.Provider'})
# def test_negociation_extend_with_gzip_encoding_for_request(apigw_event: LambdaProxyEvent):
#     # GIVEN
#     context = LambdaContext()
#     context.function_name = "Read"
#     context.aws_request_id = inspect.currentframe().f_code.co_name
#     grid = hszinc.Grid(columns={'filter': {}, 'limit': {}})
#     grid.append({'filter': '', 'limit': -1})
#     mime_type = "text/zinc"
#     apigw_event["headers"]["Accept"] = "text/zinc"
#     apigw_event["headers"]["Content-Type"] = mime_type
#     apigw_event["headers"]["Content-Encoding"] = "gzip"
#     body = hszinc.dump(grid, mode=hszinc.MODE_ZINC)
#     apigw_event["body"] = base64.b64encode(gzip.compress(body.encode("utf-8")))
#     apigw_event["isBase64Encoded"] = True
#
#     # WHEN
#     response = haystackapi_lambda.read(apigw_event, context)
#
#     # THEN
#     assert response["statusCode"] == 200
#     assert response.headers["Content-Type"].startswith(mime_type)
#     hszinc.parse(response["body"], hszinc.MODE_ZINC)


# @patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'providers.ping.Provider'})
# def test_negociation_extend_with_xxx_encoding_for_request(apigw_event: LambdaProxyEvent):
#     # GIVEN
#     context = LambdaContext()
#     context.function_name = "Read"
#     context.aws_request_id = inspect.currentframe().f_code.co_name
#     grid = hszinc.Grid(columns={'filter': {}, 'limit': {}})
#     grid.append({'filter': '', 'limit': -1})
#     mime_type = "text/zinc"
#     apigw_event["headers"]["Accept"] = "text/zinc"
#     apigw_event["headers"]["Content-Type"] = mime_type
#     apigw_event["headers"]["Content-Encoding"] = "xxx"
#     body = hszinc.dump(grid, mode=hszinc.MODE_ZINC)
#     apigw_event["body"] = base64.b64encode(gzip.compress(body.encode("utf-8")))
#     apigw_event["isBase64Encoded"] = True
#
#     # WHEN
#     response = haystackapi_lambda.read(apigw_event, context)
#
#     # THEN
#     assert response["statusCode"] == 400
#     assert response.headers["Content-Type"].startswith(mime_type)
#     error_grid = hszinc.parse(response["body"], hszinc.MODE_ZINC)
#     assert "err" in error_grid[0].metadata
