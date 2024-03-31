"""
This module provides a base handler with some useful methods for all REST API handlers.
"""
from typing import Any
import falcon

from ..serialization import my_load_from_json, my_to_json


class BaseHandler():
    """
    Base class for all REST API handlers.
    """
    def send_invalid_resource_id_error(self, resp: falcon.Response) -> None:
        """
        Sends an error that th given resource ID (e.g. scenario ID, or SCADA data ID) is invalid.

        Paramaters
        ----------
        resp : `falcon.Response`
            Response instance.
        """
        resp.status = falcon.HTTP_BAD_REQUEST
        resp.data = "Invalid resource ID".encode()

    def send_json_parsing_error(self, resp: falcon.Response) -> None:
        """
        Sends an error that the JSON parsing failed.

        Paramaters
        ----------
        resp : `falcon.Response`
            Response instance.
        """
        resp.status = falcon.HTTP_BAD_REQUEST
        resp.data = "Failed to parse JSON".encode()

    def load_json_data_from_request(self, req: falcon.Request) -> Any:
        """
        Loads/Parses an object from given JSON data.

        Parameters
        ----------
        req : `falcon.Request`
            Request instance.

        Returns
        -------
        `Any`
            Loaded object.
        """
        try:
            return my_load_from_json(req.bounded_stream.read())
        except Exception:
            return None

    def send_json_response(self, resp: falcon.Response, data: Any) -> None:
        """
        Sends a JSON response.

        Paramaters
        ----------
        resp : `falcon.Response`
            Response instance.
        data : `Any`
            Data to be sent.
        """
        resp.content_type = falcon.MEDIA_JSON
        resp.status = falcon.HTTP_200
        resp.data = my_to_json(data).encode()
