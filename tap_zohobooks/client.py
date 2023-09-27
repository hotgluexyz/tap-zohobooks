"""REST client handling, including ZohoBooksStream base class."""

import requests
from pathlib import Path
from typing import Any, Dict, Optional, Union, List, Iterable, Generator
import urllib
import backoff
from memoization import cached
from pendulum import parse
from singer_sdk.helpers.jsonpath import extract_jsonpath
from singer_sdk.streams import RESTStream
from datetime import datetime, timezone
from singer_sdk.exceptions import FatalAPIError, RetriableAPIError
from time import sleep

from tap_zohobooks.auth import OAuth2Authenticator


SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")


class ZohoBooksStream(RESTStream):
    """ZohoBooks stream class."""
    rate_limit_alert = False

    def _request(self, prepared_request, context={}) -> requests.Response:
        """
        Custom request function to enable us to throtle the requests,
        distributing them equaly during the runtime.
        """
        response = super()._request(prepared_request, context=context)
        rate_limit = response.headers.get("X-Rate-Limit-Limit")
        remaining_rate_limit = response.headers.get("X-Rate-Limit-Remaining")
        if rate_limit and remaining_rate_limit:
            sleep(2) # adds cooldown between requests (Rate limit is 30 requests per minute)
            rate_limit = int(rate_limit)
            remaining_rate_limit = int(remaining_rate_limit)
            if (rate_limit - remaining_rate_limit < 500) and not self.rate_limit_alert:
                self.logger.warning("Rate limit is almost reached (500 requests missing)")
                self.rate_limit_alert = True

        return response

    @property
    def url_base(self) -> str:
        """Return the API URL root, configurable via tap settings."""
        account_server = self._tap.config.get(
            "accounts-server", "https://accounts.zoho.com"
        )
        account_server = account_server.replace("accounts.", "books.")
        return f"{account_server}/api/v3"

    records_jsonpath = "$[*]"  # Or override `parse_response`.

    @cached
    def get_starting_time(self, context):
        if self.config.get("start_date"):
            start_date = self.config["start_date"]
        else:
            start_date = None

        rep_key = self.get_starting_replication_key_value(context)
        return rep_key or start_date

    @property
    @cached
    def authenticator(self) -> OAuth2Authenticator:
        """Return a new authenticator object."""
        account_server = self._tap.config.get(
            "accounts-server", "https://accounts.zoho.com"
        )
        return OAuth2Authenticator(
            self, self._tap.config, f"{account_server}/oauth/v2/token"
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
    

    def _infer_date(self, date):
        date_formats = [
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M%z",
            "%Y-%m-%d",
        ]
        for date_format in date_formats:
            try:
                return datetime.strptime(date, date_format)
            except ValueError:
                continue

        raise ValueError("No valid date format found")

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
            start_date = self._infer_date(rep_key_value)
            start_date = start_date.replace(tzinfo=timezone.utc).timestamp()
            start_date = datetime.fromtimestamp(start_date).strftime(
                "%Y-%m-%dT%H:%M:%S"
            )
            start_date = start_date + "-0000"
            params["last_modified_time"] = start_date
        return params

    def backoff_wait_generator(self) -> Generator[float, None, None]:
        return backoff.expo(base=2, factor=5)

    def backoff_max_tries(self) -> int:
        return 7

    def validate_response(self, response: requests.Response) -> None:
        if self.name in ["purchase_orders_details", "sales_orders_details", "item_details", "journals"]:
            sleep(1.01)
        if (
            response.status_code in self.extra_retry_statuses
            or 500 <= response.status_code < 600
        ):
            msg = self.response_error_message(response)
            raise RetriableAPIError(msg, response)
        elif 400 <= response.status_code < 500:
            msg = self.response_error_message(response)
            raise FatalAPIError(msg)

    def _divide_chunks(self, list, limit=100):
        for i in range(0, len(list), limit):
            yield list[i : i + limit]

    def _prepare_details_request(self, url, params, details_param = "item_ids"):
        if details_param not in params:
            raise ValueError("Missing details param for request")
        
        return self.build_prepared_request(
            method="GET",
            url=url,
            params=params,
            headers=self.http_headers,
            auth=self.authenticator
        )