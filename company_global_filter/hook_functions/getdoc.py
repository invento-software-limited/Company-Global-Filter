import frappe
from frappe import _
from frappe.desk.form.load import getdoc as frappe_getdoc

from company_global_filter.hook_functions.global_company_filter import (
	get_ignored_doctypes,
	get_user_company,
	is_filter_enabled,
	treat_empty_company_as_global,
)


@frappe.whitelist()
def getdoc(
	doctype: str,
	name: str,
	user: str | None = None,
	for_edit: bool = False,
	*args,
	**kwargs,
):
	"""
	Extended getdoc method that applies company filtering
	"""
	try:
		# Check if filter is enabled
		if not is_filter_enabled():
			return frappe_getdoc(doctype, name)

		# Skip company filtering for ignored doctypes
		if doctype in get_ignored_doctypes():
			return frappe_getdoc(doctype, name)

		# Get user's company
		user_company = get_user_company()

		# If no user company, proceed with original getdoc
		if not user_company:
			return frappe_getdoc(doctype, name)

		# Check if doctype has company or custom_company field
		meta = frappe.get_meta(doctype)
		has_company_field = meta.get_field("company") is not None
		has_custom_company_field = meta.get_field("custom_company") is not None

		# If neither company field exists, proceed with original getdoc
		if not has_company_field and not has_custom_company_field:
			return frappe_getdoc(doctype, name)

		# Get the document
		doc = frappe.get_doc(doctype, name)

		# Check company field
		doc_company = None
		if has_company_field:
			doc_company = doc.get("company")
		elif has_custom_company_field:
			doc_company = doc.get("custom_company")

		# Check if access is allowed
		is_allowed = False
		if not doc_company:
			if treat_empty_company_as_global():
				is_allowed = True
		else:
			if doc_company == user_company:
				is_allowed = True

		if not is_allowed:
			frappe.throw(
				_("You don't have permission to access this {0}").format(doctype), frappe.PermissionError
			)

		return frappe_getdoc(doctype, name)

	except frappe.PermissionError:
		# Re-raise permission errors
		raise
	except Exception:
		frappe.log_error("Error in getdoc", "GetDoc Error")
		# Fallback to original getdoc on any other error
		return frappe_getdoc(doctype, name)
