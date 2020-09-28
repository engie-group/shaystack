# AWS Lambda target methods
from typing import Dict

from haystackapi import *


def lambda_about(event: Dict, context: Dict) -> Dict:
    flask_response = about(event.body, event.headers, event['requestContext']['stage'])
    response = {}
    response['headers']=flask_response.headers
    response['statusCode'] = flask_response.status  # pylint: disable=invalid-name
    response['headers']["Content-Type"] = flask_response.content_type
    response['body'] = flask_response.response
    return response



def lambda_ops(event: Dict, context: Dict) -> Dict:
    flask_response = ops(event.body, event.headers, event['requestContext']['stage'])
    response = {}
    response['headers']=flask_response.headers
    response['statusCode'] = flask_response.status  # pylint: disable=invalid-name
    response['headers']["Content-Type"] = flask_response.content_type
    response['body'] = flask_response.response
    return response


def lambda_formats(event: Dict, context: Dict) -> Dict:
    flask_response = formats(event.body, event.headers, event['requestContext']['stage'])
    response = {}
    response['headers']=flask_response.headers
    response['statusCode'] = flask_response.status  # pylint: disable=invalid-name
    response['headers']["Content-Type"] = flask_response.content_type
    response['body'] = flask_response.response
    return response


def lamnda_read(event: Dict, context: Dict) -> Dict:
    flask_response = read(event.body, event.headers, event['queryStringParameters'], event['requestContext']['stage'])
    response = {}
    response['headers']=flask_response.headers
    response['statusCode'] = flask_response.status  # pylint: disable=invalid-name
    response['headers']["Content-Type"] = flask_response.content_type
    response['body'] = flask_response.response
    return response


def lambda_nav(event: Dict, context: Dict) -> Dict:
    flask_response = nav(event.body, event.headers, event['queryStringParameters'], event['requestContext']['stage'])
    response = {}
    response['headers']=flask_response.headers
    response['statusCode'] = flask_response.status  # pylint: disable=invalid-name
    response['headers']["Content-Type"] = flask_response.content_type
    response['body'] = flask_response.response
    return response


def lambda_watch_sub(event: Dict, context: Dict) -> Dict:
    flask_response = watch_sub(event.body, event.headers, event['queryStringParameters'], event['requestContext']['stage'])
    response = {}
    response['headers']=flask_response.headers
    response['statusCode'] = flask_response.status  # pylint: disable=invalid-name
    response['headers']["Content-Type"] = flask_response.content_type
    response['body'] = flask_response.response
    return response


def lamnda_watch_unsub(event: Dict, context: Dict) -> Dict:
    flask_response = watch_unsub(event.body, event.headers, event['queryStringParameters'], event['requestContext']['stage'])
    response = {}
    response['headers']=flask_response.headers
    response['statusCode'] = flask_response.status  # pylint: disable=invalid-name
    response['headers']["Content-Type"] = flask_response.content_type
    response['body'] = flask_response.response
    return response


def lamnda_watch_poll(event: Dict, context: Dict) -> Dict:
    return watch_poll(event.body, event.headers, event['queryStringParameters'], event['requestContext']['stage'])
    response = {}
    response['headers']=flask_response.headers
    response['statusCode'] = flask_response.status  # pylint: disable=invalid-name
    response['headers']["Content-Type"] = flask_response.content_type
    response['body'] = flask_response.response
    return response


def lambda_point_write(event: Dict, context: Dict) -> Dict:
    flask_response = point_write(event.body, event.headers, event['queryStringParameters'], event['requestContext']['stage'])
    response = {}
    response['headers']=flask_response.headers
    response['statusCode'] = flask_response.status  # pylint: disable=invalid-name
    response['headers']["Content-Type"] = flask_response.content_type
    response['body'] = flask_response.response
    return response


def lamnda_his_read(event: Dict, context: Dict) -> Dict:
    flask_response = his_read(event.body, event.headers, event['queryStringParameters'], event['requestContext']['stage'])
    response = {}
    response['headers']=flask_response.headers
    response['statusCode'] = flask_response.status  # pylint: disable=invalid-name
    response['headers']["Content-Type"] = flask_response.content_type
    response['body'] = flask_response.response
    return response


def lamnda_his_write(event: Dict, context: Dict) -> Dict:
    flask_response = his_write(event.body, event.headers, event['queryStringParameters'], event['requestContext']['stage'])
    response = {}
    response['headers']=flask_response.headers
    response['statusCode'] = flask_response.status  # pylint: disable=invalid-name
    response['headers']["Content-Type"] = flask_response.content_type
    response['body'] = flask_response.response
    return response


def lambda_invoke_action(event: Dict, context: Dict) -> Dict:
    flask_response = invoke_action(event.body, event.headers, event['queryStringParameters'], event['requestContext']['stage'])
    response = {}
    response['headers']=flask_response.headers
    response['statusCode'] = flask_response.status  # pylint: disable=invalid-name
    response['headers']["Content-Type"] = flask_response.content_type
    response['body'] = flask_response.response
    return response


