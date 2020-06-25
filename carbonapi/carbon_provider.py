import traceback
from abc import abstractmethod
from datetime import datetime
from typing import Any, Tuple, Dict, cast

from werkzeug.routing import Map

import hszinc
from HaystackInterface import HaystackInterface, EmptyGrid
from haystackapi_lambda import _parse_request, _format_response, _compress_response, log
from hszinc import Grid, Uri, MODE_ZINC
from lambda_types import LambdaContext, LambdaEvent, LambdaProxyResponse, LambdaProxyEvent, AttrDict

# FIXME: a déplacer dans un autre package ? CookieCutter ?
class CarbonProvider(HaystackInterface):
    def about(self) -> Grid:
        grid = hszinc.Grid(columns={
            "haystackVersion": {},  # Str version of REST implementation
            "tz": {},  # Str of server's default timezone
            "serverName": {},  # Str name of the server or project database
            "serverTime": {},  # TODO: type current DateTime of server's clock
            "serverBootTime": {},  # TODO: type DateTime when server was booted up
            "productName": {},  # Str name of the server software product
            "productUri": {},  # TODO: type Uri of the product's web site
            "productVersion": {},  # TODO: from git label. version of the server software product
            # "moduleName": {},  # module which implements Haystack server protocol if its a plug-in to the product
            # "moduleVersion": {}  # Str version of moduleName
        })
        grid.append(
            {
                "haystackVersion": "3.0",
                "tz": None,  # FIXME: set the tz
                "serverName": "localhost",  # FIXME: set the server name
                "serverTime": None,  # FIXME: set the serverTime
                "serverBootTime": None,  # FIXME: set the serverBootTime
                "productName": "carbonapi",
                "productUri": Uri("http://localhost:1234"),  # FIXME indiquer le port et trouver l'URL ?
                "productVersion": None,  # FIXME: set the product version
                "moduleName": "carbonapi",
                "moduleVersion": None  # FIXME: set the module version
            })
        return grid

    def read(self,input:Grid) -> Grid:
        return input  # FIXME


    def extend_with_co2e(_event: LambdaEvent,
                         context: LambdaContext) -> LambdaProxyResponse:  # pylint: disable=unused-argument
        """
        Read a haystack grid, inject CO2e, and return the same grid
        Parameters
        ----------
        _event Proxy event
        context AWS Lambda context

        Returns Proxy response
        -------

        """
        try:
            event = cast(LambdaProxyEvent, AttrDict(_event))
            grid = _parse_request(event)

            log.info("----> Call Carbon core calculation to update Haystack Grid")

            response = _format_response(event, grid, 200)
        except:
            error_grid = hszinc.Grid(metadata={
                "err": hszinc.MARKER,
                "id": "badId",
                "errTrace": traceback.format_exc()
            }, columns=[('id', [('meta', None)])])  # FIXME: pourquoi columns est nécessaire ? Devrait être None
            response = _format_response(event, error_grid, 400, MODE_ZINC)

        return _compress_response(event.headers.get("Accept-Encoding", None), response)

    def _download_uri(self, uri: str) -> str:
        """ Download Haystack from URI.
        The uri must be a classic url (file://, http:// ...)
        or a s3 urn (s3://).
        The suffix describe the file format.
        """
        assert uri
        parsed_uri = urlparse(uri, allow_fragments=False)
        if parsed_uri.scheme == "s3":
            s3 = boto3.client('s3')
            stream = BytesIO()
            s3.download_fileobj(parsed_uri.netloc, parsed_uri.path[1:], stream)
            return stream.getvalue().decode("utf-8")
        else:
            with urllib.request.urlopen(uri) as response:
                return response.read()
        # if (uri.endwith(".gz")): ...  # TODO : a valider

    def read(self, input: Grid) -> Grid:  # TODO
        log.info("----> Call Read API")
        uri = self._gets3()
        body = self._download_uri(self._gets3())

        if not body:
            raise ValueError(f"Empty body not supported")
        mode = MODE_JSON if (uri.endswith(".json")) else MODE_ZINC
        grid = hszinc.parse(body, mode)[0]
        # Very simple filter
        filter = ''
        if len(input):
            filter = input[0].get('filter', '')
        if filter:

            (key, val) = filter.split('==')
            result = Grid(version=grid.version, metadata=grid.metadata, columns=grid.column)
            for row in grid:
                if key in row and row[key] == val:
                    result.append(row)
            grid = result
        return grid
