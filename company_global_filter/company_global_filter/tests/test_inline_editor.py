import frappe
from frappe.tests import IntegrationTestCase
from company_global_filter.company_global_filter.api.inline_editor import (
	get_inline_editor_settings,
	update_field,
	bulk_update
)

class TestInlineEditor(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		# Clean up any existing settings for ToDo
		if frappe.db.exists("Inline Editor Settings", "ToDo"):
			frappe.delete_doc("Inline Editor Settings", "ToDo")
		
		# Create a dummy ToDo to run tests on
		self.todo = frappe.get_doc({
			"doctype": "ToDo",
			"description": "Test Inline Editor Target",
			"status": "Open"
		}).insert()

		# Create settings document by default for tests
		self.settings_doc = frappe.get_doc({
			"doctype": "Inline Editor Settings",
			"name": "ToDo",
			"enabled": 1,
			"edit_mode": "Auto Save",
			"save_debounce": 300,
			"fields": [
				{
					"fieldname": "description",
					"editable": 1,
					"editor_type": "Small Text"
				}
			]
		}).insert()

	def tearDown(self):
		if hasattr(self, 'todo') and frappe.db.exists("ToDo", self.todo.name):
			frappe.delete_doc("ToDo", self.todo.name)
		if frappe.db.exists("Inline Editor Settings", "ToDo"):
			frappe.delete_doc("Inline Editor Settings", "ToDo")
		super().tearDown()

	def test_get_settings_none_exists(self):
		# Delete setting temporarily to test when it doesn't exist
		frappe.delete_doc("Inline Editor Settings", "ToDo")
		settings = get_inline_editor_settings("ToDo")
		self.assertIsNone(settings)

	def test_get_settings_enabled(self):
		settings = get_inline_editor_settings("ToDo")
		self.assertIsNotNone(settings)
		self.assertEqual(settings["edit_mode"], "Auto Save")
		self.assertEqual(settings["save_debounce"], 300)
		self.assertIn("description", settings["fields"])
		self.assertEqual(settings["fields"]["description"]["editor_type"], "Small Text")

	def test_update_field_success(self):
		# Update field description
		res = update_field("ToDo", self.todo.name, "description", "Updated Value", self.todo.modified)
		self.assertEqual(res["value"], "Updated Value")
		
		# Verify db state
		self.assertEqual(frappe.db.get_value("ToDo", self.todo.name, "description"), "Updated Value")

	def test_update_field_disabled_settings(self):
		# Disable settings and verify update fails
		self.settings_doc.enabled = 0
		self.settings_doc.save()

		with self.assertRaises(frappe.ValidationError):
			update_field("ToDo", self.todo.name, "description", "Updated Value", self.todo.modified)

	def test_update_field_not_editable(self):
		# Try to edit field 'status' which is not marked as editable in settings
		with self.assertRaises(frappe.ValidationError):
			update_field("ToDo", self.todo.name, "status", "Closed", self.todo.modified)

	def test_update_field_conflict(self):
		# Simulate a conflict by passing an older/different modified timestamp
		from datetime import timedelta
		from frappe.utils import get_datetime
		different_time = get_datetime(self.todo.modified) + timedelta(hours=1)
		
		with self.assertRaises(frappe.ValidationError):
			update_field("ToDo", self.todo.name, "description", "New Value", different_time)

	def test_update_field_invalid_field(self):
		# Test with non-existent field. Since it's not in settings, it will throw ValidationError.
		with self.assertRaises(frappe.ValidationError):
			update_field("ToDo", self.todo.name, "invalid_fieldname_xxx", "value", self.todo.modified)

	def test_bulk_update_success(self):
		# Create another todo
		todo2 = frappe.get_doc({
			"doctype": "ToDo",
			"description": "Test Inline Editor Target 2",
			"status": "Open"
		}).insert()
		
		try:
			updates = [
				{
					"name": self.todo.name,
					"modified": self.todo.modified,
					"values": {"description": "Bulk Updated 1"}
				},
				{
					"name": todo2.name,
					"modified": todo2.modified,
					"values": {"description": "Bulk Updated 2"}
				}
			]
			
			import json
			res = bulk_update("ToDo", json.dumps(updates))
			
			self.assertEqual(res["status"], "completed")
			self.assertEqual(len(res["results"]), 2)
			self.assertEqual(res["results"][0]["status"], "success")
			self.assertEqual(res["results"][1]["status"], "success")
			
			# Verify DB
			self.assertEqual(frappe.db.get_value("ToDo", self.todo.name, "description"), "Bulk Updated 1")
			self.assertEqual(frappe.db.get_value("ToDo", todo2.name, "description"), "Bulk Updated 2")
		finally:
			if frappe.db.exists("ToDo", todo2.name):
				frappe.delete_doc("ToDo", todo2.name)

	def test_bulk_update_savepoint_isolation(self):
		# Create another todo
		todo2 = frappe.get_doc({
			"doctype": "ToDo",
			"description": "Test Inline Editor Target 2",
			"status": "Open"
		}).insert()
		
		try:
			# Verify the description before
			self.assertEqual(self.todo.description, "Test Inline Editor Target")
			self.assertEqual(todo2.description, "Test Inline Editor Target 2")

			updates = [
				{
					"name": self.todo.name,
					"modified": self.todo.modified,
					"values": {"description": "Bulk Updated 1"}
				},
				{
					"name": todo2.name,
					"modified": todo2.modified,
					"values": {"status": "Closed"}  # status is not editable (will fail)
				}
			]
			
			import json
			res = bulk_update("ToDo", json.dumps(updates))
			
			self.assertEqual(res["status"], "completed")
			self.assertEqual(res["results"][0]["status"], "success")
			self.assertEqual(res["results"][1]["status"], "error")
			
			# The first update should succeed and be committed/saved
			self.assertEqual(frappe.db.get_value("ToDo", self.todo.name, "description"), "Bulk Updated 1")
			# The second update failed, so todo2 description and status should remain unchanged
			self.assertEqual(frappe.db.get_value("ToDo", todo2.name, "status"), "Open")
		finally:
			if frappe.db.exists("ToDo", todo2.name):
				frappe.delete_doc("ToDo", todo2.name)
