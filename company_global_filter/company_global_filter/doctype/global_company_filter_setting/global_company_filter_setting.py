# Copyright (c) 2026, Invento Software Limited and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class GlobalCompanyFilterSetting(Document):
	def onload(self):
		if not self.table_adzt:
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
				self.append("table_adzt", {"doctype_to_ignore": dt})
