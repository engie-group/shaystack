# This code is to use with static checker and to have a typed AWS lambda parameters
# In lambda API, use api_event = cast(LambdaAPIEvent, AttrDict(event))
from typing import Dict, Any, List


class AttrDict(dict):
    """A dictionary with attribute-style access. It maps attribute access to
    the real dictionary.  """

    def __init__(self, init={}):
        dict.__init__(self, init)

    def __getstate__(self):
        return self.__dict__.items()

    def __setstate__(self, items):
        for key, val in items:
            self.__dict__[key] = val

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, dict.__repr__(self))

    def __setitem__(self, key, value):
        return super(AttrDict, self).__setitem__(key, value)

    def __getitem__(self, name):
        return super(AttrDict, self).__getitem__(name)

    def __delitem__(self, name):
        return super(AttrDict, self).__delitem__(name)

    __getattr__ = __getitem__
    __setattr__ = __setitem__


LambdaDict = Dict[str, Any]
LambdaEvent = Dict[str, Any]
LambdaResponse = Dict[str, Any]


class LambdaRequestCognitoIdentity(object):
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


class LambdaRequestContext(object):
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


class LambdaProxyEvent(object):
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
    def __init__(self):
        self["statusCode"] = 200
        self["headers"] = dict()
        self["cookies"] = list()
        self["isBase64Encoded"] = False

    def _asdict(self):
        return self

    statusCode: int
    isBase64Encoded: bool
    headers: Dict[str, str]
    cookies: List[str]
    # Only for version 1.0
    # See https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-develop-integrations-lambda.html
    # multiValueHeaders: Dict[str, List[str]]


class LambdaCognitoIdentity(object):
    cognito_identity_id: str
    cognito_identity_pool_id: str


class LambdaClientContextMobileClient(object):
    installation_id: str
    app_title: str
    app_version_name: str
    app_version_code: str
    app_package_name: str


class LambdaClientContext(object):
    client: LambdaClientContextMobileClient
    custom: LambdaDict
    env: LambdaDict


class LambdaContext(object):
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
        return 0
