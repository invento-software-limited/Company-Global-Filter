# 📘 Company Global Filter — User Guide

A step-by-step guide to installing, configuring, and using **Company Global Filter** by **Invento Software Limited** to enforce company-level data visibility in ERPNext.

---

## 📦 Installation

### Prerequisites
- ERPNext version 15 or 16
- Frappe Bench environment
- Multiple companies set up in your ERPNext instance

### Steps

```bash
# Navigate to your bench directory
cd ~/frappe-bench

# Download the app
bench get-app company_global_filter

# Install on your site
bench --site your-site.local install-app company_global_filter

# Build assets
bench build
```

### Post-Installation
After installation, you will see a **Company Switcher** dropdown in the top-right navbar of your ERPNext desk.

---

## ⚙️ Configuration

### Step 1: Set Default Company for Users

Each user needs a default company assigned:

1. Go to **User** list (✱ → User)
2. Open the user's document
3. Under **Default Company**, select their primary company
4. Save

> Users can switch to any other company they have permission for via the navbar dropdown.

### Step 2: Verify Doctype Compatibility

The app automatically filters all doctypes that have a standard `company` field **(type: Link, options: Company)** or a custom `custom_company` field.

**To verify a doctype is filtered:**
1. Open the doctype in **Customize Form**
2. Check if it has a `company` or `custom_company` field
3. If yes — filtering is automatic

### Step 3: Set Up User Permissions

Ensure users have appropriate **Company** access:

1. Go to **User Permission** list
2. Create a new User Permission record
3. Set **Allow** = `Company`
4. Select the **Company** the user should access
5. Assign the **User**

Repeat for each company a user needs access to.

---

## 🎯 Using Company Global Filter

### Switching Companies

![Company Switcher in Navbar](assets/cgf-navbar.png)
*The company selector appears in the top-right navbar.*

1. Click the **current company name** in the navbar
2. A dropdown shows all companies you have access to
3. Select a new company
4. The entire interface instantly switches — all lists, reports, and searches now show only data for the selected company

### Visual Indicators

- The active company is always displayed in the navbar
- Reports and lists only show records matching the selected company
- Link field searches (e.g., selecting a Customer in a Sales Invoice) only return records from the current company

### What Gets Filtered

| Feature | Filtered? |
|---|---|
| Document Lists | ✅ Yes |
| Reports | ✅ Yes |
| Link Field Searches | ✅ Yes |
| Dashboard Data | ✅ Yes |
| Print Formats | ✅ Yes |
| System Doctypes (User, Role, etc.) | ❌ No (auto-excluded) |

---

## 🛠️ Advanced Usage

### Using the API

Company Global Filter exposes Python methods for programmatic access:

```python
# Get list of companies accessible to the current user
companies = frappe.call("company_global_filter.api.get_company_list")

# Set the active company
frappe.call("company_global_filter.api.set_selected_company", {
    "company": "Company Name"
})

# Get currently selected company
current = frappe.call("company_global_filter.api.get_selected_company")

# Clear the selection (reverts to default)
frappe.call("company_global_filter.api.clear_selected_company")
```

### Custom Company Fields

If your custom doctype uses a non-standard field name, the app supports `custom_company` fields automatically. For other field names, modify the detection pattern in `global_company_filter.py`.

### Adding Custom Exclusions

To exclude specific doctypes from filtering:

```python
# In your custom app's hooks.py or override
# Extend the system_doctypes list in
# company_global_filter.hook_functions.global_company_filter
```

---

## 🔍 Troubleshooting

### Problem: Company Filter Not Applied

**Check:**
1. Does the doctype have a `company` or `custom_company` field?
2. Does the user have a **Default Company** set in their User document?
3. Does the user have **User Permission** for the company?

### Problem: Too Many Records Hidden

**Check:**
1. Has the user selected the correct company in the navbar?
2. Do the missing records actually have the company field populated?
3. Has a User Permission been created for the relevant company?

### Problem: Performance Concerns

Company Global Filter is designed for performance:
- System doctypes are automatically excluded
- Permission queries use indexed `company` fields
- Minimal overhead — a single WHERE clause addition per query

### Problem: Permission Errors on Document Load

If a user gets a permission error loading a document:
1. Confirm the document's company matches the user's selected company
2. Verify the user has access to that company
3. Switch companies via the navbar if needed

---

## 📋 FAQ

**Q: Does this app modify my data?**
A: No. It only filters what users can *see* — it never alters or deletes data.

**Q: Can a user access multiple companies?**
A: Yes. Users can switch between any companies they have permission for.

**Q: Does it work with custom doctypes?**
A: Yes — any doctype with a standard `company` field or `custom_company` field is automatically filtered.

**Q: Will it slow down my ERPNext instance?**
A: No. The filtering is lightweight — a single company condition added to each query. System doctypes are excluded.

**Q: Can I disable filtering for specific doctypes?**
A: Yes. System doctypes are auto-excluded, and you can extend the exclusion list.

---

## 📞 Support

For issues, feature requests, or custom development:

- **Publisher:** Invento Software Limited
- **Email:** munim@invento.com.bd
- **Version:** 1.0.4
- **License:** MIT
