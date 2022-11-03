"""REST client handling, including ZohoBooksStream base class."""

import requests
from pathlib import Path
from typing import Any, Dict, Optional, Union, List, Iterable

from memoization import cached
from pendulum import parse
from singer_sdk.helpers.jsonpath import extract_jsonpath
from singer_sdk.streams import RESTStream

from tap_zohobooks.auth import OAuth2Authenticator


SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")


class ZohoBooksStream(RESTStream):
    """ZohoBooks stream class."""

    url_base = "https://books.zoho.com/api/v3"

    records_jsonpath = "$[*]"  # Or override `parse_response`.

    @cached
    def get_starting_time(self, context):
        if self.config.get("start_date"):
            start_date = self.config["start_date"]
        else:
            start_date = None

        rep_key = self.get_starting_replication_key_value(context)
        if rep_key:
            rep_key = parse(rep_key)
        return rep_key or start_date

    @property
    @cached
    def authenticator(self) -> OAuth2Authenticator:
        """Return a new authenticator object."""
        return OAuth2Authenticator(
            self, self._tap.config, "https://accounts.zoho.com/oauth/v2/token"
        )

    @property
    def http_headers(self) -> dict:
        """Return the http headers needed."""
        headers = {}
        if "user_agent" in self.config:
            headers["User-Agent"] = self.config.get("user_agent")
        return headers

    def get_next_page_token(
        self, response: requests.Response, previous_token: Optional[Any]
    ) -> Optional[Any]:
        """Return a token for identifying next page or None if no more pages."""

        # if has_more_page
        r = response.json()
        try:
            has_more_pages = r["page_context"]["has_more_page"]
            current_page = r["page_context"]["page"]
        except KeyError as ke:
            return None
        if not has_more_pages:
            return None

        return current_page + 1

    def get_url_params(
        self, context: Optional[dict], next_page_token: Optional[Any]
    ) -> Dict[str, Any]:
        """Return a dictionary of values to be used in URL parameterization."""
        params: dict = {}
        if context is not None:
            params["organization_id"] = context.get("organization_id")
        if next_page_token:
            params["page"] = next_page_token
        # if self.replication_key:
        #    params["sort"] = "asc"
        #    params["order_by"] = self.replication_key

        rep_key_value = self.get_starting_time(context)
        if rep_key_value is not None:
            params["last_modified_time"] = str(rep_key_value)
        return params
