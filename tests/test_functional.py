import json
import logging
import sys

import boto3
import botocore

import pytest

log = logging.getLogger("carnonapi")
log.setLevel("DEBUG")


@pytest.mark.functional
def test_deployment():
    # Set "running_locally" flag if you are running the integration test locally
    running_locally = True  # TODO: Add parameter to run locally or remotely

    if running_locally:

        # Create Lambda SDK client to connect to appropriate Lambda endpoint
        lambda_client = boto3.client('lambda',
                                     region_name="eu-west-1",
                                     endpoint_url="http://127.0.0.1:3001",
                                     use_ssl=False,
                                     verify=False,
                                     config=botocore.client.Config(
                                         signature_version=botocore.UNSIGNED,
                                         read_timeout=5,
                                         retries={'max_attempts': 0},
                                     )
                                     )
    else:
        lambda_client = boto3.client('lambda')

    # WHEN
    # Invoke your Lambda function as you normally usually do. The function will run
    # locally if it is configured to do so
    response = lambda_client.invoke(FunctionName="About")

    # GIVEN
    assert response["StatusCode"] == 200
    payload = json.loads(response['Payload'].read())
    if 'errorType' in payload:
        print(payload["errorMessage"])
    assert 'errorType' not in payload, payload["errorMessage"]
    assert payload["statusCode"] == 200
    assert json.loads(payload["body"])["message"] == "about"
