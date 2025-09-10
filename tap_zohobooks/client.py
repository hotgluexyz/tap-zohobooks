"""REST client handling, including ZohoBooksStream base class."""

import json
from backports.cached_property import cached_property
import requests
from typing import Any, Dict, Optional, Iterable, Generator
import backoff
from memoization import cached
from datetime import datetime, timedelta
from requests import Response, Response as Response
from singer_sdk.streams import RESTStream
from datetime import datetime
from singer_sdk.exceptions import FatalAPIError, RetriableAPIError
from singer_sdk.pagination import BaseAPIPaginator
from time import sleep
from calendar import monthrange

from tap_zohobooks.auth import OAuth2Authenticator


class ZohoBooksPaginator(BaseAPIPaginator):
    def get_next(self, response):
        if self.has_more(response):
            return response.json().get("page_context", {}).get("page", 1) + 1
        return None

    def has_more(self, response: Response) -> bool:
        """Return True if there are more pages available."""

        return response.json().get("page_context", {}).get("has_more_page", False)


class ZohoBooksStream(RESTStream):
    """ZohoBooks stream class."""

    rate_limit_alert = False
    backoff_max_tries = 10

    def backoff_wait_generator(self) -> Generator[float, None, None]:
        return backoff.expo(base=4, factor=5, max_value=180)
    
    def get_new_paginator(self):
        return ZohoBooksPaginator(start_value=1)
    
    def _request(self, prepared_request, context={}) -> requests.Response:
        """
        Custom request function to enable us to throtle the requests,
        distributing them equaly during the runtime.
        """
        response = super()._request(prepared_request, context=context)
        rate_limit = response.headers.get("X-Rate-Limit-Limit")
        remaining_rate_limit = response.headers.get("X-Rate-Limit-Remaining")
        if rate_limit and remaining_rate_limit:
            # adds cooldown between requests (Rate limit is 30 requests per minute)
            sleep(2)
            rate_limit = int(rate_limit)
            remaining_rate_limit = int(remaining_rate_limit)
            if (rate_limit - remaining_rate_limit < 500) and not self.rate_limit_alert:
                self.logger.warning(
                    f"Rate limit is almost reached ({rate_limit - remaining_rate_limit} requests missing)"
                )
                self.rate_limit_alert = True

        return response

    @cached_property
    def url_base(self) -> str:
        url = self.config.get("accounts-server", "https://accounts.zoho.com")
        api_url = "https://www.zohoapis.com/books/v3/"
        # Mapping domain suffixes to their corresponding base API URIs
        domain_mapping = {
            '.com': 'https://www.zohoapis.com/books/',
            '.eu': 'https://www.zohoapis.eu/books/',
            '.in': 'https://www.zohoapis.in/books/',
            '.com.au': 'https://www.zohoapis.com.au/books/',
            '.jp': 'https://www.zohoapis.jp/books/',
            '.ca': 'https://www.zohoapis.ca/books/',
            '.com.cn': 'https://www.zohoapis.com.cn/books/',
            '.sa': 'https://www.zohoapis.sa/books/',
        }

        # Check for domain presence and update api_url dynamically
        for domain, base_api_url in domain_mapping.items():
            if url.endswith(domain):
                api_url = base_api_url + 'v3/'  # Append '/v3/' to the base URL
                break  # Stop checking further domains if found

        return api_url


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
    def account_server(self) -> str:
        DEFAULT_ACCOUNT_SERVER = "https://accounts.zoho.com"
        uri = self._tap.config.get("uri", DEFAULT_ACCOUNT_SERVER)

        # accounts-server should come from config. if it not exists, it will try to get the uri. if it is still not present in config, pick the default value
        account_server = self._tap.config.get("accounts-server", uri)
        return account_server

    @property
    @cached
    def authenticator(self) -> OAuth2Authenticator:
        """Return a new authenticator object."""

        return OAuth2Authenticator(
            self, self._tap.config, f"{self.account_server}/oauth/v2/token"
        )

    @property
    def http_headers(self) -> dict:
        """Return the http headers needed."""
        headers = {}
        if "user_agent" in self.config:
            headers["User-Agent"] = self.config.get("user_agent")
        return headers

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
            params["account_id"] = context.get("account_id")

        if next_page_token:
            params["page"] = next_page_token

        rep_key_value = self.get_starting_time(context)
        if rep_key_value is not None:
            start_date = self._infer_date(rep_key_value)
            start_date = start_date + timedelta(seconds=1)

            if start_date.microsecond > 0:
                start_date = start_date.replace(microsecond=0)

            start_date = start_date.isoformat()
            splited_start_date = start_date.split(":")
            start_date = ":".join(splited_start_date[:-1]) + splited_start_date[-1]
            params["last_modified_time"] = start_date
        # Params for reports
        if self.name in [
            "profit_and_loss",
            "report_account_transactions",
            "profit_and_loss_cash_based",
            "report_account_transactions_cash_based",
        ]:
            params = {}
            if next_page_token:
                params["page"] = next_page_token
            if context is not None:
                params["organization_id"] = context.get("organization_id")
            start_date = self.config.get(
                "reports_start_date"
            ) or self.get_starting_time(context)
            start_date = self._infer_date(start_date)
            params["from_date"] = start_date.strftime("%Y-%m-%d")
            today = datetime.now()
            _, last_day = monthrange(today.year, today.month)
            last_day_of_month = today.replace(day=last_day)
            params["to_date"] = last_day_of_month.strftime("%Y-%m-%d")
            if self.name in [
                "profit_and_loss_cash_based",
                "report_account_transactions_cash_based",
            ]:
                params["cash_based"] = True
        return params

    def sleep_until_next_day(self):
        now = datetime.now()
        # Calculate the start of the next day
        next_day = (now + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        # Calculate the difference in seconds
        time_to_sleep = (
            next_day - now
        ).total_seconds() + 1  # Add 1 second to account for rounding errors
        self.logger.info(
            f"Sleeping for {time_to_sleep} seconds until the start of the next day."
        )
        sleep(time_to_sleep)

    def is_valid_json(self, s: str):
        try:
            json.loads(s)
            return True
        except:
            return False

    def validate_response(self, response: requests.Response) -> None:
        headers = dict(response.headers)

        if "X-Rate-Limit-Remaining" in headers:
            if int(headers["X-Rate-Limit-Remaining"]) <= 0:
                self.logger.warn(
                    f"Daily API limit of {headers['X-Rate-Limit-Remaining']} reached for the account. Triggering sleep."
                )
                self.logger.info(f"Limit reached with headers: {headers}")
                # TODO once above log is reached check if limit-reset header is present and implement it
                # Daily limit reached sleep till next day
                self.sleep_until_next_day()

        if self.name in [
            "purchase_orders_details",
            "sales_orders_details",
            "item_details",
            "journals",
        ]:
            sleep(1.01)
        if (
            response.status_code in self.extra_retry_statuses
            or 500 <= response.status_code < 600
            or response.status_code == 400
        ):
            msg = self.response_error_message(response)
            raise RetriableAPIError(msg, response)
        elif 400 < response.status_code < 500:
            msg = self.response_error_message(response)
            raise FatalAPIError(msg, response.text)
        elif response.status_code == 200 and not self.is_valid_json(response.text):
            self.logger.error(f"Received a non-json response: {response.text}")
            raise RetriableAPIError("Received a non-json response", response)

        

    def _divide_chunks(self, list, limit=100):
        for i in range(0, len(list), limit):
            yield list[i : i + limit]

    def _prepare_details_request(self, url, params, details_param="item_ids"):
        if details_param not in params:
            raise ValueError("Missing details param for request")

        return self.build_prepared_request(
            method="GET",
            url=url,
            params=params,
            headers=self.http_headers,
            auth=self.authenticator,
        )

    def parse_response(self, response: Response) -> Iterable[dict]:
        if response.text == "" and response.status_code == 200:
            # Skip empty responses
            return []
        return super().parse_response(response)

