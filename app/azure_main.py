# Work in progress

import azure.functions as func

from app import app

main = func.WsgiMiddleware(app).main