import frappe
from frappe import _
from frappe.desk.form.load import getdoc as frappe_getdoc

from company_global_filter.hook_functions.global_company_filter import get_user_company


@frappe.whitelist()
def getdoc(doctype, name, user=None, for_edit=False):
	"""
	Extended getdoc method that applies company filtering
	"""
	try:
		# Get user's company
		user_company = get_user_company()

		# If no user company, proceed with original getdoc
		if not user_company:
			return frappe_getdoc(doctype, name)

		# Skip company filtering for these doctypes
		ignore_tables = ["Company", "User", "Module Def"]
		if doctype in ignore_tables:
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

		# If document company doesn't match user company, raise permission error
		if doc_company and doc_company != user_company:
			frappe.throw(
				_("You don't have permission to access this {0}").format(doctype), frappe.PermissionError
			)

			# If company matches or document has no company, proceed with original getdoc
		return frappe_getdoc(doctype, name)

	except frappe.PermissionError:
		# Re-raise permission errors
		raise
	except Exception:
		frappe.log_error("Error in getdoc", "GetDoc Error")
		# Fallback to original getdoc on any other error
		return frappe_getdoc(doctype, name)
