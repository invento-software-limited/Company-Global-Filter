import frappe
from frappe import _
from frappe.desk.search import search_link as frappe_search_link

from company_global_filter.hook_functions.global_company_filter import (
	get_user_company,
	is_filter_enabled,
	treat_empty_company_as_global,
	get_ignored_doctypes,
)


def get_clean_kwargs(kwargs):
	import inspect
	try:
		sig = inspect.signature(frappe_search_link)
		# Only keep keyword arguments that are accepted by frappe_search_link
		return {k: v for k, v in kwargs.items() if k in sig.parameters}
	except Exception:
		# Fallback to only allowing known extra parameters like link_fieldname
		allowed = {"link_fieldname"}
		return {k: v for k, v in kwargs.items() if k in allowed}


@frappe.whitelist()
def search_link(
	doctype=None,
	txt=None,
	query=None,
	filters=None,
	page_length=20,
	searchfield=None,
	reference_doctype=None,
	ignore_user_permissions=False,
	*args,
	**kwargs
):
	"""
	Extended search_link method that applies company filtering
	"""
	try:
		# Get search parameters first
		# frappe.log_error("search_link called", "Search Link Debug")

		# Use passed parameters if available, otherwise get from form_dict
		doctype = doctype or frappe.form_dict.get("doctype")
		txt = txt or frappe.form_dict.get("txt")
		query = query or frappe.form_dict.get("query")
		filters = filters or frappe.parse_json(frappe.form_dict.get("filters") or "{}")
		page_length = page_length or frappe.form_dict.get("page_length", 20)
		searchfield = searchfield or frappe.form_dict.get("searchfield")
		reference_doctype = reference_doctype or frappe.form_dict.get("reference_doctype")
		ignore_user_permissions = ignore_user_permissions or frappe.form_dict.get("ignore_user_permissions")
		ignore_user_permissions = str(ignore_user_permissions).lower() in ["1", "true", "yes"]

		# frappe.log_error(f"Parameters - doctype: {doctype}, txt: {txt}, filters: {filters}", "Search Link Debug")

		# Check if filter is enabled
		if not is_filter_enabled():
			return frappe_search_link(
				doctype=doctype,
				txt=txt,
				query=query,
				filters=filters,
				page_length=page_length,
				searchfield=searchfield,
				reference_doctype=reference_doctype,
				ignore_user_permissions=ignore_user_permissions,
				**get_clean_kwargs(kwargs)
			)

		# Skip company filtering for ignored doctypes
		if doctype in get_ignored_doctypes():
			return frappe_search_link(
				doctype=doctype,
				txt=txt,
				query=query,
				filters=filters,
				page_length=page_length,
				searchfield=searchfield,
				reference_doctype=reference_doctype,
				ignore_user_permissions=ignore_user_permissions,
				**get_clean_kwargs(kwargs)
			)

		# Get user's company
		user_company = get_user_company()
		if not user_company:
			return frappe_search_link(
				doctype=doctype,
				txt=txt,
				query=query,
				filters=filters,
				page_length=page_length,
				searchfield=searchfield,
				reference_doctype=reference_doctype,
				ignore_user_permissions=ignore_user_permissions,
				**get_clean_kwargs(kwargs)
			)

		# Check if doctype has company or custom_company field
		meta = frappe.get_meta(doctype)
		has_company_field = meta.get_field("company") is not None
		has_custom_company_field = meta.get_field("custom_company") is not None

		# If neither company field exists, return original search
		if not has_company_field and not has_custom_company_field:
			return frappe_search_link(
				doctype=doctype,
				txt=txt,
				query=query,
				filters=filters,
				page_length=page_length,
				searchfield=searchfield,
				reference_doctype=reference_doctype,
				ignore_user_permissions=ignore_user_permissions,
				**get_clean_kwargs(kwargs)
			)

		# Initialize filters if not exists
		if not filters:
			filters = {}

		# Add company filter based on which field exists and Treat Empty Company as Global setting
		if treat_empty_company_as_global():
			company_val = ["in", [user_company, "", None]]
		else:
			company_val = user_company

		if isinstance(filters, list):
			if has_company_field:
				filters.append(["company", "in" if treat_empty_company_as_global() else "=", [user_company, "", None] if treat_empty_company_as_global() else user_company])
			elif has_custom_company_field:
				filters.append(["custom_company", "in" if treat_empty_company_as_global() else "=", [user_company, "", None] if treat_empty_company_as_global() else user_company])
		else:
			if has_company_field:
				filters["company"] = company_val
			elif has_custom_company_field:
				filters["custom_company"] = company_val

		# Update form_dict filters for consistency
		frappe.form_dict["filters"] = frappe.as_json(filters)

		return frappe_search_link(
			doctype=doctype,
			txt=txt,
			query=query,
			filters=filters,
			page_length=page_length,
			searchfield=searchfield,
			reference_doctype=reference_doctype,
			ignore_user_permissions=ignore_user_permissions,
			**get_clean_kwargs(kwargs)
		)
	except Exception:
		frappe.log_error("Error in search_link", "Search Link Error")
		return frappe_search_link(
			doctype=doctype,
			txt=txt,
			query=query,
			filters=filters,
			page_length=page_length,
			searchfield=searchfield,
			reference_doctype=reference_doctype,
			ignore_user_permissions=ignore_user_permissions,
			**get_clean_kwargs(kwargs)
		)
