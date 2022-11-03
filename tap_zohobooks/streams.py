"""Stream type classes for tap-zohobooks."""

from typing import Optional

from singer_sdk import typing as th  # JSON Schema typing helpers

from tap_zohobooks.client import ZohoBooksStream


class OrganizationIdStream(ZohoBooksStream):
    name = "organization_id"
    path = "/organizations"
    primary_keys = ["organization_id"]
    replication_key = None
    records_jsonpath = "$.organizations[*]"

    schema = th.PropertiesList(
        th.Property("organization_id", th.StringType),
    ).to_dict()

    def get_child_context(self, record: dict, context: Optional[dict]) -> dict:
        """Return a context dictionary for child streams."""
        return {
            "organization_id": record["organization_id"],
        }


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
        th.Property("total", th.NumberType),
        th.Property("bcy_total", th.NumberType),
        th.Property("created_by_id", th.StringType),
        th.Property("created_by_name", th.StringType),
        th.Property("documents", th.CustomType({"type": ["array", "string"]})),
    ).to_dict()

    def get_child_context(self, record: dict, context: Optional[dict]) -> dict:
        """Return a context dictionary for child streams."""
        return {
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
        th.Property("amount", th.NumberType),
        th.Property("bcy_amount", th.NumberType),
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
        th.Property("exchange_rate", th.NumberType),
        th.Property("journal_date", th.StringType),
        th.Property("journal_type", th.StringType),
        th.Property("vat_treatment", th.StringType),
        th.Property("product_type", th.StringType),
        th.Property("include_in_vat_return", th.BooleanType),
        th.Property("is_bas_adjustment", th.BooleanType),
        th.Property("line_items", th.ArrayType(line_object_schema)),
        th.Property("line_item_total", th.NumberType),
        th.Property("total", th.NumberType),
        th.Property("bcy_total", th.NumberType),
        th.Property("price_precision", th.IntegerType),
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
        th.Property("created_time", th.StringType),
        th.Property("last_modified_time", th.StringType),
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
        th.Property("child_count", th.StringType),
        th.Property("documents", th.ArrayType(th.StringType)),
        th.Property("created_time", th.StringType),
        th.Property("last_modified_time", th.StringType),
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
        th.Property("zcrm_potential_id", th.StringType),
        th.Property("zcrm_potential_name", th.StringType),
        th.Property("customer_name", th.StringType),
        th.Property("customer_id", th.StringType),
        th.Property("status", th.StringType),
        th.Property("salesorder_number", th.StringType),
        th.Property("reference_number", th.StringType),
        th.Property("date", th.StringType),
        th.Property("shipment_date", th.StringType),
        th.Property("shipment_days", th.IntegerType),
        th.Property("currency_id", th.StringType),
        th.Property("currency_code", th.StringType),
        th.Property("total", th.NumberType),
        th.Property("sub_total", th.IntegerType),
        th.Property("bcy_total", th.NumberType),
        th.Property("created_time", th.StringType),
        th.Property("last_modified_time", th.StringType),
        th.Property("is_emailed", th.BooleanType),
        th.Property("has_attachment", th.BooleanType),
        th.Property(
            "custom_fields",
            th.ArrayType(
                th.ObjectType(
                    th.Property("customfield_id", th.StringType),
                    th.Property("index", th.IntegerType),
                    th.Property("value", th.StringType),
                    th.Property("label", th.StringType),
                )
            ),
        ),
    ).to_dict()


class ItemsStream(ZohoBooksStream):
    name = "items"
    path = "/items"
    primary_keys = ["item_id"]
    replication_key = "last_modified_time"
    records_jsonpath: str = "$.items[*]"
    parent_stream_type = OrganizationIdStream

    schema = th.PropertiesList(
        th.Property("item_id", th.StringType),
        th.Property("name", th.StringType),
        th.Property("item_name", th.StringType),
        th.Property("unit", th.StringType),
        th.Property("status", th.StringType),
        th.Property("source", th.StringType),
        th.Property("is_linked_with_zohocrm", th.BooleanType),
        th.Property("zcrm_product_id", th.StringType),
        th.Property("description", th.StringType),
        th.Property("rate", th.NumberType),
        th.Property("tax_id", th.StringType),
        th.Property("tax_name", th.StringType),
        th.Property("tax_percentage", th.IntegerType),
        th.Property("purchase_account_id", th.StringType),
        th.Property("purchase_account_name", th.StringType),
        th.Property("account_id", th.StringType),
        th.Property("account_name", th.StringType),
        th.Property("purchase_description", th.StringType),
        th.Property("purchase_rate", th.NumberType),
        th.Property("item_type", th.StringType),
        th.Property("product_type", th.StringType),
        th.Property("has_attachment", th.BooleanType),
        th.Property("sku", th.StringType),
        th.Property("image_name", th.StringType),
        th.Property("image_type", th.StringType),
        th.Property("image_document_id", th.StringType),
        th.Property("created_time", th.StringType),
        th.Property("last_modified_time", th.StringType),
        th.Property("show_in_storefront", th.BooleanType),
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
        th.Property("total", th.NumberType),
        th.Property("balance", th.NumberType),
        th.Property("created_time", th.StringType),
        th.Property("last_modified_time", th.StringType),
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
        th.Property("shipping_charge", th.NumberType),
        th.Property("adjustment", th.NumberType),
        th.Property("write_off_amount", th.NumberType),
        th.Property("exchange_rate", th.NumberType),
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
        th.Property("outstanding_receivable_amount", th.NumberType),
        th.Property("outstanding_receivable_amount_bcy", th.NumberType),
        th.Property("outstanding_payable_amount", th.NumberType),
        th.Property("outstanding_payable_amount_bcy", th.NumberType),
        th.Property("unused_credits_receivable_amount", th.NumberType),
        th.Property("unused_credits_receivable_amount_bcy", th.NumberType),
        th.Property("unused_credits_payable_amount", th.NumberType),
        th.Property("unused_credits_payable_amount_bcy", th.NumberType),
        th.Property("first_name", th.StringType),
        th.Property("last_name", th.StringType),
        th.Property("email", th.StringType),
        th.Property("phone", th.StringType),
        th.Property("mobile", th.StringType),
        th.Property("portal_status", th.StringType),
        th.Property("track_1099", th.BooleanType),
        th.Property("created_time", th.StringType),
        th.Property("created_time_formatted", th.StringType),
        th.Property("last_modified_time", th.StringType),
        th.Property("last_modified_time_formatted", th.StringType),
        th.Property("custom_fields", th.CustomType({"type": ["array", "string"]})),
        th.Property("custom_field_hash", th.CustomType({"type": ["array", "object"]})),
        th.Property("ach_supported", th.BooleanType),
        th.Property("has_attachment", th.BooleanType),
    ).to_dict()
