"""Stream type classes for tap-zohobooks."""
import requests

from collections import OrderedDict

from typing import Optional

from singer_sdk import typing as th  # JSON Schema typing helpers
from singer_sdk.helpers.jsonpath import extract_jsonpath
from tap_zohobooks.client import ZohoBooksStream


class OrganizationIdStream(ZohoBooksStream):
    name = "organization_id"
    path = "/organizations"
    primary_keys = ["organization_id"]
    replication_key = None
    records_jsonpath = "$.organizations[*]"
    first_run = True

    schema = th.PropertiesList(
        th.Property("organization_id", th.StringType),
    ).to_dict()

    def get_child_context(self, record: dict, context: Optional[dict]) -> dict:
        """Return a context dictionary for child streams."""
        return {
            "organization_id": record["organization_id"],
        }

    def _sync_children(self, child_context: dict) -> None:
        child_streams_len = len(self.child_streams)
        for child_stream in self.child_streams:
            if child_stream.selected or child_stream.has_selected_descendents:
                organization_id = self.config.get("organization_id")
                # if organization_id is set in the config only fetch that organization
                if organization_id and self.first_run:
                    child_context = {
                        "organization_id": organization_id
                    }
                    # Check if it is the last child stream to fetch
                    if child_stream == self.child_streams[child_streams_len-1]:
                        self.first_run = False
                    child_stream.sync(context=child_context)
                # if not otganization_id is set in the config fetch all organizations
                elif not organization_id:
                    child_stream.sync(context=child_context)


class JournalsIdStream(ZohoBooksStream):
    name = "journals_id"
    path = "/journals"
    primary_keys = ["journal_id"]
    replication_key = None
    records_jsonpath: str = "$.journals[*]"
    parent_stream_type = OrganizationIdStream

    schema = th.PropertiesList(
        th.Property("journal_id", th.StringType),
        th.Property("journal_date", th.StringType),
        th.Property("entry_number", th.StringType),
        th.Property("reference_number", th.StringType),
        th.Property("currency_id", th.StringType),
        th.Property("status", th.StringType),
        th.Property("notes", th.StringType),
        th.Property("journal_type", th.StringType),
        th.Property("entity_type", th.StringType),
        th.Property("total", th.CustomType({"type": ["number", "string"]})),
        th.Property("bcy_total", th.CustomType({"type": ["number", "string"]})),
        th.Property("created_by_id", th.StringType),
        th.Property("created_by_name", th.StringType),
        th.Property("documents", th.CustomType({"type": ["array", "string"]})),
    ).to_dict()

    def get_child_context(self, record: dict, context: Optional[dict]) -> dict:
        """Return a context dictionary for child streams."""
        return {
            "organization_id": context.get("organization_id"),
            "journal_id": record["journal_id"],
        }


class JournalStream(ZohoBooksStream):
    name = "journals"
    path = "/journals/{journal_id}"
    primary_keys = ["journal_id"]
    replication_key = "last_modified_time"
    records_jsonpath: str = "$.journal"
    parent_stream_type = JournalsIdStream
    # no need to set the org_id parent because it's a parent to JournalsIdStream
    # so all journal id returned will be already org_id filtered

    line_object_schema = th.ObjectType(
        th.Property("line_id", th.StringType),
        th.Property("account_id", th.StringType),
        th.Property("customer_id", th.StringType),
        th.Property("customer_name", th.StringType),
        th.Property("account_name", th.StringType),
        th.Property("description", th.StringType),
        th.Property("debit_or_credit", th.StringType),
        th.Property("tax_exemption_id", th.StringType),
        th.Property("tax_exemption_type", th.StringType),
        th.Property("tax_exemption_code", th.StringType),
        th.Property("tax_authority_id", th.StringType),
        th.Property("tax_authority_name", th.StringType),
        th.Property("tax_id", th.StringType),
        th.Property("tax_name", th.StringType),
        th.Property("tax_type", th.StringType),
        th.Property("tax_percentage", th.StringType),
        th.Property("amount", th.CustomType({"type": ["number", "string"]})),
        th.Property("bcy_amount", th.CustomType({"type": ["number", "string"]})),
        th.Property("acquisition_vat_id", th.StringType),
        th.Property("acquisition_vat_name", th.StringType),
        th.Property("acquisition_vat_percentage", th.StringType),
        th.Property("acquisition_vat_amount", th.StringType),
        th.Property("reverse_charge_vat_id", th.StringType),
        th.Property("reverse_charge_vat_name", th.StringType),
        th.Property("reverse_charge_vat_percentage", th.StringType),
        th.Property("reverse_charge_vat_amount", th.StringType),
        th.Property(
            "tags",
            th.ArrayType(
                th.ObjectType(
                    th.Property("is_tag_mandatory", th.BooleanType),
                    th.Property("tag_id", th.StringType),
                    th.Property("tag_name", th.StringType),
                    th.Property("tag_option_id", th.StringType),
                    th.Property("tag_option_name", th.StringType),
                )
            ),
        ),
        th.Property("project_id", th.StringType),
        th.Property("project_name", th.StringType),
    )

    schema = th.PropertiesList(
        th.Property("journal_id", th.StringType),
        th.Property("entry_number", th.StringType),
        th.Property("reference_number", th.StringType),
        th.Property("notes", th.StringType),
        th.Property("currency_id", th.StringType),
        th.Property("currency_code", th.StringType),
        th.Property("currency_symbol", th.StringType),
        th.Property("exchange_rate", th.CustomType({"type": ["number", "string"]})),
        th.Property("journal_date", th.StringType),
        th.Property("journal_type", th.StringType),
        th.Property("vat_treatment", th.StringType),
        th.Property("product_type", th.StringType),
        th.Property("include_in_vat_return", th.BooleanType),
        th.Property("is_bas_adjustment", th.BooleanType),
        th.Property("line_items", th.ArrayType(line_object_schema)),
        th.Property("line_item_total", th.CustomType({"type": ["number", "string"]})),
        th.Property("total", th.CustomType({"type": ["number", "string"]})),
        th.Property("bcy_total", th.CustomType({"type": ["number", "string"]})),
        th.Property("price_precision", th.CustomType({"type": ["number", "string"]})),
        th.Property(
            "taxes",
            th.ArrayType(
                th.ObjectType(
                    th.Property("tax_name", th.StringType),
                    th.Property("tax_amount", th.IntegerType),
                    th.Property("debit_or_credit", th.StringType),
                    th.Property("tax_account", th.BooleanType),
                )
            ),
        ),
        th.Property("created_time", th.DateTimeType),
        th.Property("last_modified_time", th.DateTimeType),
        th.Property("status", th.StringType),
        th.Property("custom_fields", th.CustomType({"type": ["array", "string"]})),
    ).to_dict()


class ChartOfAccountsStream(ZohoBooksStream):
    name = "chart_of_accounts"
    path = "/chartofaccounts"
    primary_keys = ["account_id"]
    replication_key = "last_modified_time"
    records_jsonpath: str = "$.chartofaccounts[*]"
    parent_stream_type = OrganizationIdStream

    schema = th.PropertiesList(
        th.Property("account_id", th.StringType),
        th.Property("account_name", th.StringType),
        th.Property("account_code", th.StringType),
        th.Property("account_type", th.StringType),
        th.Property("is_user_created", th.BooleanType),
        th.Property("is_system_account", th.BooleanType),
        th.Property("is_standalone_account", th.BooleanType),
        th.Property("is_active", th.BooleanType),
        th.Property("can_show_in_ze", th.BooleanType),
        th.Property("is_involved_in_transaction", th.BooleanType),
        th.Property("current_balance", th.StringType),
        th.Property("parent_account_id", th.StringType),
        th.Property("parent_account_name", th.StringType),
        th.Property("depth", th.IntegerType),
        th.Property("has_attachment", th.BooleanType),
        th.Property("is_child_present", th.BooleanType),
        th.Property("child_count", th.CustomType({"type": ["number", "string"]})),
        th.Property("documents", th.ArrayType(th.StringType)),
        th.Property("created_time", th.DateTimeType),
        th.Property("last_modified_time", th.DateTimeType),
    ).to_dict()


class ItemsStream(ZohoBooksStream):
    name = "items"
    path = "/items"
    primary_keys = ["item_id"]
    replication_key = "last_modified_time"
    records_jsonpath: str = "$.items[*]"
    parent_stream_type = OrganizationIdStream
    use_item_details = False

    schema = th.PropertiesList(
        th.Property("name", th.StringType),
        th.Property("line_items", th.CustomType({"type": ["array", "string"]})),
        th.Property("rate", th.CustomType({"type": ["number", "string"]})),
        th.Property("description", th.StringType),
        th.Property("tax_id", th.StringType),
        th.Property("item_id", th.StringType),
        th.Property("item_name", th.StringType),
        th.Property("crm_owner_id", th.StringType),
        th.Property("unit", th.StringType),
        th.Property("unitkey_code", th.StringType),
        th.Property("status", th.StringType),
        th.Property("source", th.StringType),
        th.Property("is_linked_with_zohocrm", th.BooleanType),
        th.Property("is_fulfillable", th.BooleanType),
        th.Property("zcrm_product_id", th.StringType),
        th.Property("is_taxable", th.BooleanType),
        th.Property("tax_name", th.StringType),
        th.Property("tax_percentage", th.IntegerType),
        th.Property("sales_rate", th.CustomType({"type": ["number", "string"]})),
        th.Property("unit_id", th.StringType),
        th.Property("tax_exemption_id", th.StringType),
        th.Property("purchase_account_id", th.StringType),
        th.Property("purchase_account_name", th.StringType),
        th.Property("purchase_tax_rule_id", th.CustomType({"type": ["number", "string"]})),
        th.Property("purchase_description", th.StringType),
        th.Property("purchase_rate", th.CustomType({"type": ["number", "string"]})),
        th.Property("sales_tax_rule_id", th.CustomType({"type": ["number", "string"]})),
        th.Property("avatax_tax_code", th.CustomType({"type": ["number", "string"]})),
        th.Property("avatax_use_code", th.CustomType({"type": ["number", "string"]})),
        th.Property("account_id", th.StringType),
        th.Property("account_name", th.StringType),
        th.Property("item_type", th.StringType),
        th.Property("product_type", th.StringType),
        th.Property("hsn_or_sac", th.StringType),
        th.Property("sat_item_key_code", th.StringType),
        th.Property("stock_on_hand", th.CustomType({"type": ["number", "string"]})),
        th.Property("has_attachment", th.BooleanType),
        th.Property("available_stock", th.CustomType({"type": ["number", "string"]})),
        th.Property("actual_available_stock", th.CustomType({"type": ["number", "string"]})),
        th.Property("sku", th.StringType),
        th.Property("reorder_level", th.CustomType({"type": ["number", "string"]})),
        th.Property("initial_stock", th.StringType),
        th.Property("brand", th.StringType),
        th.Property("initial_stock_rate", th.StringType),
        th.Property("image_name", th.StringType),
        th.Property("image_type", th.StringType),
        th.Property("image_document_id", th.StringType),
        th.Property("created_time", th.DateTimeType),
        th.Property("last_modified_time", th.DateTimeType),
        th.Property("show_in_storefront", th.BooleanType),
        th.Property("vendor_id", th.StringType),
        th.Property("vendor_name", th.StringType),
        th.Property("tax_type", th.StringType),
        th.Property("associated_template_id", th.StringType),
        th.Property("inventory_account_id", th.StringType),
        th.Property("inventory_account_name", th.StringType),
        th.Property("is_combo_product", th.BooleanType),
        th.Property("manufacturer", th.StringType),
        th.Property("pricebook_rate", th.CustomType({"type": ["number", "string"]})),
        th.Property(
            "sales_channels", th.CustomType({"type": ["array", "string"]})
        ),
        th.Property(
            "price_brackets", th.CustomType({"type": ["array", "string"]})
        ),
        th.Property("package_details", th.ObjectType(
            th.Property("length", th.CustomType({"type": ["number", "string"]})),
            th.Property("width", th.CustomType({"type": ["number", "string"]})),
            th.Property("height", th.CustomType({"type": ["number", "string"]})),
            th.Property("weight", th.CustomType({"type": ["number", "string"]})),
            th.Property("weight_unit", th.StringType),
            th.Property("dimension_unit", th.StringType),
        )),
        th.Property(
            "tags", th.CustomType({"type": ["array", "string"]})
        ),
        th.Property(
            "item_tax_preferences", th.CustomType({"type": ["array", "string"]})
        ),
        th.Property(
            "custom_fields", th.CustomType({"type": ["array", "string"]})
        ),
        th.Property(
            "preferred_vendors", th.CustomType({"type": ["array", "string"]})
        ),
        th.Property("warehouses", th.CustomType({"type": ["array", "string"]})),
        th.Property("documents", th.CustomType({"type": ["array", "string"]})),
        th.Property("custom_field_hash", th.CustomType({"type": ["object", "string"]})),
        th.Property("minimum_order_quantity", th.StringType),
        th.Property("maximum_order_quantity", th.StringType),
        th.Property("offline_created_date_with_time", th.DateTimeType),
    ).to_dict()

    def get_child_context(self, record: dict, context: Optional[dict]) -> dict:
        """Return a context dictionary for child streams."""
        return {
            "item_id": record["item_id"],
            "organization_id": context.get("organization_id"),
        }

    def parse_response(self, response):
        """
        This function works getting all of the data from the Stream
        and adds item details to each item of the stream available.

        It does it using the /itemdetails endpoint, chunking with
        100 ids per request.
        """
        if not self.config.get("use_item_details", False):
            yield from super().parse_response(response)
            return

        # gets organization id from the url
        org_id = response.url.replace(
            self.url_base + "/items?", ""
        ).split("&")[0].replace("organization_id=", "")
        details_base_url = self.url_base + "/itemdetails"
        records = list(extract_jsonpath(self.records_jsonpath, input=response.json()))

        # get all item ids from the records and create a dict with it
        record_ids = OrderedDict((record.get("item_id"), record) for record in records)

        # chunks the request, preserving API quota
        for chunk in self._divide_chunks(list(record_ids.keys())):
            params = {
                "organization_id": org_id,
                "item_ids": ",".join(chunk)
            }

            req = requests.Request(
                "GET",
                details_base_url,
                params=params,
                headers=self.authenticator.auth_headers
            )
            detail_response = self._request(req.prepare())

            item_details = extract_jsonpath(self.records_jsonpath, input=detail_response.json())

            for item_detail in item_details:
                for key in [
                    key for key in item_detail.keys()
                    if key not in record_ids[item_detail["item_id"]]
                ]:
                    # Adds data from missing keys
                    record_ids[item_detail["item_id"]][key] = item_detail[key]

                yield record_ids[item_detail["item_id"]]


class ItemsDetailStream(ZohoBooksStream):
    name = "item_details"
    path = "/items/{item_id}"
    primary_keys = ["item_id"]
    replication_key = "last_modified_time"
    records_jsonpath: str = "$.item[*]"
    parent_stream_type = ItemsStream

    schema = th.PropertiesList(
        th.Property("name", th.StringType),
        th.Property("rate", th.CustomType({"type": ["number", "string"]})),
        th.Property("description", th.StringType),
        th.Property("tax_id", th.StringType),
        th.Property("item_id", th.StringType),
        th.Property("vendor_id", th.StringType),
        th.Property("item_name", th.StringType),
        th.Property("unit", th.StringType),
        th.Property("unitkey_code", th.StringType),
        th.Property("status", th.StringType),
        th.Property("source", th.StringType),
        th.Property("is_linked_with_zohocrm", th.BooleanType),
        th.Property("is_fulfillable", th.BooleanType),
        th.Property("is_default_tax_applied", th.BooleanType),
        th.Property("crm_owner_id", th.StringType),
        th.Property("zcrm_product_id", th.StringType),
        th.Property("is_taxable", th.BooleanType),
        th.Property("tax_name", th.StringType),
        th.Property("tax_percentage", th.IntegerType),
        th.Property("tax_type", th.StringType),
        th.Property("tax_exemption_id", th.StringType),
        th.Property("purchase_account_id", th.StringType),
        th.Property("purchase_account_name", th.StringType),
        th.Property("purchase_tax_rule_id", th.CustomType({"type": ["number", "string"]})),
        th.Property("purchase_description", th.StringType),
        th.Property("purchase_rate", th.CustomType({"type": ["number", "string"]})),
        th.Property("sales_tax_rule_id", th.CustomType({"type": ["number", "string"]})),
        th.Property("avatax_tax_code", th.CustomType({"type": ["number", "string"]})),
        th.Property("avatax_use_code", th.CustomType({"type": ["number", "string"]})),
        th.Property("account_id", th.StringType),
        th.Property("account_name", th.StringType),
        th.Property("inventory_account_id", th.StringType),
        th.Property("item_type", th.StringType),
        th.Property("product_type", th.StringType),
        th.Property("hsn_or_sac", th.StringType),
        th.Property("sat_item_key_code", th.StringType),
        th.Property("stock_on_hand", th.CustomType({"type": ["number", "string"]})),
        th.Property("has_attachment", th.BooleanType),
        th.Property("available_stock", th.CustomType({"type": ["number", "string"]})),
        th.Property("actual_available_stock", th.CustomType({"type": ["number", "string"]})),
        th.Property("sku", th.StringType),
        th.Property("reorder_level", th.CustomType({"type": ["number", "string"]})),
        th.Property("initial_stock", th.CustomType({"type": ["number", "string"]})),
        th.Property("brand", th.StringType),
        th.Property("associated_template_id", th.StringType),
        th.Property("initial_stock_rate", th.CustomType({"type": ["number", "string"]})),
        th.Property("image_name", th.StringType),
        th.Property("image_type", th.StringType),
        th.Property("created_at", th.DateType),
        th.Property("created_time", th.DateTimeType),
        th.Property("last_modified_time", th.DateTimeType),
        th.Property("show_in_storefront", th.BooleanType),
        th.Property("vendor_id", th.StringType),
        th.Property("vendor_name", th.StringType),
        th.Property("tax_type", th.StringType),
        th.Property("inventory_account_id", th.StringType),
        th.Property("inventory_account_name", th.StringType),
        th.Property("pricebook_rate", th.CustomType({"type": ["number", "string"]})),
        th.Property("sales_rate", th.CustomType({"type": ["number", "string"]})),
        th.Property("unit_id", th.StringType),
        th.Property("zcrm_product_id", th.StringType),
        th.Property("reorder_level", th.CustomType({"type": ["number", "string"]})),
        th.Property(
            "sales_channels", th.CustomType({"type": ["array", "string"]})
        ),
        th.Property("package_details", th.ObjectType(
            th.Property("length", th.CustomType({"type": ["number", "string"]})),
            th.Property("width", th.CustomType({"type": ["number", "string"]})),
            th.Property("height", th.CustomType({"type": ["number", "string"]})),
            th.Property("weight", th.CustomType({"type": ["number", "string"]})),
            th.Property("weight_unit", th.StringType),
            th.Property("dimension_unit", th.StringType),
        )),
        th.Property(
            "tags", th.CustomType({"type": ["array", "string"]})
        ),
        th.Property(
            "item_tax_preferences", th.CustomType({"type": ["array", "string"]})
        ),
        th.Property(
            "custom_fields", th.CustomType({"type": ["array", "string"]})
        ),
        th.Property("manufacturer", th.StringType),
        th.Property("minimum_order_quantity", th.StringType),
        th.Property("maximum_order_quantity", th.StringType),
        th.Property("offline_created_date_with_time", th.DateTimeType),
        th.Property(
            "preferred_vendors", th.ArrayType(th.ObjectType(
                th.Property("is_primary", th.BooleanType),
                th.Property("item_price", th.CustomType({"type": ["number", "string"]})),
                th.Property("item_stock", th.CustomType({"type": ["number", "string"]})),
                th.Property("last_modified_time", th.DateTimeType),
                th.Property("vendor_id", th.StringType),
                th.Property("vendor_name", th.StringType),
            ))
        ),
        th.Property("warehouses", th.CustomType({"type": ["array", "string"]})),
        th.Property("documents", th.CustomType({"type": ["array", "string"]})),
        th.Property("custom_field_hash", th.CustomType({"type": ["object", "string"]})),
    ).to_dict()


class InvoicesStream(ZohoBooksStream):
    name = "invoices"
    path = "/invoices"
    primary_keys = ["invoice_id"]
    replication_key = "last_modified_time"
    records_jsonpath = "$.invoices[*]"
    parent_stream_type = OrganizationIdStream

    schema = th.PropertiesList(
        th.Property("invoice_id", th.StringType),
        th.Property("ach_payment_initiated", th.BooleanType),
        th.Property("zcrm_potential_id", th.StringType),
        th.Property("zcrm_potential_name", th.StringType),
        th.Property("customer_name", th.StringType),
        th.Property("customer_id", th.StringType),
        th.Property("company_name", th.StringType),
        th.Property("status", th.StringType),
        th.Property("color_code", th.StringType),
        th.Property("current_sub_status_id", th.StringType),
        th.Property("current_sub_status", th.StringType),
        th.Property("invoice_number", th.StringType),
        th.Property("reference_number", th.StringType),
        th.Property("date", th.StringType),
        th.Property("due_date", th.StringType),
        th.Property("due_days", th.StringType),
        th.Property("currency_id", th.StringType),
        th.Property("schedule_time", th.StringType),
        th.Property("email", th.StringType),
        th.Property("currency_code", th.StringType),
        th.Property("currency_symbol", th.StringType),
        th.Property("template_type", th.StringType),
        th.Property("is_viewed_by_client", th.BooleanType),
        th.Property("has_attachment", th.BooleanType),
        th.Property("client_viewed_time", th.StringType),
        th.Property("invoice_url", th.StringType),
        th.Property("project_name", th.StringType),
        th.Property(
            "billing_address",
            th.ObjectType(
                th.Property("address", th.StringType),
                th.Property("street2", th.StringType),
                th.Property("city", th.StringType),
                th.Property("state", th.StringType),
                th.Property("zipcode", th.StringType),
                th.Property("country", th.StringType),
                th.Property("phone", th.StringType),
                th.Property("fax", th.StringType),
                th.Property("attention", th.StringType),
            ),
        ),
        th.Property(
            "shipping_address",
            th.ObjectType(
                th.Property("address", th.StringType),
                th.Property("street2", th.StringType),
                th.Property("city", th.StringType),
                th.Property("state", th.StringType),
                th.Property("zipcode", th.StringType),
                th.Property("country", th.StringType),
                th.Property("phone", th.StringType),
                th.Property("fax", th.StringType),
                th.Property("attention", th.StringType),
            ),
        ),
        th.Property("country", th.StringType),
        th.Property("phone", th.StringType),
        th.Property("created_by", th.StringType),
        th.Property("updated_time", th.StringType),
        th.Property("transaction_type", th.StringType),
        th.Property("total", th.CustomType({"type": ["number", "string"]})),
        th.Property("balance", th.CustomType({"type": ["number", "string"]})),
        th.Property("created_time", th.DateTimeType),
        th.Property("last_modified_time", th.DateTimeType),
        th.Property("is_emailed", th.BooleanType),
        th.Property("is_viewed_in_mail", th.BooleanType),
        th.Property("mail_first_viewed_time", th.StringType),
        th.Property("mail_last_viewed_time", th.StringType),
        th.Property("reminders_sent", th.IntegerType),
        th.Property("last_reminder_sent_date", th.StringType),
        th.Property("payment_expected_date", th.StringType),
        th.Property("last_payment_date", th.StringType),
        th.Property("custom_fields", th.CustomType({"type": ["array", "string"]})),
        th.Property("custom_field_hash", th.CustomType({"type": ["array", "object"]})),
        th.Property("template_id", th.StringType),
        th.Property("documents", th.StringType),
        th.Property("salesperson_id", th.StringType),
        th.Property("salesperson_name", th.StringType),
        th.Property("shipping_charge", th.CustomType({"type": ["number", "string"]})),
        th.Property("adjustment", th.CustomType({"type": ["number", "string"]})),
        th.Property("write_off_amount", th.CustomType({"type": ["number", "string"]})),
        th.Property("exchange_rate", th.CustomType({"type": ["number", "string"]})),
    ).to_dict()


class ContactsStream(ZohoBooksStream):
    name = "contacts"
    path = "/contacts"
    primary_keys = ["contact_id"]
    replication_key = "last_modified_time"
    records_jsonpath: str = "$.contacts[*]"
    parent_stream_type = OrganizationIdStream

    schema = th.PropertiesList(
        th.Property("contact_id", th.StringType),
        th.Property("contact_name", th.StringType),
        th.Property("customer_name", th.StringType),
        th.Property("vendor_name", th.StringType),
        th.Property("company_name", th.StringType),
        th.Property("website", th.StringType),
        th.Property("language_code", th.StringType),
        th.Property("language_code_formatted", th.StringType),
        th.Property("contact_type", th.StringType),
        th.Property("contact_type_formatted", th.StringType),
        th.Property("status", th.StringType),
        th.Property("customer_sub_type", th.StringType),
        th.Property("source", th.StringType),
        th.Property("is_linked_with_zohocrm", th.BooleanType),
        th.Property("payment_terms", th.IntegerType),
        th.Property("payment_terms_label", th.StringType),
        th.Property("currency_id", th.StringType),
        th.Property("twitter", th.StringType),
        th.Property("facebook", th.StringType),
        th.Property("currency_code", th.StringType),
        th.Property("outstanding_receivable_amount", th.CustomType({"type": ["number", "string"]})),
        th.Property("outstanding_receivable_amount_bcy", th.CustomType({"type": ["number", "string"]})),
        th.Property("outstanding_payable_amount", th.CustomType({"type": ["number", "string"]})),
        th.Property("outstanding_payable_amount_bcy", th.CustomType({"type": ["number", "string"]})),
        th.Property("unused_credits_receivable_amount", th.CustomType({"type": ["number", "string"]})),
        th.Property("unused_credits_receivable_amount_bcy", th.CustomType({"type": ["number", "string"]})),
        th.Property("unused_credits_payable_amount", th.CustomType({"type": ["number", "string"]})),
        th.Property("unused_credits_payable_amount_bcy", th.CustomType({"type": ["number", "string"]})),
        th.Property("first_name", th.StringType),
        th.Property("last_name", th.StringType),
        th.Property("email", th.StringType),
        th.Property("phone", th.StringType),
        th.Property("mobile", th.StringType),
        th.Property("portal_status", th.StringType),
        th.Property("track_1099", th.BooleanType),
        th.Property("created_time", th.DateTimeType),
        th.Property("created_time_formatted", th.DateTimeType),
        th.Property("last_modified_time", th.StringType),
        th.Property("last_modified_time_formatted", th.StringType),
        th.Property("custom_fields", th.CustomType({"type": ["array", "string"]})),
        th.Property("custom_field_hash", th.CustomType({"type": ["array", "object"]})),
        th.Property("ach_supported", th.BooleanType),
        th.Property("has_attachment", th.BooleanType),
    ).to_dict()


class BillsStream(ZohoBooksStream):
    name = "bills"
    path = "/bills"
    primary_keys = ["bill_id"]
    replication_key = "last_modified_time"
    records_jsonpath: str = "$.bills[*]"
    parent_stream_type = OrganizationIdStream

    schema = th.PropertiesList(
        th.Property("bill_id", th.StringType),
        th.Property("vendor_id", th.StringType),
        th.Property("vendor_id", th.StringType),
        th.Property("vendor_name", th.StringType),
        th.Property("status", th.StringType),
        th.Property("bill_number", th.StringType),
        th.Property("reference_number", th.StringType),
        th.Property("date", th.DateType),
        th.Property("due_date", th.DateType),
        th.Property("due_days", th.StringType),
        th.Property("currency_id", th.StringType),
        th.Property("currency_code", th.StringType),
        th.Property("price_precision", th.CustomType({"type": ["number", "string"]})),
        th.Property("exchange_rate", th.CustomType({"type": ["number", "string"]})),
        th.Property("total", th.CustomType({"type": ["number", "string"]})),
        th.Property("balance", th.CustomType({"type": ["number", "string"]})),
        th.Property("created_time", th.DateTimeType),
        th.Property("last_modified_time", th.DateTimeType),
        th.Property("attachment_name", th.StringType),
        th.Property("has_attachment", th.BooleanType),
        th.Property("is_tds_applied", th.BooleanType),
        th.Property("is_abn_quoted", th.StringType),
    ).to_dict()


class SalesOrdersStream(ZohoBooksStream):
    name = "sales_orders"
    path = "/salesorders"
    primary_keys = ["salesorder_id"]
    replication_key = "last_modified_time"
    records_jsonpath: str = "$.salesorders[*]"
    parent_stream_type = OrganizationIdStream

    schema = th.PropertiesList(
        th.Property("salesorder_id", th.StringType),
        th.Property("documents", th.CustomType({"type": ["array", "string"]})),
        th.Property("line_items", th.CustomType({"type": ["array", "string"]})),
        th.Property("shipment_days", th.StringType),
        th.Property("due_by_days", th.StringType),
        th.Property("due_in_days", th.StringType),
        th.Property("paid_status", th.StringType),
        th.Property("is_pre_gst", th.BooleanType),
        th.Property("gst_no", th.StringType),
        th.Property("total_invoiced_amount", th.CustomType({"type": ["number", "string"]})),
        th.Property("gst_treatment", th.StringType),
        th.Property("place_of_supply", th.StringType),
        th.Property("vat_treatment", th.StringType),
        th.Property("tax_treatment", th.StringType),
        th.Property("zcrm_potential_id", th.StringType),
        th.Property("zcrm_potential_name", th.StringType),
        th.Property("salesorder_number", th.StringType),
        th.Property("date", th.DateType),
        th.Property("delivery_date", th.DateType),
        th.Property("status", th.StringType),
        th.Property("shipment_date", th.StringType),
        th.Property("company_name", th.StringType),
        th.Property("reference_number", th.StringType),
        th.Property("customer_id", th.StringType),
        th.Property("customer_name", th.StringType),
        th.Property("contact_persons", th.CustomType({"type": ["array", "string"]})),
        th.Property("currency_id", th.StringType),
        th.Property("currency_code", th.StringType),
        th.Property("currency_symbol", th.StringType),
        th.Property("exchange_rate", th.CustomType({"type": ["number", "string"]})),
        th.Property("discount_amount", th.CustomType({"type": ["number", "string"]})),
        th.Property("discount", th.CustomType({"type": ["number", "string"]})),
        th.Property("discount_applied_on_amount", th.CustomType({"type": ["number", "string"]})),
        th.Property("is_discount_before_tax", th.BooleanType),
        th.Property("discount_type", th.StringType),
        th.Property("estimate_id", th.StringType),
        th.Property("order_status", th.StringType),
        th.Property("email", th.StringType),
        th.Property("delivery_method", th.StringType),
        th.Property("delivery_method_id", th.StringType),
        th.Property("is_inclusive_tax", th.BooleanType),
        th.Property("shipping_charge", th.CustomType({"type": ["number", "string"]})),
        th.Property("adjustment", th.CustomType({"type": ["number", "string"]})),
        th.Property("adjustment_description", th.StringType),
        th.Property("sub_total", th.CustomType({"type": ["number", "string"]})),
        th.Property("tax_total", th.CustomType({"type": ["number", "string"]})),
        th.Property("total", th.CustomType({"type": ["number", "string"]})),
        th.Property("bcy_total", th.CustomType({"type": ["number", "string"]})),
        th.Property("taxes", th.CustomType({"type": ["array", "string"]})),
        th.Property("price_precision", th.CustomType({"type": ["number", "string"]})),
        th.Property("is_emailed", th.BooleanType),
        th.Property("billing_address", th.CustomType({"type": ["object", "string"]})),
        th.Property("shipping_address", th.CustomType({"type": ["object", "string"]})),
        th.Property("notes", th.StringType),
        th.Property("terms", th.StringType),
        th.Property("custom_fields", th.CustomType({"type": ["array", "string"]})),
        th.Property("template_id", th.StringType),
        th.Property("template_name", th.StringType),
        th.Property("page_width", th.StringType),
        th.Property("page_height", th.StringType),
        th.Property("orientation", th.StringType),
        th.Property("template_type", th.StringType),
        th.Property("created_time", th.DateTimeType),
        th.Property("last_modified_time", th.DateTimeType),
        th.Property("created_by_id", th.StringType),
        th.Property("attachment_name", th.StringType),
        th.Property("can_send_in_mail", th.BooleanType),
        th.Property("has_attachment", th.BooleanType),
        th.Property("salesperson_id", th.StringType),
        th.Property("salesperson_name", th.StringType),
        th.Property("merchant_id", th.StringType),
        th.Property("merchant_name", th.StringType),
    ).to_dict()



    def parse_response(self, response):
        """
        This function works getting all of the data from the Stream
        and adds item details to each item of the stream available.

        It does it using the /salesorders/ details endpoint, chunking with
        100 ids per request.
        """

        if not self.config.get("use_sales_details", False):
            yield from super().parse_response(response)
            return

        # gets organization id from the url
        org_id = response.url.replace(
            self.url_base + "/salesorders?", ""
        ).split("&")[0].replace("organization_id=", "")
        details_base_url = self.url_base + "/salesorders/"
        records = list(extract_jsonpath(self.records_jsonpath, input=response.json()))

        # get all item ids from the records and create a dict with it
        record_ids = OrderedDict((record.get("salesorder_id"), record) for record in records)

        # chunks the request, preserving API quota
        for chunk in self._divide_chunks(list(record_ids.keys())):
            params = {
                "organization_id": org_id,
                "salesorder_ids": ",".join(chunk)
            }
            req = requests.Request(
                "GET",
                details_base_url,
                params=params,
                headers=self.authenticator.auth_headers
            )
            detail_response = self._request(req.prepare())

            sales_details = extract_jsonpath(self.records_jsonpath, input=detail_response.json())

            for sale_detail in sales_details:
                for key in [
                    key for key in sale_detail.keys()
                    if key not in record_ids[sale_detail["salesorder_id"]]
                ]:
                    # Adds data from missing keys
                    record_ids[sale_detail["salesorder_id"]][key] = sale_detail[key]

                yield record_ids[sale_detail["salesorder_id"]]

    def get_child_context(self, record: dict, context: Optional[dict]) -> dict:
        """Return a context dictionary for child streams."""
        return {
            "salesorder_id": record["salesorder_id"],
            "organization_id": context.get("organization_id"),
        }


class SalesOrdersDetailsStream(ZohoBooksStream):
    name = "sales_orders_details"
    path = "/salesorders/{salesorder_id}"
    primary_keys = ["salesorder_id"]
    replication_key = "last_modified_time"
    records_jsonpath: str = "$.salesorder[*]"
    parent_stream_type = SalesOrdersStream
    ignore_parent_replication_key = True

    schema = th.PropertiesList(
        th.Property("salesorder_id", th.StringType),
        th.Property("documents", th.CustomType({"type": ["array", "string"]})),
        th.Property("line_items", th.CustomType({"type": ["array", "string"]})),
        th.Property("shipment_days", th.StringType),
        th.Property("due_by_days", th.StringType),
        th.Property("due_in_days", th.StringType),
        th.Property("paid_status", th.StringType),
        th.Property("is_pre_gst", th.BooleanType),
        th.Property("gst_no", th.StringType),
        th.Property("total_invoiced_amount", th.CustomType({"type": ["number", "string"]})),
        th.Property("gst_treatment", th.StringType),
        th.Property("place_of_supply", th.StringType),
        th.Property("vat_treatment", th.StringType),
        th.Property("tax_treatment", th.StringType),
        th.Property("zcrm_potential_id", th.StringType),
        th.Property("zcrm_potential_name", th.StringType),
        th.Property("salesorder_number", th.StringType),
        th.Property("date", th.DateType),
        th.Property("delivery_date", th.DateType),
        th.Property("status", th.StringType),
        th.Property("shipment_date", th.StringType),
        th.Property("company_name", th.StringType),
        th.Property("reference_number", th.StringType),
        th.Property("customer_id", th.StringType),
        th.Property("customer_name", th.StringType),
        th.Property("contact_persons", th.CustomType({"type": ["array", "string"]})),
        th.Property("currency_id", th.StringType),
        th.Property("currency_code", th.StringType),
        th.Property("currency_symbol", th.StringType),
        th.Property("exchange_rate", th.CustomType({"type": ["number", "string"]})),
        th.Property("discount_amount", th.CustomType({"type": ["number", "string"]})),
        th.Property("discount", th.CustomType({"type": ["number", "string"]})),
        th.Property("discount_applied_on_amount", th.CustomType({"type": ["number", "string"]})),
        th.Property("is_discount_before_tax", th.BooleanType),
        th.Property("discount_type", th.StringType),
        th.Property("estimate_id", th.StringType),
        th.Property("order_status", th.StringType),
        th.Property("email", th.StringType),
        th.Property("delivery_method", th.StringType),
        th.Property("delivery_method_id", th.StringType),
        th.Property("is_inclusive_tax", th.BooleanType),
        th.Property("shipping_charge", th.CustomType({"type": ["number", "string"]})),
        th.Property("adjustment", th.CustomType({"type": ["number", "string"]})),
        th.Property("adjustment_description", th.StringType),
        th.Property("sub_total", th.CustomType({"type": ["number", "string"]})),
        th.Property("tax_total", th.CustomType({"type": ["number", "string"]})),
        th.Property("total", th.CustomType({"type": ["number", "string"]})),
        th.Property("bcy_total", th.CustomType({"type": ["number", "string"]})),
        th.Property("taxes", th.CustomType({"type": ["array", "string"]})),
        th.Property("price_precision", th.CustomType({"type": ["number", "string"]})),
        th.Property("is_emailed", th.BooleanType),
        th.Property("billing_address", th.CustomType({"type": ["object", "string"]})),
        th.Property("shipping_address", th.CustomType({"type": ["object", "string"]})),
        th.Property("notes", th.StringType),
        th.Property("terms", th.StringType),
        th.Property("custom_fields", th.CustomType({"type": ["array", "string"]})),
        th.Property("template_id", th.StringType),
        th.Property("template_name", th.StringType),
        th.Property("page_width", th.StringType),
        th.Property("page_height", th.StringType),
        th.Property("orientation", th.StringType),
        th.Property("template_type", th.StringType),
        th.Property("created_time", th.DateTimeType),
        th.Property("last_modified_time", th.DateTimeType),
        th.Property("created_by_id", th.StringType),
        th.Property("attachment_name", th.StringType),
        th.Property("can_send_in_mail", th.BooleanType),
        th.Property("has_attachment", th.BooleanType),
        th.Property("salesperson_id", th.StringType),
        th.Property("salesperson_name", th.StringType),
        th.Property("merchant_id", th.StringType),
        th.Property("merchant_name", th.StringType),
    ).to_dict()


class PurchaseOrdersStream(ZohoBooksStream):
    name = "purchase_orders"
    path = "/purchaseorders"
    primary_keys = ["purchaseorder_id"]
    replication_key = "last_modified_time"
    records_jsonpath: str = "$.purchaseorders[*]"
    parent_stream_type = OrganizationIdStream

    schema = th.PropertiesList(
        th.Property("purchaseorder_id", th.StringType),
        th.Property("documents", th.CustomType({"type": ["array", "string"]})),
        th.Property("vat_treatment", th.StringType),
        th.Property("gst_no", th.StringType),
        th.Property("gst_treatment", th.StringType),
        th.Property("tax_treatment", th.StringType),
        th.Property("is_pre_gst", th.BooleanType),
        th.Property("source_of_supply", th.StringType),
        th.Property("destination_of_supply", th.StringType),
        th.Property("place_of_supply", th.StringType),
        th.Property("pricebook_id", th.CustomType({"type": ["number", "string"]})),
        th.Property("pricebook_name", th.StringType),
        th.Property("is_reverse_charge_applied", th.BooleanType),
        th.Property("purchaseorder_number", th.StringType),
        th.Property("date", th.DateType),
        th.Property("expected_delivery_date", th.StringType),
        th.Property("discount", th.CustomType({"type": ["number", "string"]})),
        th.Property("discount_account_id", th.StringType),
        th.Property("is_discount_before_tax", th.BooleanType),
        th.Property("reference_number", th.StringType),
        th.Property("status", th.StringType),
        th.Property("vendor_id", th.StringType),
        th.Property("vendor_name", th.StringType),
        th.Property("crm_owner_id", th.StringType),
        th.Property("contact_persons", th.CustomType({"type": ["array", "string"]})),
        th.Property("currency_id", th.StringType),
        th.Property("currency_code", th.StringType),
        th.Property("currency_symbol", th.StringType),
        th.Property("exchange_rate", th.CustomType({"type": ["number", "string"]})),
        th.Property("delivery_date", th.DateType),
        th.Property("is_emailed", th.BooleanType),
        th.Property("is_inclusive_tax", th.BooleanType),
        th.Property("sub_total", th.CustomType({"type": ["number", "string"]})),
        th.Property("tax_total", th.CustomType({"type": ["number", "string"]})),
        th.Property("total", th.CustomType({"type": ["number", "string"]})),
        th.Property("taxes", th.CustomType({"type": ["array", "string"]})),
        th.Property(
            "acquisition_vat_summary", th.CustomType({"type": ["array", "string"]})
        ),
        th.Property(
            "reverse_charge_vat_summary", th.CustomType({"type": ["array", "string"]})
        ),
        th.Property("acquisition_vat_total", th.CustomType({"type": ["number", "string"]})),
        th.Property("reverse_charge_vat_total", th.CustomType({"type": ["number", "string"]})),
        th.Property("billing_address", th.CustomType({"type": ["object", "string"]})),
        th.Property("notes", th.StringType),
        th.Property("terms", th.StringType),
        th.Property("ship_via", th.StringType),
        th.Property("ship_via_id", th.StringType),
        th.Property("attention", th.StringType),
        th.Property("delivery_org_address_id", th.StringType),
        th.Property("delivery_customer_id", th.StringType),
        th.Property("delivery_address", th.CustomType({"type": ["object", "string"]})),
        th.Property("price_precision", th.CustomType({"type": ["number", "string"]})),
        th.Property("custom_fields", th.CustomType({"type": ["array", "string"]})),
        th.Property("attachment_name", th.StringType),
        th.Property("can_send_in_mail", th.BooleanType),
        th.Property("template_id", th.StringType),
        th.Property("template_name", th.StringType),
        th.Property("page_width", th.StringType),
        th.Property("page_height", th.StringType),
        th.Property("orientation", th.StringType),
        th.Property("template_type", th.StringType),
        th.Property("created_time", th.DateTimeType),
        th.Property("created_by_id", th.StringType),
        th.Property("last_modified_time", th.DateTimeType),
        th.Property("can_mark_as_bill", th.BooleanType),
        th.Property("can_mark_as_unbill", th.BooleanType),
    ).to_dict()

    def get_child_context(self, record: dict, context: Optional[dict]) -> dict:
        """Return a context dictionary for child streams."""
        return {
            "purchaseorder_id": record["purchaseorder_id"],
            "organization_id": context.get("organization_id"),
        }


class PurchaseOrderDetailsStream(ZohoBooksStream):
    name = "purchase_orders_details"
    path = "/purchaseorders/{purchaseorder_id}"
    primary_keys = ["purchaseorder_id"]
    replication_key = "last_modified_time"
    records_jsonpath: str = "$.purchaseorder[*]"
    parent_stream_type = PurchaseOrdersStream
    ignore_parent_replication_key = True

    schema = th.PropertiesList(
        th.Property("purchaseorder_id", th.StringType),
        th.Property("documents", th.CustomType({"type": ["array", "string"]})),
        th.Property("line_items", th.CustomType({"type": ["array", "string"]})),
        th.Property("vat_treatment", th.StringType),
        th.Property("gst_no", th.StringType),
        th.Property("gst_treatment", th.StringType),
        th.Property("color_code", th.StringType),
        th.Property("order_status", th.StringType),
        th.Property("current_sub_status_id", th.StringType),
        th.Property("current_sub_status", th.StringType),
        th.Property("pickup_location_id", th.StringType),
        th.Property("source", th.StringType),
        th.Property("tax_treatment", th.StringType),
        th.Property("is_pre_gst", th.BooleanType),
        th.Property("source_of_supply", th.StringType),
        th.Property("destination_of_supply", th.StringType),
        th.Property("place_of_supply", th.StringType),
        th.Property("pricebook_id", th.CustomType({"type": ["number", "string"]})),
        th.Property("pricebook_name", th.StringType),
        th.Property("is_reverse_charge_applied", th.BooleanType),
        th.Property("purchaseorder_number", th.StringType),
        th.Property("date", th.DateType),
        th.Property("expected_delivery_date", th.StringType),
        th.Property("discount", th.CustomType({"type": ["number", "string"]})),
        th.Property("discount_account_id", th.StringType),
        th.Property("is_discount_before_tax", th.BooleanType),
        th.Property("reference_number", th.StringType),
        th.Property("status", th.StringType),
        th.Property("vendor_id", th.StringType),
        th.Property("vendor_name", th.StringType),
        th.Property("crm_owner_id", th.StringType),
        th.Property("contact_persons", th.CustomType({"type": ["array", "string"]})),
        th.Property("currency_id", th.StringType),
        th.Property("currency_code", th.StringType),
        th.Property("currency_symbol", th.StringType),
        th.Property("exchange_rate", th.CustomType({"type": ["number", "string"]})),
        th.Property("delivery_date", th.DateType),
        th.Property("is_emailed", th.BooleanType),
        th.Property("is_inclusive_tax", th.BooleanType),
        th.Property("sub_total", th.CustomType({"type": ["number", "string"]})),
        th.Property("tax_total", th.CustomType({"type": ["number", "string"]})),
        th.Property("total_invoiced_amount", th.CustomType({"type": ["number", "string"]})),
        th.Property("total", th.CustomType({"type": ["number", "string"]})),
        th.Property("taxes", th.CustomType({"type": ["array", "string"]})),
        th.Property(
            "acquisition_vat_summary", th.CustomType({"type": ["array", "string"]})
        ),
        th.Property(
            "reverse_charge_vat_summary", th.CustomType({"type": ["array", "string"]})
        ),
        th.Property("acquisition_vat_total", th.CustomType({"type": ["number", "string"]})),
        th.Property("reverse_charge_vat_total", th.CustomType({"type": ["number", "string"]})),
        th.Property("billing_address", th.CustomType({"type": ["object", "string"]})),
        th.Property("notes", th.StringType),
        th.Property("terms", th.StringType),
        th.Property("ship_via", th.StringType),
        th.Property("ship_via_id", th.StringType),
        th.Property("attention", th.StringType),
        th.Property("delivery_org_address_id", th.StringType),
        th.Property("delivery_customer_id", th.StringType),
        th.Property("delivery_address", th.CustomType({"type": ["object", "string"]})),
        th.Property("price_precision", th.CustomType({"type": ["number", "string"]})),
        th.Property("custom_fields", th.CustomType({"type": ["array", "string"]})),
        th.Property("attachment_name", th.StringType),
        th.Property("can_send_in_mail", th.BooleanType),
        th.Property("template_id", th.StringType),
        th.Property("template_name", th.StringType),
        th.Property("page_width", th.StringType),
        th.Property("page_height", th.StringType),
        th.Property("orientation", th.StringType),
        th.Property("template_type", th.StringType),
        th.Property("created_time", th.DateTimeType),
        th.Property("created_by_id", th.StringType),
        th.Property("last_modified_time", th.DateTimeType),
        th.Property("can_mark_as_bill", th.BooleanType),
        th.Property("can_mark_as_unbill", th.BooleanType),
    ).to_dict()


class VendorsStream(ZohoBooksStream):
    name = "vendors"
    path = "/vendors"
    primary_keys = ["purchaseorder_id"]
    replication_key = "last_modified_time"
    records_jsonpath: str = "$.contacts[*]"
    parent_stream_type = OrganizationIdStream

    schema = th.PropertiesList(
        th.Property("contact_id", th.StringType),
        th.Property("vendor_id", th.StringType),
        th.Property("contact_name", th.StringType),
        th.Property("vendor_name", th.StringType),
        th.Property("company_name", th.StringType),
        th.Property("website", th.StringType),
        th.Property("language_code", th.StringType),
        th.Property("language_code_formatted", th.StringType),
        th.Property("contact_type", th.StringType),
        th.Property("contact_type_formatted", th.StringType),
        th.Property("status", th.StringType),
        th.Property("customer_sub_type", th.StringType),
        th.Property("source", th.StringType),
        th.Property("is_linked_with_zohocrm", th.BooleanType),
        th.Property("payment_terms", th.IntegerType),
        th.Property("payment_terms_label", th.StringType),
        th.Property("currency_id", th.StringType),
        th.Property("twitter", th.StringType),
        th.Property("facebook", th.StringType),
        th.Property("currency_code", th.StringType),
        th.Property("outstanding_payable_amount", th.CustomType({"type": ["number", "string"]})),
        th.Property("outstanding_payable_amount_bcy", th.CustomType({"type": ["number", "string"]})),
        th.Property("unused_credits_payable_amount", th.CustomType({"type": ["number", "string"]})),
        th.Property("unused_credits_payable_amount_bcy", th.CustomType({"type": ["number", "string"]})),
        th.Property("first_name", th.StringType),
        th.Property("last_name", th.StringType),
        th.Property("email", th.StringType),
        th.Property("phone", th.StringType),
        th.Property("mobile", th.StringType),
        th.Property("portal_status", th.StringType),
        th.Property("created_time", th.DateTimeType),
        th.Property("created_time_formatted", th.DateTimeType),
        th.Property("last_modified_time", th.DateTimeType),
        th.Property("last_modified_time_formatted", th.DateTimeType),
        th.Property("custom_fields", th.ArrayType(th.CustomType({"type": ["object", "string"]}))),
        th.Property("custom_field_hash", th.CustomType({"type": ["object", "string"]})),
        th.Property("ach_supported", th.BooleanType),
        th.Property("has_attachment", th.BooleanType),
    ).to_dict()