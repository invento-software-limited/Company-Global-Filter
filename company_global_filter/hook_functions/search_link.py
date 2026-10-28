import frappe
from frappe import _
from frappe.desk.search import search_link as frappe_search_link

from company_global_filter.hook_functions.global_company_filter import (
	get_ignored_doctypes,
	get_user_company,
	is_filter_enabled,
	treat_empty_company_as_global,
	get_allowed_companies,
)


def get_target_search_link(doctype):
	"""
	Delegate to global_tree_view.api.tree_search.search_link if installed and doctype is a tree,
	otherwise fallback to standard frappe.desk.search.search_link.
	"""
	try:
		if doctype:
			meta = frappe.get_meta(doctype)
			if getattr(meta, "is_tree", False):
				from global_tree_view.api.tree_search import search_link as tree_search_link
				return tree_search_link
	except Exception:
		pass
	return frappe_search_link


def get_clean_kwargs(func, kwargs):
	import inspect

	try:
		sig = inspect.signature(func)
		return {k: v for k, v in kwargs.items() if k in sig.parameters}
	except Exception:
		allowed = {"link_fieldname", "start"}
		return {k: v for k, v in kwargs.items() if k in allowed}


@frappe.whitelist()
def search_link(
	doctype: str | None = None,
	txt: str | None = None,
	query: str | None = None,
	filters: dict | list | str | None = None,
	page_length: int | None = 20,
	searchfield: str | None = None,
	reference_doctype: str | None = None,
	ignore_user_permissions: bool | None = False,
	*args,
	**kwargs,
):
	"""
	Extended search_link method that applies company filtering and supports tree view.
	"""
	target_search = frappe_search_link
	try:
		# Use passed parameters if available, otherwise get from form_dict
		doctype = doctype or frappe.form_dict.get("doctype")
		txt = txt if txt is not None else frappe.form_dict.get("txt", "")
		txt = txt or ""
		query = query or frappe.form_dict.get("query")

		# Robust filter parsing: ensure filters is always a dict or list
		raw_filters = filters if filters is not None else frappe.form_dict.get("filters")
		if isinstance(raw_filters, str):
			try:
				filters = frappe.parse_json(raw_filters)
			except Exception:
				filters = {}
		elif isinstance(raw_filters, (dict, list)):
			filters = raw_filters
		else:
			filters = {}

		if filters is None:
			filters = {}

		page_length = page_length or frappe.form_dict.get("page_length", 20)
		searchfield = searchfield or frappe.form_dict.get("searchfield")
		reference_doctype = reference_doctype or frappe.form_dict.get("reference_doctype")
		ignore_user_permissions = ignore_user_permissions or frappe.form_dict.get("ignore_user_permissions")
		ignore_user_permissions = str(ignore_user_permissions).lower() in ["1", "true", "yes"]

		# Determine target search function (tree search or core frappe)
		target_search = get_target_search_link(doctype)

		# Check if filter is enabled
		if not is_filter_enabled():
			return target_search(
				doctype=doctype,
				txt=txt,
				query=query,
				filters=filters,
				page_length=page_length,
				searchfield=searchfield,
				reference_doctype=reference_doctype,
				ignore_user_permissions=ignore_user_permissions,
				**get_clean_kwargs(target_search, kwargs),
			)

		# Skip company filtering for ignored doctypes
		if doctype in get_ignored_doctypes():
			return target_search(
				doctype=doctype,
				txt=txt,
				query=query,
				filters=filters,
				page_length=page_length,
				searchfield=searchfield,
				reference_doctype=reference_doctype,
				ignore_user_permissions=ignore_user_permissions,
				**get_clean_kwargs(target_search, kwargs),
			)

		# Get user's company
		user_company = get_user_company()
		if not user_company:
			return target_search(
				doctype=doctype,
				txt=txt,
				query=query,
				filters=filters,
				page_length=page_length,
				searchfield=searchfield,
				reference_doctype=reference_doctype,
				ignore_user_permissions=ignore_user_permissions,
				**get_clean_kwargs(target_search, kwargs),
			)

		# Check if doctype has company or custom_company field
		meta = frappe.get_meta(doctype)
		has_company_field = meta.get_field("company") is not None
		has_custom_company_field = meta.get_field("custom_company") is not None

		# If neither company field exists, return target search directly
		if not has_company_field and not has_custom_company_field:
			return target_search(
				doctype=doctype,
				txt=txt,
				query=query,
				filters=filters,
				page_length=page_length,
				searchfield=searchfield,
				reference_doctype=reference_doctype,
				ignore_user_permissions=ignore_user_permissions,
				**get_clean_kwargs(target_search, kwargs),
			)

		# Add company filter based on which field exists and Treat Empty Company as Global setting
		allowed_companies = get_allowed_companies(user_company)
		if treat_empty_company_as_global():
			company_val = ["in", allowed_companies + ["", None]]
		else:
			if len(allowed_companies) == 1:
				company_val = allowed_companies[0]
			else:
				company_val = ["in", allowed_companies]

		if isinstance(filters, list):
			has_existing_company_filter = any(
				isinstance(f, (list, tuple))
				and len(f) > 1
				and (
					(len(f) >= 3 and f[1] in ("company", "custom_company"))
					or f[0] in ("company", "custom_company")
				)
				for f in filters
			)
			if not has_existing_company_filter:
				if has_company_field:
					filters.append(
						[
							"company",
							"in",
							allowed_companies + ["", None] if treat_empty_company_as_global() else allowed_companies,
						]
					)
				elif has_custom_company_field:
					filters.append(
						[
							"custom_company",
							"in",
							allowed_companies + ["", None] if treat_empty_company_as_global() else allowed_companies,
						]
					)
		else:
			if has_company_field:
				if "company" not in filters:
					filters["company"] = company_val
				elif isinstance(filters["company"], str) and filters["company"] not in allowed_companies:
					filters["company"] = company_val
			elif has_custom_company_field:
				if "custom_company" not in filters:
					filters["custom_company"] = company_val
				elif isinstance(filters["custom_company"], str) and filters["custom_company"] not in allowed_companies:
					filters["custom_company"] = company_val

		# Update form_dict filters for consistency
		frappe.form_dict["filters"] = frappe.as_json(filters)

		return target_search(
			doctype=doctype,
			txt=txt,
			query=query,
			filters=filters,
			page_length=page_length,
			searchfield=searchfield,
			reference_doctype=reference_doctype,
			ignore_user_permissions=ignore_user_permissions,
			**get_clean_kwargs(target_search, kwargs),
		)
	except Exception:
		frappe.log_error(message=frappe.get_traceback(), title="Search Link Error")
		return target_search(
			doctype=doctype,
			txt=txt or "",
			query=query,
			filters=raw_filters if raw_filters is not None else (filters or {}),
			page_length=page_length or 20,
			searchfield=searchfield,
			reference_doctype=reference_doctype,
			ignore_user_permissions=ignore_user_permissions,
			**get_clean_kwargs(target_search, kwargs),
		)
