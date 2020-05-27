import inspect

import hszinc
import pytest

from carbonapi import haystackapi
from lambda_types import LambdaProxyEvent, LambdaContext


@pytest.fixture()
def apigw_event():
    """ Generates API GW Event"""

    return {
        "body": '{ "test": "body"}',
        "resource": "/{proxy+}",
        "requestContext": {
            "resourceId": "123456",
            "apiId": "1234567890",
            "resourcePath": "/{proxy+}",
            "httpMethod": "POST",
            "requestId": "c6af9ac6-7b61-11e6-9a41-93e8deadbeef",
            "accountId": "123456789012",
            "identity": {
                "apiKey": "",
                "userArn": "",
                "cognitoAuthenticationType": "",
                "caller": "",
                "userAgent": "Custom User Agent String",
                "user": "",
                "cognitoIdentityPoolId": "",
                "cognitoIdentityId": "",
                "cognitoAuthenticationProvider": "",
                "sourceIp": "127.0.0.1",
                "accountId": "",
            },
            "stage": "prod",
        },
        "queryStringParameters": {"foo": "bar"},
        "headers": {
            "Via": "1.1 08f323deadbeefa7af34d5feb414ce27.cloudfront.net (CloudFront)",
            "Accept-Language": "en-US,en;q=0.8",
            "CloudFront-Is-Desktop-Viewer": "true",
            "CloudFront-Is-SmartTV-Viewer": "false",
            "CloudFront-Is-Mobile-Viewer": "false",
            "X-Forwarded-For": "127.0.0.1, 127.0.0.2",
            "CloudFront-Viewer-Country": "US",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Upgrade-Insecure-Requests": "1",
            "X-Forwarded-Port": "443",
            "Host": "1234567890.execute-api.us-east-1.amazonaws.com",
            "X-Forwarded-Proto": "https",
            "X-Amz-Cf-Id": "aaaaaaaaaae3VYQb9jd-nvCd-de396Uhbp027Y2JvkCPNLmGJHqlaA==",
            "CloudFront-Is-Tablet-Viewer": "false",
            "Cache-Control": "max-age=0",
            "User-Agent": "Custom User Agent String",
            "CloudFront-Forwarded-Proto": "https",
            "Accept-Encoding": "gzip, deflate, sdch",
        },
        "pathParameters": {"proxy": "/examplepath"},
        "httpMethod": "POST",
        "stageVariables": {"baz": "qux"},
        "path": "/extend_with_co2e",
    }


def test_extend_with_co2e_with_zinc(apigw_event: LambdaProxyEvent):
    # GIVEN
    context = LambdaContext()
    context.function_name = "ExtendWithCO2e"
    context.aws_request_id = inspect.currentframe().f_code.co_name
    grid = hszinc.Grid(columns={'id': {}, "val": {}})
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
    grid = hszinc.Grid(columns={'id': {}, "val": {}})
    grid.append({"id": "@me", "val": "sample"})
    mime_type = "text/json"
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
    grid = hszinc.Grid(columns={'id': {}})
    mime_type = "text/zinc"
    apigw_event["headers"]["Accept"] = mime_type
    apigw_event["body"] = hszinc.dump(grid, mode=hszinc.MODE_ZINC)

    # WHEN
    response = haystackapi.extend_with_co2e(apigw_event, context)

    # THEN
    assert response["statusCode"] == 400
    assert response.headers["Content-Type"].startswith(mime_type)
    error_grid = hszinc.parse(response["body"], hszinc.MODE_ZINC)
    assert "err" in error_grid[0].metadata


def test_extend_with_co2e_json_without_content_type(apigw_event: LambdaProxyEvent):
    # GIVEN
    context = LambdaContext()
    context.function_name = "ExtendWithCO2e"
    context.aws_request_id = inspect.currentframe().f_code.co_name
    grid = hszinc.Grid(columns={'id': {}})
    mime_type = "text/json"
    apigw_event["headers"]["Accept"] = mime_type
    apigw_event["body"] = hszinc.dump(grid, mode=hszinc.MODE_JSON)

    # WHEN
    response = haystackapi.extend_with_co2e(apigw_event, context)

    # THEN
    assert response["statusCode"] == 400
    assert response.headers["Content-Type"].startswith(mime_type)
    error_grid = hszinc.parse(response["body"], hszinc.MODE_JSON)
    assert "err" in error_grid.metadata


def test_extend_with_co2e_without_accept(apigw_event: LambdaProxyEvent):
    # GIVEN
    context = LambdaContext()
    context.function_name = "ExtendWithCO2e"
    context.aws_request_id = inspect.currentframe().f_code.co_name
    grid = hszinc.Grid(columns={'id': {}})
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
    grid = hszinc.Grid(columns={'id': {}})
    mime_type = "text/zinc"
    apigw_event["headers"]["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    apigw_event["headers"]["Content-Type"] = mime_type
    apigw_event["body"] = hszinc.dump(grid, mode=hszinc.MODE_ZINC)

    # WHEN
    response = haystackapi.extend_with_co2e(apigw_event, context)

    # THEN
    assert response["statusCode"] == 400
    assert response.headers["Content-Type"].startswith(mime_type)
    error_grid = hszinc.parse(response["body"], hszinc.MODE_ZINC)
    assert "err" in error_grid[0].metadata


def test_extend_with_co2e_with_complex_accept(apigw_event: LambdaProxyEvent):
    # GIVEN
    context = LambdaContext()
    context.function_name = "ExtendWithCO2e"
    context.aws_request_id = inspect.currentframe().f_code.co_name
    grid = hszinc.Grid(columns={'id': {}})
    mime_type = "text/zinc"
    apigw_event["headers"]["Accept"] = "text/json;q=0.9,text/zinc;q=1"
    apigw_event["headers"]["Content-Type"] = mime_type
    apigw_event["body"] = hszinc.dump(grid, mode=hszinc.MODE_ZINC)

    # WHEN
    response = haystackapi.extend_with_co2e(apigw_event, context)

    # THEN
    assert response["statusCode"] == 200
    assert response.headers["Content-Type"].startswith(mime_type)
