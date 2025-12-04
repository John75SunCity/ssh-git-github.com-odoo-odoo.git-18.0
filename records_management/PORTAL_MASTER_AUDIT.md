# PORTAL MASTER AUDIT - FINAL
Generated: 2025-12-04 11:50

---

## 📊 EXECUTIVE SUMMARY

| Metric | Count | Status |
|--------|-------|--------|
| Controller Files | 13 | ✅ Clean |
| Unique Routes | 158 | ✅ No Duplicates |
| Total Templates | 152 | ✅ |
| Used Templates | 65 | ✅ Active |
| Inherit Templates | 8 | ✅ Extensions |
| Unused Templates | 80 | ⚠️ Cleanup Candidate |
| Missing Templates | 0 | ✅ All Found |

---

## 📋 ROUTES BY CONTROLLER

### advanced_search.py (3 routes)

| Route | Function | Template |
|-------|----------|----------|
| `/my/inventory/advanced_search` | advanced_inventory_search | portal_advanced_inventory_search |
| `/my/inventory/export` | export_search_results | _(json/redirect)_ |
| `/my/inventory/save_search` | save_search_preset | _(json/redirect)_ |

### destruction_portal.py (12 routes)

| Route | Function | Template |
|-------|----------|----------|
| `/my/shredding` | portal_shredding_dashboard | portal_shredding_dashboard |
| `/my/shredding/bin/<int:bin_id>` | portal_shredding_bin_detail | portal_shredding_bin_detail |
| `/my/shredding/bin/<int:bin_id>/request-service` | portal_request_bin_service | portal_shredding_bins |
| `/my/shredding/bins` | portal_shredding_bins | portal_shredding_bins |
| `/my/shredding/certificate/<int:cert_id>` | portal_shredding_certificate_detail | portal_certificate_detail |
| `/my/shredding/certificate/<int:cert_id>/download` | portal_download_certificate | _(json/redirect)_ |
| `/my/shredding/certificates` | portal_shredding_certificates | portal_shredding_certificates |
| `/my/shredding/dashboard` | portal_shredding_dashboard | portal_shredding_dashboard |
| `/my/shredding/history` | portal_shredding_history | portal_shredding_history |
| `/my/shredding/request/new` | portal_new_shredding_request | portal_new_shredding_request |
| `/my/shredding/scheduled` | portal_scheduled_services | portal_scheduled_services |
| `/my/shredding/service/<int:task_id>` | portal_service_detail | portal_service_detail |

### field_label_portal.py (2 routes)

| Route | Function | Template |
|-------|----------|----------|
| `/portal/field-labels/get` | get_field_labels | _(json/redirect)_ |
| `/records/admin/field-labels/preview` | preview_field_labels | _(json/redirect)_ |

### intelligent_search.py (5 routes)

| Route | Function | Template |
|-------|----------|----------|
| `/my/records/search` | _search_portal_containers | _(json/redirect)_ |
| `/records/search/containers` | _search_containers_autocomplete | _(json/redirect)_ |
| `/records/search/fulltext` | _search_fulltext_containers | _(json/redirect)_ |
| `/records/search/recommend_containers` | _search_recommend_containers_for_file | _(json/redirect)_ |
| `/records/search/suggestions/config` | _search_config | _(json/redirect)_ |

### portal.py (113 routes)

| Route | Function | Template |
|-------|----------|----------|
| `/my/access` | portal_access | portal_error |
| `/my/barcode/main` | portal_barcode_main | portal_barcode_main_menu |
| `/my/barcode/process/<string:operation>` | portal_barcode_process | _(json/redirect)_ |
| `/my/barcode/scan/<string:scan_type>` | portal_barcode_scanner | portal_barcode_scanner |
| `/my/barcode/scan/container` | portal_barcode_scan_container | portal_barcode_scanner |
| `/my/barcode/scan/file` | portal_barcode_scan_file | portal_barcode_scanner |
| `/my/billing/rates` | portal_billing_rates | portal_billing_rates |
| `/my/billing/statements` | portal_billing_statements | portal_billing_statements |
| `/my/billing/summary` | portal_billing_summary | portal_billing_dashboard |
| `/my/certificate/<int:certificate_id>` | portal_my_certificate | portal_certificate_detail |
| `/my/certificate/<int:certificate_id>/download` | portal_certificate_download | _(json/redirect)_ |
| `/my/certificates` | portal_my_certificates | portal_my_certificates |
| `/my/certificates/page/<int:page>` | portal_my_certificates | portal_my_certificates |
| `/my/container/<int:container_id>` | portal_my_container | portal_container_detail |
| `/my/containers` | portal_my_containers | portal_my_containers |
| `/my/containers/bulk_request` | create_bulk_container_request | _(json/redirect)_ |
| `/my/containers/page/<int:page>` | portal_my_containers | portal_my_containers |
| `/my/containers/search` | instant_container_search | _(json/redirect)_ |
| `/my/custody/chain` | portal_custody_chain | portal_custody_chain |
| `/my/destruction` | portal_destruction_list | portal_destruction_list |
| `/my/destruction/<int:request_id>/approve` | portal_destruction_approve | _(json/redirect)_ |
| `/my/destruction/pending` | portal_destruction_pending | portal_error |
| `/my/document-retrieval` | portal_document_retrieval | portal_document_retrieval_template |
| `/my/document-retrieval/calculate-price` | calculate_retrieval_price | _(json/redirect)_ |
| `/my/document-retrieval/submit` | submit_retrieval_request | _(json/redirect)_ |
| `/my/document/<int:document_id>` | portal_my_document | portal_document_detail |
| `/my/document/<int:document_id>/download` | portal_document_download | _(json/redirect)_ |
| `/my/documents` | portal_my_documents | portal_my_documents |
| `/my/documents/page/<int:page>` | portal_my_documents | portal_my_documents |
| `/my/feedback` | portal_feedback | feedback_form_template |
| `/my/feedback/history` | portal_feedback_history | portal_feedback_history |
| `/my/files/bulk_request` | create_bulk_file_request | _(json/redirect)_ |
| `/my/files/search` | instant_file_search | _(json/redirect)_ |
| `/my/inventory` | portal_inventory_dashboard | portal_inventory_enhanced |
| `/my/inventory/bulk/destroy` | portal_bulk_destroy | _(json/redirect)_ |
| `/my/inventory/bulk/pickup` | portal_bulk_pickup | _(json/redirect)_ |
| `/my/inventory/bulk/retrieve` | portal_bulk_retrieve | _(json/redirect)_ |
| `/my/inventory/container/<int:container_id>` | portal_container_detail | portal_container_detail |
| `/my/inventory/container/<int:container_id>/delete` | portal_container_delete | _(json/redirect)_ |
| `/my/inventory/container/<int:container_id>/edit` | portal_container_edit | _(json/redirect)_ |
| `/my/inventory/container/<int:container_id>/movements` | portal_container_movements | portal_container_movements |
| `/my/inventory/container/<int:container_id>/request-move` | portal_container_request_move | _(json/redirect)_ |
| `/my/inventory/container/<int:container_id>/update` | portal_update_container | _(json/redirect)_ |
| `/my/inventory/containers` | portal_inventory_containers | portal_inventory_containers |
| `/my/inventory/containers/create` | portal_container_create | portal_error |
| `/my/inventory/counts` | portal_inventory_counts | portal_inventory_enhanced |
| `/my/inventory/document/<int:doc_id>` | portal_document_detail | portal_document_detail |
| `/my/inventory/document/<int:doc_id>/delete` | portal_document_delete | _(json/redirect)_ |
| `/my/inventory/document/<int:doc_id>/edit` | portal_document_edit | _(json/redirect)_ |
| `/my/inventory/document/<int:doc_id>/request-scan` | portal_document_request_scan | _(json/redirect)_ |
| `/my/inventory/document/<int:doc_id>/upload` | portal_document_upload | _(json/redirect)_ |
| `/my/inventory/document/<int:document_id>` | portal_document_detail | portal_document_detail |
| `/my/inventory/documents` | portal_inventory_documents | portal_inventory_documents |
| `/my/inventory/documents/bulk-upload` | portal_document_bulk_upload | portal_error |
| `/my/inventory/documents/create` | portal_document_create | portal_error |
| `/my/inventory/file/<int:file_id>` | portal_file_detail | portal_file_detail |
| `/my/inventory/file/<int:file_id>/add-document` | portal_file_add_document | _(json/redirect)_ |
| `/my/inventory/file/<int:file_id>/delete` | portal_file_delete | _(json/redirect)_ |
| `/my/inventory/file/<int:file_id>/edit` | portal_file_edit | _(json/redirect)_ |
| `/my/inventory/file/<int:file_id>/move-container` | portal_file_move_container | _(json/redirect)_ |
| `/my/inventory/file/<int:file_id>/upload` | portal_file_upload_document | _(json/redirect)_ |
| `/my/inventory/file/add_to_container` | portal_add_file_to_container | _(json/redirect)_ |
| `/my/inventory/files` | portal_inventory_files | portal_inventory_files |
| `/my/inventory/files/available` | portal_available_files | _(json/redirect)_ |
| `/my/inventory/files/create` | portal_file_create | portal_error |
| `/my/inventory/location/<int:location_id>` | portal_staging_location_detail | portal_staging_location_detail |
| `/my/inventory/location/<int:location_id>/archive` | portal_staging_location_archive | _(json/redirect)_ |
| `/my/inventory/location/<int:location_id>/delete` | portal_staging_location_delete | portal_error |
| `/my/inventory/location/<int:location_id>/edit` | portal_staging_location_edit | portal_error |
| `/my/inventory/location/create` | portal_staging_location_create | portal_staging_location_create |
| `/my/inventory/locations` | portal_staging_locations | portal_staging_locations |
| `/my/inventory/movements` | portal_stock_movements | portal_stock_movements |
| `/my/inventory/movements/data` | get_movements_data | _(json/redirect)_ |
| `/my/inventory/recent_activity` | portal_inventory_recent_activity | portal_reports_activity |
| `/my/inventory/temp` | portal_inventory_temp | portal_inventory_temp |
| `/my/invoices` | portal_invoices | portal_billing |
| `/my/invoices/history` | portal_invoices_history | portal_billing_details |
| `/my/notifications` | portal_notifications | portal_notifications |
| `/my/notifications/update` | portal_notifications_update | _(json/redirect)_ |
| `/my/organization` | portal_organization_chart | portal_organization_diagram |
| `/my/organization/add-user` | portal_add_team_member | portal_error |
| `/my/reports` | portal_reports | portal_reports |
| `/my/reports/activity` | portal_reports_activity | portal_reports_activity |
| `/my/reports/audit` | portal_reports_audit | portal_reports |
| `/my/reports/compliance` | portal_reports_compliance | portal_reports_compliance |
| `/my/reports/export` | portal_reports_export | portal_reports_export |
| `/my/request/new/<string:request_type>` | portal_request_create | portal_error |
| `/my/request/search_containers` | search_matching_containers | _(json/redirect)_ |
| `/my/requests` | portal_requests_list | portal_requests_template |
| `/my/requests/<int:request_id>` | portal_request_detail | portal_request_detail |
| `/my/requests/<int:request_id>/cancel` | portal_request_cancel | _(json/redirect)_ |
| `/my/requests/<int:request_id>/edit` | portal_request_edit | _(json/redirect)_ |
| `/my/requests/<int:request_id>/submit` | portal_request_submit | _(json/redirect)_ |
| `/my/retrieval-cart` | portal_retrieval_cart | portal_retrieval_cart |
| `/my/retrieval-cart/add` | portal_retrieval_cart_add | _(json/redirect)_ |
| `/my/retrieval-cart/remove` | portal_retrieval_cart_remove | _(json/redirect)_ |
| `/my/retrieval-cart/submit` | portal_retrieval_cart_submit | _(json/redirect)_ |
| `/my/service-attachment/<int:attachment_id>` | portal_service_attachment_detail | portal_service_attachment_detail |
| `/my/service-attachment/<int:attachment_id>/download` | portal_service_attachment_download | _(json/redirect)_ |
| `/my/service-attachments` | portal_service_attachments | portal_service_attachments |
| `/my/service-attachments/page/<int:page>` | portal_service_attachments | portal_service_attachments |
| `/my/service-photos` | portal_service_photos_redirect | _(json/redirect)_ |
| `/my/service-photos/page/<int:page>` | portal_service_photos_redirect | _(json/redirect)_ |
| `/my/users` | portal_department_users | portal_department_users |
| `/my/users/<int:user_id>/deactivate` | portal_deactivate_user | _(json/redirect)_ |
| `/my/users/<int:user_id>/edit` | portal_edit_department_user | _(json/redirect)_ |
| `/my/users/create` | portal_create_department_user | portal_error |
| `/portal-hub` | portal_hub | portal_my_home_preconfigured |
| `/records/report/certificates` | portal_report_certificates | _(json/redirect)_ |
| `/records/report/containers` | portal_report_containers | _(json/redirect)_ |
| `/records_management/portal/generate_container_barcode` | generate_container_barcode | _(json/redirect)_ |
| `/records_management/portal/generate_file_barcode` | generate_file_barcode | _(json/redirect)_ |
| `/records_management/portal/generate_temp_barcode` | generate_temp_barcode | _(json/redirect)_ |

### portal_access.py (2 routes)

| Route | Function | Template |
|-------|----------|----------|
| `/portal/access/<string:token>` | portal_access_login | portal_access_denied |
| `/portal/switch_back` | portal_switch_back_to_admin | _(json/redirect)_ |

### portal_barcode.py (3 routes)

| Route | Function | Template |
|-------|----------|----------|
| `/my/scan/validate` | validate_portal_scan | _(json/redirect)_ |
| `/my/scan/verify_delivery` | verify_delivery_ownership | _(json/redirect)_ |
| `/records_management/portal/generate_barcode` | generate_portal_barcode | _(json/redirect)_ |

### portal_calendar.py (2 routes)

| Route | Function | Template |
|-------|----------|----------|
| `/my/calendar` | portal_my_calendar | portal_calendar_view |
| `/my/calendar/events` | portal_calendar_events | _(json/redirect)_ |

### portal_document_bulk_upload.py (2 routes)

| Route | Function | Template |
|-------|----------|----------|
| `/my/bulk-upload` | portal_bulk_upload | portal_document_bulk_upload |
| `/my/bulk-upload/template/<string:upload_type>` | portal_bulk_upload_template | _(json/redirect)_ |

### portal_interactive.py (9 routes)

| Route | Function | Template |
|-------|----------|----------|
| `/my/barcode/process/<string:scan_type>` | process_barcode | _(json/redirect)_ |
| `/my/containers/export` | export_containers | _(json/redirect)_ |
| `/my/files/export` | export_files | _(json/redirect)_ |
| `/my/import/containers` | import_containers | _(json/redirect)_ |
| `/my/import/files` | import_files | _(json/redirect)_ |
| `/my/import/template/<string:data_type>` | download_import_template | _(json/redirect)_ |
| `/my/requests/export` | export_requests | _(json/redirect)_ |
| `/my/users/export` | export_users | _(json/redirect)_ |
| `/my/users/import` | import_users | _(json/redirect)_ |

### pos_customer_history.py (1 routes)

| Route | Function | Template |
|-------|----------|----------|
| `/records_management/pos/customer_history` | get_pos_customer_history | _(json/redirect)_ |

### work_order_portal.py (4 routes)

| Route | Function | Template |
|-------|----------|----------|
| `/my/work_order/<string:model>/<int:order_id>` | portal_work_order_detail | portal_work_order_detail |
| `/my/work_order/<string:model>/<int:order_id>/download` | portal_work_order_download | _(json/redirect)_ |
| `/my/work_orders` | portal_my_work_orders | portal_my_work_orders |
| `/my/work_orders/page/<int:page>` | portal_my_work_orders | portal_my_work_orders |

---

## 🗑️ UNUSED TEMPLATES (61 total)

### Categories:

| Category | Count | Action |
|----------|-------|--------|
| **Duplicates** | 7 | 🔴 DELETE |
| Mobile Features | 5 | 🟡 Keep if planning mobile |
| E-learning | 4 | 🟡 Keep if planning training |
| Error Pages | 2 | 🟢 KEEP |
| Empty States | 3 | 🟢 KEEP |
| Compliance | 3 | 🟡 Keep for future |
| PDF Reports | 3 | 🟡 Review |
| Profile/Settings | 3 | 🟡 Review |
| Inventory Views | 7 | 🟡 Review |
| Barcode | 2 | 🟡 Review |
| Misc | 22 | 🔴 Review each |

### 🔴 SAFE TO DELETE (Duplicates):

- `container_detail` → portal_containers.xml
- `location_detail` → portal_locations.xml
- `portal_container_form` → portal_containers.xml
- `portal_document_retrieval` → portal_document_retrieval.xml
- `portal_feedback_form` → portal_missing_templates.xml
- `portal_location_detail` → portal_locations.xml
- `portal_requests` → my_portal_inventory.xml

### 🟢 KEEP (Error handling, empty states):

- `portal_error_page` → portal_errors.xml
- `portal_not_found` → portal_errors.xml
- `portal_empty_state_certificates` → portal_home_preconfigured.xml
- `portal_empty_state_inventory` → portal_home_preconfigured.xml
- `portal_empty_state_work_orders` → portal_home_preconfigured.xml

---

## ✅ ACTIVE TEMPLATES

### Routed (used by request.render)

- `feedback_form_template` → portal_feedback.xml
- `portal_access_denied` → portal_access_templates.xml
- `portal_advanced_inventory_search` → advanced_search_templates.xml
- `portal_barcode_main_menu` → portal_barcode_templates.xml
- `portal_barcode_scanner` → portal_barcode_templates.xml
- `portal_billing` → my_portal_inventory.xml
- `portal_billing_dashboard` → portal_billing_template.xml
- `portal_billing_details` → portal_billing_template.xml
- `portal_billing_rates` → portal_missing_templates.xml
- `portal_billing_statements` → portal_missing_templates.xml
- `portal_calendar_view` → portal_calendar_view.xml
- `portal_certificate_detail` → portal_certificates.xml
- `portal_container_detail` → portal_inventory_detail.xml
- `portal_container_movements` → portal_template_aliases.xml
- `portal_custody_chain` → portal_missing_templates.xml
- `portal_department_users` → portal_missing_templates.xml
- `portal_destruction_list` → portal_missing_templates.xml
- `portal_document_bulk_upload` → portal_document_bulk_upload.xml
- `portal_document_detail` → portal_inventory_detail.xml
- `portal_document_retrieval_template` → portal_document_retrieval.xml
- `portal_error` → portal_errors.xml
- `portal_feedback_history` → portal_missing_templates.xml
- `portal_file_detail` → portal_inventory_detail.xml
- `portal_inventory_containers` → portal_inventory_tabs.xml
- `portal_inventory_documents` → portal_inventory_tabs.xml
- `portal_inventory_enhanced` → portal_template_aliases.xml
- `portal_inventory_files` → portal_inventory_tabs.xml
- `portal_inventory_temp` → portal_inventory_tabs.xml
- `portal_my_certificates` → portal_certificates.xml
- `portal_my_containers` → portal_containers_list.xml
- `portal_my_documents` → portal_documents.xml
- `portal_my_home_preconfigured` → portal_home_preconfigured.xml
- `portal_my_work_orders` → portal_work_order_templates.xml
- `portal_new_shredding_request` → portal_shredding_dashboard.xml
- `portal_notifications` → portal_profile_templates.xml
- `portal_organization_diagram` → portal_organization_diagram.xml
- `portal_reports` → portal_reports.xml
- `portal_reports_activity` → portal_missing_templates.xml
- `portal_reports_compliance` → portal_missing_templates.xml
- `portal_reports_export` → portal_missing_templates.xml
- `portal_request_detail` → portal_requests_template.xml
- `portal_requests_template` → portal_requests_template.xml
- `portal_retrieval_cart` → portal_retrieval_cart.xml
- `portal_scheduled_services` → portal_shredding_dashboard.xml
- `portal_service_attachment_detail` → portal_service_photos.xml
- `portal_service_attachments` → portal_service_photos.xml
- `portal_service_detail` → portal_shredding_dashboard.xml
- `portal_shredding_bin_detail` → portal_shredding_bins.xml
- `portal_shredding_bins` → portal_shredding_dashboard.xml
- `portal_shredding_certificates` → portal_shredding_dashboard.xml
- `portal_shredding_dashboard` → portal_shredding_dashboard.xml
- `portal_shredding_history` → portal_shredding_history.xml
- `portal_staging_location_create` → portal_staging_location_forms.xml
- `portal_staging_location_detail` → portal_staging_location_forms.xml
- `portal_staging_locations` → portal_staging_locations.xml
- `portal_stock_movements` → portal_template_aliases.xml
- `portal_work_order_detail` → portal_work_order_templates.xml

### Inherit (extend other templates)

- `portal_breadcrumbs_admin_switch` → portal_access_templates.xml
- `portal_breadcrumbs_work_orders` → portal_work_order_templates.xml
- `portal_my_containers_bulk` → portal_bulk_actions.xml
- `portal_my_home_inventory` → my_portal_inventory.xml
- `portal_my_home_menu_retrieval` → portal_document_retrieval.xml
- `portal_my_home_menu_work_orders` → portal_work_order_templates.xml
- `portal_my_home_preconfigured` → portal_home_preconfigured.xml
- `portal_organization_menu` → portal_organization_diagram.xml
