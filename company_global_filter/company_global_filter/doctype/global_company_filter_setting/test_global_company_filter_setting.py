# Copyright (c) 2026, Invento Software Limited and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from company_global_filter.hook_functions.global_company_filter import (
	is_filter_enabled,
	treat_empty_company_as_global,
	get_allowed_companies,
	get_permission_query_conditions,
)
from company_global_filter.hook_functions.search_link import search_link
from company_global_filter.hook_functions.getdoc import getdoc
from company_global_filter.hook_functions.treeview import (
	get_department_children,
	get_account_children,
	get_warehouse_children,
)



class IntegrationTestGlobalCompanyFilterSetting(IntegrationTestCase):
	"""
	Integration tests for GlobalCompanyFilterSetting.
	Use this class for testing interactions between multiple components.
	"""

	def setUp(self):
		super().setUp()
		# Clean up any test user permissions
		frappe.db.delete("User Permission", {"user": frappe.session.user, "allow": "Company", "for_value": "Shangu"})
		# Ensure settings is enabled for tests
		self.old_enabled = frappe.db.get_single_value("Global Company Filter Setting", "enabled")

		frappe.db.set_value("Global Company Filter Setting", "Global Company Filter Setting", "enabled", 1)
		frappe.db.commit()
		# Remove Shangu from ignored list if it's there
		self.ignored_doc = frappe.get_doc("Global Company Filter Setting")
		self.old_ignored = [row.doctype_to_ignore for row in self.ignored_doc.table_adzt]
		if "ToDo" in self.old_ignored:
			self.ignored_doc.table_adzt = [row for row in self.ignored_doc.table_adzt if row.doctype_to_ignore != "ToDo"]
			self.ignored_doc.save(ignore_permissions=True)
			frappe.db.commit()

	def tearDown(self):
		# Clean up test user permissions
		frappe.db.delete("User Permission", {"user": frappe.session.user, "allow": "Company", "for_value": "Shangu"})
		# Restore old settings
		frappe.db.set_value("Global Company Filter Setting", "Global Company Filter Setting", "enabled", self.old_enabled)
		# Restore ignored list
		self.ignored_doc = frappe.get_doc("Global Company Filter Setting")
		self.ignored_doc.table_adzt = []
		for item in self.old_ignored:
			self.ignored_doc.append("table_adzt", {"doctype_to_ignore": item})
		self.ignored_doc.save(ignore_permissions=True)
		frappe.db.commit()
		super().tearDown()

	def test_is_filter_enabled_default(self):
		self.assertIn(is_filter_enabled(), [True, False])

	def test_treat_empty_company_as_global_default(self):
		self.assertIn(treat_empty_company_as_global(), [True, False])

	def test_get_allowed_companies_no_permission(self):
		# With no User Permission, should return company itself + descendants (Shangu + Farseeing + Voyager + Shangu Tex + Corporate Office)
		allowed = get_allowed_companies("Shangu")
		self.assertIn("Shangu", allowed)
		self.assertIn("Farseeing Knit Composite Limited", allowed)
		self.assertIn("Voyager Apparels Limited", allowed)
		self.assertIn("Shangu Tex Limited", allowed)
		self.assertIn("Corporate Office", allowed)

	def test_get_allowed_companies_hide_descendants_disabled(self):
		# Create User Permission with hide_descendants = 0
		user_perm = frappe.get_doc({
			"doctype": "User Permission",
			"user": frappe.session.user,
			"allow": "Company",
			"for_value": "Shangu",
			"hide_descendants": 0
		}).insert()

		try:
			allowed = get_allowed_companies("Shangu")
			self.assertIn("Shangu", allowed)
			self.assertIn("Farseeing Knit Composite Limited", allowed)
		finally:
			frappe.delete_doc("User Permission", user_perm.name)

	def test_get_allowed_companies_hide_descendants_enabled(self):
		# Create User Permission with hide_descendants = 1
		user_perm = frappe.get_doc({
			"doctype": "User Permission",
			"user": frappe.session.user,
			"allow": "Company",
			"for_value": "Shangu",
			"hide_descendants": 1
		}).insert()

		try:
			allowed = get_allowed_companies("Shangu")
			self.assertEqual(allowed, ["Shangu"])
		finally:
			frappe.delete_doc("User Permission", user_perm.name)

	def test_get_permission_query_conditions_with_descendants(self):
		# Mock session user and selected company
		frappe.session.selected_company = "Shangu"
		
		# Test conditions on a doctype like ToDo (if it had company field, but wait, ToDo doesn't have company)
		# Let's check for a doctype that has company field, like "Company" itself or custom doctype.
		# Since Company itself is ignored, let's check a standard doctype like "Warehouse" or "Account"
		
		# Ensure "Account" has company field
		meta = frappe.get_meta("Account")
		has_company = any(f.fieldname == "company" for f in meta.fields)
		if has_company:
			cond = get_permission_query_conditions(frappe.session.user, "Account")
			# Since hide_descendants is disabled by default, we expect IN query containing Shangu and descendants
			self.assertIn("IN", cond)
			self.assertIn("Shangu", cond)
			self.assertIn("Farseeing Knit Composite Limited", cond)

	def test_get_permission_query_conditions_hide_descendants(self):
		# Create User Permission with hide_descendants = 1
		user_perm = frappe.get_doc({
			"doctype": "User Permission",
			"user": frappe.session.user,
			"allow": "Company",
			"for_value": "Shangu",
			"hide_descendants": 1
		}).insert()

		frappe.session.selected_company = "Shangu"

		try:
			cond = get_permission_query_conditions(frappe.session.user, "Account")
			# Since hide_descendants is enabled, we expect strict equality `=`
			self.assertIn("=", cond)
			self.assertNotIn("IN", cond)
		finally:
			frappe.delete_doc("User Permission", user_perm.name)

	def test_treeview_get_children_filters_by_allowed_companies(self):
		# Set selected company to "Farseeing Knit Composite Limited"
		frappe.session.selected_company = "Farseeing Knit Composite Limited"
		frappe.defaults.set_user_default("Company", "Farseeing Knit Composite Limited")

		try:
			res = get_account_children("Cost Center", parent="", company="Farseeing Knit Composite Limited", is_root=True)
			# Should only return Cost Center of "Farseeing Knit Composite Limited"
			values = [r["value"] for r in res]
			self.assertIn("Farseeing Knit Composite Limited - FKCL", values)
			self.assertNotIn("Shangu - S", values)
		finally:
			# Reset session
			frappe.session.selected_company = None
			frappe.defaults.set_user_default("Company", None)

	def test_treeview_get_children_hide_descendants(self):
		# Create User Permission with hide_descendants = 1 for "Shangu"
		user_perm = frappe.get_doc({
			"doctype": "User Permission",
			"user": frappe.session.user,
			"allow": "Company",
			"for_value": "Shangu",
			"hide_descendants": 1
		}).insert()

		frappe.session.selected_company = "Shangu"
		frappe.defaults.set_user_default("Company", "Shangu")

		try:
			# With hide descendants enabled on "Shangu", get_allowed_companies returns only "Shangu"
			# Descendant companies (e.g. Farseeing Knit Composite Limited) should be filtered out
			res = get_account_children("Cost Center", parent="", company="Shangu", is_root=True)
			values = [r["value"] for r in res]
			self.assertIn("Shangu - S", values)
			self.assertNotIn("Farseeing Knit Composite Limited - FKCL", values)
		finally:
			frappe.delete_doc("User Permission", user_perm.name)
			frappe.session.selected_company = None
			frappe.defaults.set_user_default("Company", None)

	def test_department_get_children(self):
		frappe.session.selected_company = "Shangu"
		frappe.defaults.set_user_default("Company", "Shangu")
		try:
			res = get_department_children("Department", parent="All Departments", company="Shangu")
			values = [r["value"] for r in res]
			self.assertIn("Accounts - S", values)
		finally:
			frappe.session.selected_company = None
			frappe.defaults.set_user_default("Company", None)

	def test_warehouse_get_children(self):
		frappe.session.selected_company = "Shangu"
		frappe.defaults.set_user_default("Company", "Shangu")
		try:
			res = get_warehouse_children("Warehouse", parent="All Warehouses - S", company="Shangu")
			values = [r["value"] for r in res]
			self.assertIn("Goods In Transit - S", values)
		finally:
			frappe.session.selected_company = None
			frappe.defaults.set_user_default("Company", None)

