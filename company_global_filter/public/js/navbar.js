
frappe.provide("company_global_filter.ui");

company_global_filter.ui.SidebarCompanySwitcher = class {
	constructor() {
		this.companies = [];
		this.active_company_logo = null;
		this._making = false; // guard against concurrent async calls
		this.inject_styles();
		this.init_observer();
	}

	get_initials(name) {
		return name.split(" ").map(n => n[0]).join("").toUpperCase().substring(0, 2);
	}

	inject_styles() {
		if ($("#company-switcher-styles").length) return;
		$("<style id='company-switcher-styles'>")
			.prop("type", "text/css")
			.html(`
				.company-switcher-list {
					margin: 4px 0;
					padding: 0 3px;
				}
				.company-switcher-list .switcher-btn {
					height: 30px !important;
					display: flex !important;
					align-items: center !important;
					padding: 0 8px !important;
					border-radius: 6px !important;
					background: transparent !important;
					border: none !important;
					width: 100% !important;
					transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
					font-size: 14px !important;
					color: rgb(56, 56, 56) !important;
					text-decoration: none !important;
					cursor: pointer;
				}
				.company-switcher-list .switcher-btn:hover {
					background-color: var(--bg-light-gray, #f3f3f3) !important;
				}
				.company-switcher-list .switcher-btn:active {
					background-color: var(--bg-gray, #ebebeb) !important;
				}

				.company-switcher-list .company-icon-container {
					width: 18px;
					height: 18px;
					display: flex;
					align-items: center;
					justify-content: center;
					margin-right: 12px;
					flex-shrink: 0;
				}
				.company-switcher-list .company-logo-img {
					max-width: 100%;
					max-height: 100%;
					border-radius: 2px;
					object-fit: contain;
				}
				.company-switcher-list .company-avatar {
					width: 18px;
					height: 18px;
					border-radius: 4px;
					background-color: var(--primary-color, #171717);
					color: #fff;
					font-size: 8px;
					font-weight: 600;
					display: flex;
					align-items: center;
					justify-content: center;
					text-transform: uppercase;
				}

				.company-switcher-list .switcher-text {
					flex: 1;
					font-weight: 420;
					line-height: 1.2;
					white-space: nowrap;
					overflow: hidden;
					text-overflow: ellipsis;
				}

				.company-switcher-list .switcher-icon {
					font-size: 10px;
					color: rgb(140, 140, 140);
					margin-left: 8px;
				}

				/* Collapsed Sidebar Logic */
				.company-switcher-list.is-collapsed {
					padding: 0 !important;
					display: flex;
					justify-content: center;
				}
				.company-switcher-list.is-collapsed .switcher-btn {
					padding: 0 !important;
					justify-content: center !important;
					width: 30px !important;
				}
				.company-switcher-list.is-collapsed .company-icon-container {
					margin-right: 0 !important;
				}
				.company-switcher-list.is-collapsed .switcher-text,
				.company-switcher-list.is-collapsed .switcher-icon {
					display: none !important;
				}

				/* Dropdown — fixed-positioned so it escapes sidebar overflow/clipping */
				#sidebar-company-dropdown {
					position: fixed !important;
					width: 220px;
					border-radius: 10px;
					margin-top: 4px;
					box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1) !important;
					z-index: 1060;
				}
			`)
			.appendTo("head");
	}

	init_observer() {
		const targetNode = document.body;
		const config = { childList: true, subtree: true };

		const callback = (mutationsList, observer) => {
			if (!$(".company-switcher-list").length && $(".body-sidebar").length && !this._making) {
				this.make();
			}
		};

		const observer = new MutationObserver(callback);
		observer.observe(targetNode, config);

		$(document).ready(() => this.make());

		// Collapse detection
		setInterval(() => {
			const $sidebar = $(".body-sidebar");
			const $switcher = $(".company-switcher-list");
			if ($sidebar.length && $switcher.length) {
				const width = $sidebar.outerWidth();
				if (width > 0 && width < 100) {
					$switcher.addClass("is-collapsed");
				} else {
					$switcher.removeClass("is-collapsed");
				}
			}
		}, 300);
	}

	async make() {
		// Prevent duplicate creation — async race condition guard
		if (this._making || $(".company-switcher-list").length) return;
		this._making = true;

		try {
			let $sidebar = $(".body-sidebar");
			if (!$sidebar.length) return;

			let company = frappe.defaults.get_user_default("Company") || __("Select Company");

			// Fetch logo for active company
			if (company !== __("Select Company")) {
				try {
					const r = await frappe.db.get_value('Company', company, 'company_logo');
					this.active_company_logo = r.message.company_logo;
				} catch (e) {
					console.log("Error fetching company logo", e);
				}
			}

			// Double-check after await — another call may have finished first
			if ($(".company-switcher-list").length) return;

			const icon_html = this.active_company_logo
				? `<img src="${this.active_company_logo}" class="company-logo-img">`
				: `<div class="company-avatar">${this.get_initials(company)}</div>`;

			this.$container = $(`
				<div class="company-switcher-list">
					<div class="dropdown">
						<button class="switcher-btn" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
							<div class="company-icon-container">
								${icon_html}
							</div>
							<span class="switcher-text">${company}</span>
							<i class="fa fa-chevron-down switcher-icon"></i>
						</button>
						<div class="dropdown-menu shadow-lg border" id="sidebar-company-dropdown">
							<div class="px-3 py-2 border-bottom sticky-top bg-white">
								<input type="text" class="form-control form-control-sm" placeholder="${__("Search Company...")}" id="sidebar-company-search" autocomplete="off" style="border-radius: 6px;">
							</div>
							<div id="sidebar-company-options" class="py-1">
								<div class="text-muted small px-3 py-2 text-center small italic">${__("Loading...")}</div>
							</div>
						</div>
					</div>
				</div>
			`);

			let $header = $sidebar.find(".sidebar-header");
			if ($header.length) {
				this.$container.insertAfter($header);
			} else {
				$sidebar.prepend(this.$container);
			}

			this.bind_events();
			this.load_companies();
		} finally {
			this._making = false;
		}
	}

	bind_events() {
		// Align fixed-position dropdown to the trigger button on open
		this.$container.on("show.bs.dropdown", () => {
			const btn = this.$container.find(".switcher-btn")[0];
			if (!btn) return;
			const rect = btn.getBoundingClientRect();
			const $dropdown = this.$container.find("#sidebar-company-dropdown");
			$dropdown.css({
				top: rect.bottom + 4,
				left: rect.left,
			});
		});

		this.$container.on("shown.bs.dropdown", () => {
			this.$container.find("#sidebar-company-search").focus();
		});

		this.$container.find("#sidebar-company-search").on("input", (e) => {
			let val = $(e.currentTarget).val().toLowerCase();
			this.render_list(val);
		});

		this.$container.find("#sidebar-company-search").on("click", (e) => {
			e.stopPropagation();
		});
	}

	load_companies() {
		frappe.call({
			method: 'company_global_filter.hook_functions.global_company_filter.get_company_list',
			callback: (r) => {
				this.companies = r.message || [];
				this.render_list();
			}
		});
	}

	render_list(filter = "") {
		let $options = this.$container.find("#sidebar-company-options");
		if (!$options.length) return;

		$options.empty();

		let filtered = this.companies.filter(c => c.toLowerCase().includes(filter));

		if (!filtered.length) {
			$options.append(`<div class="text-muted small px-3 py-2 text-center italic">${__("No matching companies")}</div>`);
			return;
		}

		filtered.forEach(name => {
			let is_current = name === frappe.defaults.get_user_default("Company");
			let $btn = $(`
				<button class="btn-reset dropdown-item py-2 px-3 ellipsis d-flex align-items-center ${is_current ? 'active' : ''}" style="font-size: 13px; border-radius: 4px; margin: 2px 8px; width: calc(100% - 16px);">
					<span class="ellipsis">${name}</span>
					${is_current ? '<i class="fa fa-check ml-auto text-primary" style="font-size: 10px;"></i>' : ''}
				</button>
			`);
			$btn.on("click", () => {
				this.set_company(name);
			});
			$options.append($btn);
		});
	}

	set_company(company) {
		frappe.dom.freeze(__("Changing Company..."));
		frappe.call({
			method: "frappe.core.doctype.session_default_settings.session_default_settings.set_session_default_values",
			args: {
				default_values: { company: company }
			},
			callback: function (r) {
				if (r.message == "success") {
					frappe.show_alert({
						message: __("Company set to {0}", [company]),
						indicator: "green"
					});
					location.reload();
				} else {
					frappe.dom.unfreeze();
				}
			}
		});
	}
};

new company_global_filter.ui.SidebarCompanySwitcher();
