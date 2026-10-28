import frappe
from frappe import _
from frappe.desk.search import search_link


@frappe.whitelist()
def get_company_list():
	companies = search_link(txt="", doctype="Company", reference_doctype="", page_length=100000)
	company_names = [c.get("value") for c in companies]
	return company_names


def get_permission_query_conditions(user, doctype=None):
	"""
	Apply global company filter to all doctypes that have a company field
	This function is called by Frappe's permission system
	"""
	try:
		# Handle both calling patterns
		if doctype is None:
			return ""

		# Skip system/core doctypes to avoid boot issues
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
		]

		if doctype in system_doctypes:
			return ""

		# Check if session is available (avoid boot errors)
		if not hasattr(frappe, "session") or not frappe.session:
			return ""

		# Check if database is available
		if not hasattr(frappe, "db") or not frappe.db:
			return ""

		# Get user's selected/default company
		user_company = get_user_company()

		if not user_company:
			return ""

		# Check if this doctype has a company field
		company_field_name = get_company_field_name(doctype)

		if not company_field_name:
			return ""

		# Return the condition to filter by company
		# Use a more robust approach to avoid SQL syntax issues
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
