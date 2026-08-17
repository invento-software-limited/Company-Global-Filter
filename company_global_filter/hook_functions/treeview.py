import frappe

@frappe.whitelist()
def get_department_children(doctype, parent=None, company=None, is_root=False, include_disabled=False):
	from company_global_filter.hook_functions.global_company_filter import (
		is_filter_enabled,
		get_user_company,
		get_allowed_companies,
		treat_empty_company_as_global,
	)
	import json
	from frappe.utils.nestedset import get_root_of

	if isinstance(include_disabled, str):
		include_disabled = json.loads(include_disabled)

	fields = ["name as value", "is_group as expandable"]
	filters = {}

	# Get allowed companies if filter is enabled
	if is_filter_enabled():
		user_company = company or get_user_company()
		allowed_companies = get_allowed_companies(user_company) if user_company else []
		if allowed_companies and treat_empty_company_as_global():
			allowed_companies = list(allowed_companies) + [None, ""]
	else:
		allowed_companies = [company] if company else []

	if company == parent:
		filters["name"] = get_root_of("Department")
	else:
		filters["parent_department"] = parent
		if allowed_companies:
			filters["company"] = ["in", allowed_companies]
		elif company:
			filters["company"] = company

	if frappe.db.has_column(doctype, "disabled") and not include_disabled:
		filters["disabled"] = False

	return frappe.get_all("Department", fields=fields, filters=filters, order_by="name")


@frappe.whitelist()
def get_account_children(doctype, parent, company, is_root=False, include_disabled=False):
	from company_global_filter.hook_functions.global_company_filter import (
		is_filter_enabled,
		get_user_company,
		get_allowed_companies,
		treat_empty_company_as_global,
	)
	from json import loads
	from erpnext.accounts.report.financial_statements import sort_accounts
	from frappe.query_builder import Field
	from frappe.query_builder.functions import IfNull

	if isinstance(include_disabled, str):
		include_disabled = loads(include_disabled)
	if isinstance(is_root, str):
		is_root = loads(is_root)

	parent_fieldname = "parent_" + doctype.lower().replace(" ", "_")
	fields = ["name as value", "is_group as expandable"]
	filters = [["docstatus", "<", 2]]
	if frappe.db.has_column(doctype, "disabled") and not include_disabled:
		filters.append(["disabled", "=", False])

	if is_root:
		filters.append(IfNull(Field(parent_fieldname), "") == "")
	else:
		filters.append([parent_fieldname, "=", parent])

	# Get allowed companies
	if is_filter_enabled():
		user_company = company or get_user_company()
		allowed_companies = get_allowed_companies(user_company) if user_company else []
		if allowed_companies and treat_empty_company_as_global():
			allowed_companies = list(allowed_companies) + [None, ""]
	else:
		allowed_companies = [company] if company else []

	if is_root:
		fields += ["root_type", "report_type", "account_currency"] if doctype == "Account" else []
		if allowed_companies:
			filters.append(["company", "in", allowed_companies])
		else:
			filters.append(["company", "=", company])
	else:
		fields += ["root_type", "account_currency"] if doctype == "Account" else []
		fields += [parent_fieldname + " as parent"]
		if allowed_companies:
			filters.append(["company", "in", allowed_companies])
		elif company:
			filters.append(["company", "=", company])

	acc = frappe.get_list(doctype, fields=fields, filters=filters)

	if doctype == "Account":
		sort_accounts(acc, is_root, key="value")

	return acc


@frappe.whitelist()
def get_warehouse_children(doctype, parent=None, company=None, is_root=False, include_disabled=False):
	from company_global_filter.hook_functions.global_company_filter import (
		is_filter_enabled,
		get_user_company,
		get_allowed_companies,
		treat_empty_company_as_global,
	)
	import json
	from frappe.query_builder import Field
	from frappe.query_builder.functions import IfNull

	if is_root:
		parent = ""

	if isinstance(include_disabled, str):
		include_disabled = json.loads(include_disabled)

	fields = ["name as value", "is_group as expandable"]

	# Get allowed companies
	if is_filter_enabled():
		user_company = company or get_user_company()
		allowed_companies = get_allowed_companies(user_company) if user_company else []
		if allowed_companies and treat_empty_company_as_global():
			allowed_companies = list(allowed_companies) + [None, ""]
	else:
		allowed_companies = [company] if company else []

	if allowed_companies:
		allowed_companies_with_empty = list(allowed_companies)
		if None not in allowed_companies_with_empty:
			allowed_companies_with_empty.append(None)
		if "" not in allowed_companies_with_empty:
			allowed_companies_with_empty.append("")
		filters = [
			[IfNull(Field("parent_warehouse"), ""), "=", parent],
			["company", "in", allowed_companies_with_empty],
		]
	else:
		filters = [
			[IfNull(Field("parent_warehouse"), ""), "=", parent],
			["company", "in", (company, None, "")],
		]

	if frappe.db.has_column(doctype, "disabled") and not include_disabled:
		filters.append(["disabled", "=", False])

	return frappe.get_list(doctype, fields=fields, filters=filters, order_by="name")
