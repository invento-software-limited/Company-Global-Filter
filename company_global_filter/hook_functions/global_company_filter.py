import frappe
from frappe import _
from frappe.desk.search import search_link


@frappe.whitelist()
def get_company_list():
	companies = search_link(txt="", doctype="Company", reference_doctype="", page_length=100000)
	company_names = [c.get("value") for c in companies]
	return company_names


from frappe.utils import cint

def get_ignored_doctypes():
	if not hasattr(frappe.local, "global_company_filter_ignored_doctypes"):
		ignored = []
		try:
			# Only attempt to read from database if the table/doctype exists
			if hasattr(frappe, "db") and frappe.db and frappe.db.exists("DocType", "Global Company Filter Setting"):
				db_ignored = frappe.get_all(
					"Global Company Filter Ignore Doctype",
					fields=["doctype_to_ignore"],
					pluck="doctype_to_ignore"
				)
				if db_ignored:
					ignored = [d for d in db_ignored if d]
		except Exception:
			pass
		frappe.local.global_company_filter_ignored_doctypes = ignored
	return frappe.local.global_company_filter_ignored_doctypes


def is_filter_enabled():
	if not hasattr(frappe.local, "global_company_filter_enabled"):
		enabled = True
		try:
			if hasattr(frappe, "db") and frappe.db and frappe.db.exists("DocType", "Global Company Filter Setting"):
				val = frappe.db.get_single_value("Global Company Filter Setting", "enabled")
				if val is not None:
					enabled = bool(cint(val))
		except Exception:
			pass
		frappe.local.global_company_filter_enabled = enabled
	return frappe.local.global_company_filter_enabled


def treat_empty_company_as_global():
	if not hasattr(frappe.local, "global_company_filter_treat_empty_as_global"):
		treat_empty = False
		try:
			if hasattr(frappe, "db") and frappe.db and frappe.db.exists("DocType", "Global Company Filter Setting"):
				val = frappe.db.get_single_value("Global Company Filter Setting", "treat_empty_company_as_global")
				if val is not None:
					treat_empty = bool(cint(val))
		except Exception:
			pass
		frappe.local.global_company_filter_treat_empty_as_global = treat_empty
	return frappe.local.global_company_filter_treat_empty_as_global


def preload_ignore_doctypes():
	"""Preload standard system doctypes into Global Company Filter Setting if empty"""
	try:
		if not hasattr(frappe, "db") or not frappe.db or not frappe.db.exists("DocType", "Global Company Filter Setting"):
			return

		doc = frappe.get_doc("Global Company Filter Setting")
		if not doc.table_adzt:
			system_doctypes = [
				"User",
				"Role",
				"DocType",
				"DocField",
				"DocPerm",
				"Print Format",
				"Page",
				"Report",
				"Module Def",
				"Desktop Icon",
				"Workspace",
				"Dashboard",
				"Number Card",
				"Dashboard Chart",
				"Session Default",
				"System Settings",
				"Error Log",
				"Activity Log",
				"Email Queue",
				"Communication",
				"Comment",
				"File",
				"Version",
				"Translation",
				"Language",
				"Letter Head",
				"Email Template",
				"Print Settings",
				"Customize Form",
				"Property Setter",
				"Custom Field",
				"Company",
			]
			for dt in system_doctypes:
				doc.append("table_adzt", {"doctype_to_ignore": dt})
			doc.save(ignore_permissions=True)
			frappe.db.commit()
	except Exception:
		pass


def get_permission_query_conditions(user, doctype=None):
	"""
	Apply global company filter to all doctypes that have a company field
	This function is called by Frappe's permission system
	"""
	try:
		# Handle both calling patterns
		if doctype is None:
			return ""

		# Check if filter is enabled
		if not is_filter_enabled():
			return ""

		# Skip system/core doctypes and user-configured ignored doctypes to avoid boot issues
		if doctype in get_ignored_doctypes():
			return ""

		# Check if session is available (avoid boot errors)
		if not hasattr(frappe, "session") or not frappe.session:
			return ""

		# Check if database is available
		if not hasattr(frappe, "db") or not frappe.db:
			return ""

		# Check if this doctype has a company field FIRST
		# to avoid infinite recursion when looking up user's company
		company_field_name = get_company_field_name(doctype)

		if not company_field_name:
			return ""

		# Get user's selected/default company
		user_company = get_user_company()

		if not user_company:
			return ""

		# Return the condition to filter by company
		if treat_empty_company_as_global():
			condition = f"(`tab{doctype}`.`{company_field_name}` = {frappe.db.escape(user_company)} OR `tab{doctype}`.`{company_field_name}` = '' OR `tab{doctype}`.`{company_field_name}` IS NULL)"
		else:
			condition = f"`tab{doctype}`.`{company_field_name}` = {frappe.db.escape(user_company)}"

		return condition

	except Exception:
		# Don't raise errors during permission queries to avoid boot failures
		return ""


def get_user_company():
	"""Get user's selected company from session or default"""
	try:
		# Check if session is available
		if not hasattr(frappe, "session") or not frappe.session:
			return None

		# First check if user has selected a company in session
		selected_company = frappe.session.get("selected_company")

		if selected_company:
			return selected_company

		# Check if defaults module is available
		if not hasattr(frappe, "defaults"):
			return None

		# Fallback to user's default company
		default_company = frappe.defaults.get_user_default("Company")

		if default_company:
			return default_company

		# If no default, get first available company user has access to
		if hasattr(frappe, "get_list"):
			companies = frappe.get_list("Company", fields=["name"], limit=1)

			if companies:
				return companies[0].name

		return None

	except Exception:
		# Don't raise errors during session boot
		return None


def get_company_field_name(doctype):
	"""Check if doctype has a company field and return the field name"""
	try:
		# Check if get_meta is available
		if not hasattr(frappe, "get_meta"):
			return None

		meta = frappe.get_meta(doctype)

		# Check if doctype has company field (either 'company' or 'custom_company')
		for field in meta.fields:
			if field.fieldname in ["company", "custom_company"] and field.fieldtype == "Link":
				if field.options == "Company":  # Make sure it links to Company doctype
					return field.fieldname

		return None

	except Exception:
		# Don't raise errors during permission queries
		return None


@frappe.whitelist()
def set_selected_company(company):
	"""Set user's selected company in session"""
	try:
		if company:
			# Validate company exists and user has access
			if frappe.db.exists("Company", company):
				frappe.session["selected_company"] = company
				frappe.db.commit()
				return {"status": "success", "company": company}

		return {"status": "error", "message": "Invalid company"}

	except Exception:
		return {"status": "error", "message": "Error setting company"}


@frappe.whitelist()
def get_selected_company():
	"""Get user's currently selected company"""
	try:
		return {
			"selected_company": frappe.session.get("selected_company") if frappe.session else None,
			"default_company": frappe.defaults.get_user_default("Company")
			if hasattr(frappe, "defaults")
			else None,
			"current_company": get_user_company(),
		}
	except Exception:
		return {"selected_company": None, "default_company": None, "current_company": None}


@frappe.whitelist()
def clear_selected_company():
	"""Clear user's selected company from session"""
	try:
		if frappe.session and "selected_company" in frappe.session:
			del frappe.session["selected_company"]
			frappe.db.commit()
		return {"status": "success", "message": "Company filter cleared"}
	except Exception:
		return {"status": "error", "message": "Error clearing company filter"}
