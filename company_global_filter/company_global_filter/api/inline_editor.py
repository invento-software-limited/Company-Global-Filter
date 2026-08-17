import frappe
from frappe import _
from frappe.utils import get_datetime, parse_json

def check_inline_edit_permission(doctype, fieldname):
	if not frappe.db.exists("Inline Editor Settings", doctype):
		frappe.throw(_("Inline editing is not enabled for DocType {0}").format(doctype))
		
	settings = frappe.get_doc("Inline Editor Settings", doctype)
	if not settings.enabled:
		frappe.throw(_("Inline editing is disabled for DocType {0}").format(doctype))
		
	is_editable = False
	for f in settings.fields:
		if f.fieldname == fieldname and f.editable:
			is_editable = True
			break
			
	if not is_editable:
		frappe.throw(_("Field {0} is not configured as inline-editable for DocType {1}").format(fieldname, doctype))

@frappe.whitelist()
def get_inline_editor_settings(doctype):
	if not frappe.db.exists("Inline Editor Settings", doctype):
		return None
	
	settings = frappe.get_doc("Inline Editor Settings", doctype)
	if not settings.enabled:
		return None
	
	# Fetch allowed fields
	fields = {}
	for f in settings.fields:
		if f.editable:
			fields[f.fieldname] = {
				"fieldname": f.fieldname,
				"editable": f.editable,
				"editor_type": f.editor_type,
				"required": f.required,
				"allow_bulk_edit": f.allow_bulk_edit,
				"width": f.width
			}
			
	return {
		"enabled": settings.enabled,
		"edit_mode": settings.edit_mode,
		"allow_bulk_edit": settings.allow_bulk_edit,
		"allow_copy_paste": settings.allow_copy_paste,
		"allow_keyboard_navigation": settings.allow_keyboard_navigation,
		"save_debounce": settings.save_debounce or 500,
		"fields": fields
	}

@frappe.whitelist()
def update_field(doctype, docname, fieldname, value, modified=None):
	check_inline_edit_permission(doctype, fieldname)
	
	doc = frappe.get_doc(doctype, docname)
	doc.check_permission("write")
	
	meta = frappe.get_meta(doctype)
	df = meta.get_field(fieldname)
	if not df:
		frappe.throw(_("Field {0} does not exist in {1}").format(fieldname, doctype))
		
	if df.read_only:
		frappe.throw(_("Field {0} is read-only").format(fieldname))
		
	# Enforce submitted document rules
	if doc.docstatus == 1 and not df.allow_on_submit:
		frappe.throw(_("Cannot modify field '{0}' on a submitted document").format(df.label or fieldname))
		
	# Enforce field level permission level (permlevel)
	if df.permlevel:
		if not doc.has_permlevel_access_to(fieldname, df, "write"):
			frappe.throw(_("You do not have permission to edit {0}").format(df.label or fieldname))
			
	# Conflict detection
	if modified:
		doc_mod = get_datetime(doc.modified)
		client_mod = get_datetime(modified)
		if abs((doc_mod - client_mod).total_seconds()) > 1:
			frappe.throw(_("Document {0} was modified by another user. Please reload.").format(docname))
			
	# Update the field value
	doc.set(fieldname, value)
	doc.save()
	
	return {
		"name": doc.name,
		"fieldname": fieldname,
		"value": doc.get(fieldname),
		"modified": doc.modified
	}

@frappe.whitelist()
def bulk_update(doctype, updates):
	updates = parse_json(updates)
	
	# If updates are large, we can queue them as a background job
	if len(updates) > 50:
		job = frappe.enqueue(
			"company_global_filter.company_global_filter.api.inline_editor.run_bulk_update_job",
			queue="default",
			doctype=doctype,
			updates=updates,
			user=frappe.session.user
		)
		return {
			"status": "queued",
			"job_id": job.id
		}
		
	results = []
	for i, item in enumerate(updates):
		name = item.get("name")
		values = item.get("values", {})
		modified = item.get("modified")
		
		savepoint_name = f"sp_bulk_{i}"
		try:
			frappe.db.savepoint(savepoint_name)
			
			doc = frappe.get_doc(doctype, name)
			doc.check_permission("write")
			
			for fieldname, value in values.items():
				check_inline_edit_permission(doctype, fieldname)
				
				df = doc.meta.get_field(fieldname)
				if not df or df.read_only:
					raise Exception(_("Field {0} is invalid or read-only").format(fieldname))
					
				if doc.docstatus == 1 and not df.allow_on_submit:
					raise Exception(_("Cannot modify field '{0}' on a submitted document").format(df.label or fieldname))
					
				if df.permlevel and not doc.has_permlevel_access_to(fieldname, df, "write"):
					raise Exception(_("No permission to edit field {0}").format(df.label or fieldname))
					
				doc.set(fieldname, value)
				
			if modified:
				doc_mod = get_datetime(doc.modified)
				client_mod = get_datetime(modified)
				if abs((doc_mod - client_mod).total_seconds()) > 1:
					raise Exception(_("Document was modified by another user"))
					
			doc.save()
			results.append({
				"name": name,
				"status": "success",
				"modified": doc.modified
			})
		except Exception as e:
			frappe.db.rollback(save_point=savepoint_name)
			results.append({
				"name": name,
				"status": "error",
				"error": str(e)
			})
			
	return {
		"status": "completed",
		"results": results
	}

def run_bulk_update_job(doctype, updates, user):
	# Set current user session for permissions
	frappe.set_user(user)
	results = []
	for i, item in enumerate(updates):
		name = item.get("name")
		values = item.get("values", {})
		modified = item.get("modified")
		
		savepoint_name = f"sp_bulk_job_{i}"
		try:
			frappe.db.savepoint(savepoint_name)
			
			doc = frappe.get_doc(doctype, name)
			doc.check_permission("write")
			for fieldname, value in values.items():
				check_inline_edit_permission(doctype, fieldname)
				
				df = doc.meta.get_field(fieldname)
				if not df or df.read_only:
					raise Exception(_("Field {0} is invalid or read-only").format(fieldname))
				if doc.docstatus == 1 and not df.allow_on_submit:
					raise Exception(_("Cannot modify field '{0}' on a submitted document").format(df.label or fieldname))
				if df.permlevel and not doc.has_permlevel_access_to(fieldname, df, "write"):
					raise Exception(_("No permission to edit field {0}").format(df.label or fieldname))
				doc.set(fieldname, value)
			if modified:
				doc_mod = get_datetime(doc.modified)
				client_mod = get_datetime(modified)
				if abs((doc_mod - client_mod).total_seconds()) > 1:
					raise Exception(_("Document was modified by another user"))
			doc.save()
			results.append({
				"name": name,
				"status": "success",
				"modified": doc.modified
			})
		except Exception as e:
			frappe.db.rollback(save_point=savepoint_name)
			results.append({
				"name": name,
				"status": "error",
				"error": str(e)
			})
	# Publish a realtime event to notify the user
	frappe.publish_realtime(
		"inline_editor_bulk_update_finished",
		{"results": results, "doctype": doctype},
		user=user
	)

