import json
import logging
import os
from typing import cast

import hszinc  # type: ignore

from lambda_types import LambdaProxyEvent, LambdaContext, LambdaEvent, LambdaProxyResponse, AttrDict

if os.environ.get("DEBUGGING", "false").lower() == "true":
    # TODO: validate the attachement of debugger
    # https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-using-debugging-python.html
    import ptvsd  # type: ignore
    # Enable ptvsd on 0.0.0.0 address and on port 5890 that we'll connect later with our IDE
    ptvsd.enable_attach(address=('0.0.0.0', 5890), redirect_output=True)
    print("Connect debugger...")
    ptvsd.wait_for_attach()


log = logging.getLogger("carnonapi")
log.setLevel(level=os.environ.get("LOGLEVEL", "WARNING"))


def about(_event: LambdaEvent, context: LambdaContext) -> LambdaProxyResponse:
    # event = cast(LambdaProxyEvent, AttrDict(_event))
    # print(f"PATH={event.path}")
    print(f"function_name={context.function_name}")
    g = hszinc.Grid()
    log.info("Invoke /about")
    response = LambdaProxyResponse()
    response.statusCode = 200
    response.body = json.dumps({
        "message": "about",
    })
    return response


def extend_with_co2e(_event: LambdaEvent, context: LambdaContext) -> LambdaProxyResponse:
    # event = cast(LambdaProxyEvent, AttrDict(_event))
    log.info("Invoke /extend_with_co2e")
    response = LambdaProxyResponse()
    response.statusCode = 200
    response.body = json.dumps({
        "message": "extend_with_co2e",
    })
    return response
