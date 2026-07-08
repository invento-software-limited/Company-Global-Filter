# 🌐 Company Global Filter — Product Overview

**Company Global Filter** by **Invento Software Limited** is a powerful Frappe/ERPNext app that automatically enforces company-level data visibility across your entire ERPNext instance. Designed for multi-company organizations, it ensures users only see records belonging to the company they are assigned to — simplifying compliance, improving data security, and eliminating cross-company confusion.

---

## 🎯 Target Audience

- **ERPNext Administrators** managing multi-company deployments
- **Organizations** with branch-wise or group-wise company structures
- **ERPNext Implementation Partners** delivering secure, role-based access
- **Finance Teams** needing strict data isolation between legal entities
- **System Integrators** building multi-tenant ERPNext solutions

---

## 🚀 Key Features

### 🔒 Global Company Filtering
- Automatically applies company filters to every doctype with a `company` or `custom_company` field
- Database-level permission queries — nothing slips through
- Zero configuration required for most doctypes

### 👤 Company Switcher (Navbar)
- Dropdown company selector in the ERPNext navbar
- Users switch between their accessible companies instantly
- Visual indication of the currently active company
- Search-enabled dropdown for quick access

### 🧠 Smart Doctype Detection
- Automatically detects doctypes with company-linked fields
- Skips system doctypes to prevent performance overhead
- Graceful fallback if a doctype lacks a company field

### 🔧 Core Method Overrides
- **`search_link`** — filters link-field search results by selected company
- **`getdoc`** — validates company ownership when loading a document
- **Permission Queries** — adds company conditions to all SQL queries at the database level

---

## 📋 Feature Checklist

| Feature | Status |
|---|---|
| Global company filtering | ✅ Active |
| Navbar company switcher | ✅ Active |
| Search-link filtering | ✅ Active |
| Document-load validation | ✅ Active |
| Database-level permission queries | ✅ Active |
| System doctype auto-exclusion | ✅ Active |
| Multi-company session management | ✅ Active |
| Custom company field support | ✅ Active |
| Fallback error handling | ✅ Active |

---

## ⚙️ How It Works

1. **User logs in** → system detects their available companies from user permissions
2. **Default company loads** → the user's default company (from User document) is set as active
3. **Every query is filtered** → `get_permission_query_conditions` injects a `company = <selected_company>` clause into every list, report, and search query
4. **User switches company** → a new session value is set; all subsequent queries instantly reflect the new company
5. **Document access validated** → when a user opens a document, `getdoc` verifies the document's company matches the selected company

---

## 🏢 Why Multi-Company Filtering Matters

Organizations running multiple companies in a single ERPNext instance face a critical challenge: **data leakage between legal entities**. An accounts user in Company A should never accidentally see invoices from Company B. Company Global Filter solves this at the architecture level — not with complex role hierarchies or manual permission rules, but with automatic, database-enforced company isolation.

Built by **Invento Software Limited** for real-world multi-company ERPNext deployments.

---

## 📞 Support & Contact

- **Publisher:** Invento Software Limited
- **Email:** munim@invento.com.bd
- **Version:** 1.0.4
- **License:** MIT
