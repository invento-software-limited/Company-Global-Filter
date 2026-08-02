app_name = "company_global_filter"
app_title = "Company Global Filter"
app_publisher = "Invento Software Limited"
app_description = "Company Global Filter automatically applies company-level filters across all doctypes in ERPNext that have a company or custom_company field. This ensures that users only see records relevant to their company, simplifying multi-company management and improving data security and usability."
app_email = "munim@invento.com.bd"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
add_to_apps_screen = [
	{
		"name": "company_global_filter",
		"logo": "/assets/company_global_filter/logo.png",
		"title": "Company Global Filter",
		# "route": "/company_global_filter",
		# "has_permission": "company_global_filter.api.permission.has_app_permission"
	}
]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_js = "cgf.bundle.js"
# app_include_css = "/assets/company_global_filter/js/company_global_filter.css"

# include js, css files in header of web template
# web_include_css = "/assets/company_global_filter/css/company_global_filter.css"
# web_include_js = "/assets/company_global_filter/js/company_global_filter.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "company_global_filter/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "company_global_filter/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "company_global_filter.utils.jinja_methods",
# 	"filters": "company_global_filter.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "company_global_filter.install.before_install"
after_install = "company_global_filter.hook_functions.global_company_filter.preload_ignore_doctypes"
after_migrate = "company_global_filter.hook_functions.global_company_filter.preload_ignore_doctypes"

# Uninstallation
# ------------

# before_uninstall = "company_global_filter.uninstall.before_uninstall"
# after_uninstall = "company_global_filter.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "company_global_filter.utils.before_app_install"
# after_app_install = "company_global_filter.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "company_global_filter.utils.before_app_uninstall"
# after_app_uninstall = "company_global_filter.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "company_global_filter.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

permission_query_conditions = {
	"*": "company_global_filter.hook_functions.global_company_filter.get_permission_query_conditions",
}
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"company_global_filter.tasks.all"
# 	],
# 	"daily": [
# 		"company_global_filter.tasks.daily"
# 	],
# 	"hourly": [
# 		"company_global_filter.tasks.hourly"
# 	],
# 	"weekly": [
# 		"company_global_filter.tasks.weekly"
# 	],
# 	"monthly": [
# 		"company_global_filter.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "company_global_filter.install.before_tests"

# Overriding Methods
# ------------------------------
#
override_whitelisted_methods = {
	"frappe.desk.search.search_link": "company_global_filter.hook_functions.search_link.search_link",
	"frappe.desk.form.load.getdoc": "company_global_filter.hook_functions.getdoc.getdoc",
}
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "company_global_filter.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["company_global_filter.utils.before_request"]
# after_request = ["company_global_filter.utils.after_request"]

# Job Events
# ----------
# before_job = ["company_global_filter.utils.before_job"]
# after_job = ["company_global_filter.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"company_global_filter.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }
