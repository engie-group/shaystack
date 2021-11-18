# -*- coding: utf-8 -*-
# SQL Provider
# See the accompanying LICENSE file.
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:
"""
Tools for providers
"""
import base64
import json

from botocore.exceptions import ClientError

_BOTO3_AVAILABLE = False
try:
    # noinspection PyUnresolvedReferences
    import boto3

    _BOTO3_AVAILABLE = True
except ImportError:
    pass


def get_secret_manager_secret(pattern, envs) -> str:
    """
    Return the password present in the AWS Secret manager.
    Args:
        pattern: <container>|<key>
        envs: Environment variables (with `AWS_REGION`)

    Returns:
        The password at `container[key]`

    """
    if not _BOTO3_AVAILABLE:
        return "secretManager"

    secret_id, secret_key = pattern.split('|')
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=envs["AWS_REGION"]
    )

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_id)
        # Decrypts secret using the associated KMS CMK.
        # Depending on whether the secret is a string or binary,
        # one of these fields will be populated.
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
            j = json.loads(secret)
            return j[secret_key]
        decoded_binary_secret = base64.b64decode(
            get_secret_value_response['SecretBinary']).decode("UTF8")
        return decoded_binary_secret
    except ClientError as ex:
        if ex.response['Error']['Code'] == 'DecryptionFailureException':
            # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise ex
        if ex.response['Error']['Code'] == 'InternalServiceErrorException':
            # An error occurred on the server side.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise ex
        if ex.response['Error']['Code'] == 'InvalidParameterException':
            # You provided an invalid value for a parameter.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise ex
        if ex.response['Error']['Code'] == 'InvalidRequestException':
            # You provided a parameter value that is not valid for the current state of the resource.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise ex
        if ex.response['Error']['Code'] == 'ResourceNotFoundException':
            # We can't find the resource that you asked for.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise ex
        raise ex
