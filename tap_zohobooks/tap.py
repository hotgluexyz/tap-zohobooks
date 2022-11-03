"""ZohoBooks tap class."""

from typing import List

from singer_sdk import Tap, Stream
from singer_sdk import typing as th  # JSON schema typing helpers

# TODO: Import your custom stream types here:
from tap_zohobooks.streams import (
    OrganizationIdStream,
    InvoicesStream,
    JournalsIdStream,
    JournalStream,
    ChartOfAccountsStream,
    SalesOrdersStream,
    ItemsStream,
    ContactsStream,
)

STREAM_TYPES = [
    OrganizationIdStream,
    JournalsIdStream,
    InvoicesStream,
    JournalStream,
    ChartOfAccountsStream,
    SalesOrdersStream,
    ItemsStream,
    ContactsStream,
]


class TapZohoBooks(Tap):
    """ZohoBooks tap class."""

    name = "tap-zohobooks"

    def __init__(
        self,
        config=None,
        catalog=None,
        state=None,
        parse_env_config=False,
        validate_config=True,
    ) -> None:
        self.config_file = config[0]
        super().__init__(config, catalog, state, parse_env_config, validate_config)

    # TODO: Update this section with the actual config values you expect:
    config_jsonschema = th.PropertiesList(
        th.Property(
            "access_token",
            th.StringType,
            required=True,
            secret=True,  # Flag config as protected.
            description="The token to authenticate against the API service",
        ),
        th.Property(
            "project_ids",
            th.ArrayType(th.StringType),
            required=False,
            description="Project IDs to replicate",
        ),
        th.Property(
            "start_date",
            th.DateTimeType,
            description="The earliest record date to sync",
        ),
        th.Property(
            "api_url",
            th.StringType,
            default="https://api.mysample.com",
            description="The url for the API service",
        ),
    ).to_dict()

    def discover_streams(self) -> List[Stream]:
        """Return a list of discovered streams."""
        return [stream_class(tap=self) for stream_class in STREAM_TYPES]


if __name__ == "__main__":
    TapZohoBooks.cli()
