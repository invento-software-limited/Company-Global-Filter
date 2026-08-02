# Copyright (c) 2026, Invento Software Limited and Contributors
# See license.txt

# import frappe
from frappe.tests import IntegrationTestCase

from company_global_filter.hook_functions.global_company_filter import (
	is_filter_enabled,
	treat_empty_company_as_global,
)

# On IntegrationTestCase, the doctype test records and all
# link-field test record dependencies are recursively loaded
# Use these module variables to add/remove to/from that list
EXTRA_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]
IGNORE_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]


class IntegrationTestGlobalCompanyFilterSetting(IntegrationTestCase):
	"""
	Integration tests for GlobalCompanyFilterSetting.
	Use this class for testing interactions between multiple components.
	"""

	def test_is_filter_enabled_default(self):
		# Should return boolean
		self.assertIn(is_filter_enabled(), [True, False])

	def test_treat_empty_company_as_global_default(self):
		# Should return boolean
		self.assertIn(treat_empty_company_as_global(), [True, False])
