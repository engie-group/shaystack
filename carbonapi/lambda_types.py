"""This code add a static checker and to have a typed AWS lambda parameters
In lambda API, use api_event = cast(LambdaAPIEvent, AttrDict(event))
"""
from typing import Dict, Any


class AttrDict(dict):
    """A dictionary with attribute-style access. It maps attribute access to
    the real dictionary.  """

    def __init__(self, init=None):
        dict.__init__(self, init)

    def __getstate__(self):
        return self.__dict__.items()

    def __setstate__(self, items):
        for key, val in items:
            self.__dict__[key] = val

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, dict.__repr__(self))

    def __setitem__(self, key, value):  # pylint: disable=useless-super-delegation
        return super(AttrDict, self).__setitem__(key, value)

    def __getitem__(self, name):  # pylint: disable=useless-super-delegation
        return super(AttrDict, self).__getitem__(name)

    def __delitem__(self, name):  # pylint: disable=useless-super-delegation
        return super(AttrDict, self).__delitem__(name)

    __getattr__ = __getitem__
    __setattr__ = __setitem__


LambdaDict = Dict[str, Any]
LambdaEvent = Dict[str, Any]
LambdaResponse = Dict[str, Any]


class LambdaRequestCognitoIdentity:
    """
    Lambda request cognito wrapper
    """
    cognitoIdentityPoolId: str
    accountId: str
    cognitoIdentityId: str
    caller: str
    accessKey: str
    sourceIp: str
    cognitoAuthenticationType: str
    cognitoAuthenticationProvider: str
    userArn: str
    userAgent: str
    user: str


class LambdaRequestContext:
    """
    Lambda request context wrapper
    """
    accountId: str
    resourceId: str
    stage: str
    requestId: str
    requestTime: str
    requestTimeEpoch: int
    identity: LambdaRequestCognitoIdentity
    path: str
    resourcePath: str
    httpMethod: str
    apiId: str
    protocol: str


class LambdaProxyEvent:
    """
    Lambda event from proxy wrapper
    """
    body: Any
    ressource: Any
    path: str
    httpMethod: str
    isBase64Encoded: bool
    queryStringParameters: Dict[str, str]
    pathParameters: Dict[str, str]
    stageVariables: Dict[str, str]
    headers: Dict[str, str]
    requestContext: LambdaRequestContext


class LambdaProxyResponse(AttrDict):
    """
    Lambda response to proxy wrapper
    """
    def __init__(self):  # pylint: disable=super-init-not-called
        self["statusCode"] = 200
        self["headers"] = dict()
        self["isBase64Encoded"] = False

    def _asdict(self):
        return self

    statusCode: int
    isBase64Encoded: bool
    headers: Dict[str, str]


class LambdaCognitoIdentity:
    """
    Lambda cognito identity wrapper
    """
    cognito_identity_id: str
    cognito_identity_pool_id: str


class LambdaClientContextMobileClient:
    """
    Lambda client context mobile wrapper
    """
    installation_id: str
    app_title: str
    app_version_name: str
    app_version_code: str
    app_package_name: str


class LambdaClientContext:
    """
    Lambda client context wrapper
    """
    client: LambdaClientContextMobileClient
    custom: LambdaDict
    env: LambdaDict


class LambdaContext:
    """
    Lambda context wrapper
    """
    function_name: str
    function_version: str
    invoked_function_arn: str
    memory_limit_in_mb: int
    aws_request_id: str
    log_group_name: str
    log_stream_name: str
    identity: LambdaCognitoIdentity
    client_context: LambdaClientContext

    @staticmethod
    def get_remaining_time_in_millis() -> int:
        """Return remaining time in millisecond """
        return 0
