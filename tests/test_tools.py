import boto3
import botocore
from botocore.client import BaseClient


def boto_client() -> BaseClient:
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
    return lambda_client

