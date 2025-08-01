# COMPREHENSIVE RECORDS MANAGEMENT MODULE SCAN REPORT

**Generated:** Fri Aug  1 07:56:49 UTC 2025
**Module Path:** /workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management

## 📊 EXECUTIVE SUMMARY

- **Models:** 103
- **Fields:** 1126
- **Views:** 53
- **Security Rules:** 209
- **Issues Found:** 0
- **Recommendations:** 3

## 🐍 MODELS ANALYSIS

### installer (`installer.py`)
- **Fields:** 7
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### account.move.records.extension (`account_move.py`)
- **Fields:** 8
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### bin.key.history (`bin_key_history.py`)
- **Fields:** 10
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### naid.destruction.record (`naid_destruction_record.py`)
- **Fields:** 8
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### records.advanced.billing.period (`advanced_billing.py`)
- **Fields:** 7
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### records.approval.step (`records_approval_step.py`)
- **Fields:** 17
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### Unknown (`hr_employee.py`)
- **Fields:** 0
- **Inheritance:** []

### field.label.customization (`field_label_customization.py`)
- **Fields:** 11
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### records.container.transfer (`records_container_transfer.py`)
- **Fields:** 8
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### partner.bin.key (`partner_bin_key.py`)
- **Fields:** 49
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### transitory.items (`transitory_items.py`)
- **Fields:** 7
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### revenue.forecaster (`revenue_forecaster.py`)
- **Fields:** 29
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### stock.picking.records.extension (`stock_picking.py`)
- **Fields:** 8
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### records.department.billing.enhanced (`department_billing.py`)
- **Fields:** 8
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### records.chain.of.custody (`records_chain_of_custody.py`)
- **Fields:** 7
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### records.deletion.request.enhanced (`records_deletion_request.py`)
- **Fields:** 8
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### barcode.models.enhanced (`barcode_models.py`)
- **Fields:** 8
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### barcode.product (`barcode_product.py`)
- **Fields:** 8
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### naid.compliance (`naid_compliance.py`)
- **Fields:** 8
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### survey.user.input.enhanced (`survey_user_input.py`)
- **Fields:** 8
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### records.management.base.menus (`records_management_base_menus.py`)
- **Fields:** 13
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### survey.improvement.action (`survey_improvement_action.py`)
- **Fields:** 11
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### records.container (`records_container.py`)
- **Fields:** 10
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### records.billing.service (`billing_automation.py`)
- **Fields:** 9
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### document.retrieval.work.order (`document_retrieval_work_order.py`)
- **Fields:** 11
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### shredding.hard_drive (`shredding_hard_drive.py`)
- **Fields:** 8
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### shredding.rates (`shredding_rates.py`)
- **Fields:** 21
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### fsm.notification.placeholder (`fsm_notification.py`)
- **Fields:** 1
- **Inheritance:** []

### ir.module.ext (`ir_module.py`)
- **Fields:** 8
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### records.storage.department.user (`records_storage_department_user.py`)
- **Fields:** 8
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### shredding.service.log (`shredding_service_log.py`)
- **Fields:** 11
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### paper.bale (`paper_bale.py`)
- **Fields:** 6
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### records.location (`records_location.py`)
- **Fields:** 9
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### stock.report_reception_report_label (`ir_actions_report.py`)
- **Fields:** 8
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### Unknown (`res_config_settings.py`)
- **Fields:** 0
- **Inheritance:** []

### paper.bale.recycling (`paper_bale_recycling.py`)
- **Fields:** 11
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### mobile.bin.key.wizard (`mobile_bin_key_wizard.py`)
- **Fields:** 40
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### photo (`photo.py`)
- **Fields:** 11
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### scrm.records.management (`scrm_records_management.py`)
- **Fields:** 8
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### records.billing.config (`billing_models.py`)
- **Fields:** 8
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### records.location.inspection (`records_location_inspection.py`)
- **Fields:** 8
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### records.digital.scan (`records_digital_scan.py`)
- **Fields:** 33
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### bin.unlock.service (`bin_unlock_service.py`)
- **Fields:** 11
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### destruction.item (`destruction_item.py`)
- **Fields:** 11
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### naid.chain.custody (`naid_custody.py`)
- **Fields:** 8
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### naid.audit.log (`naid_audit.py`)
- **Fields:** 8
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### container.contents (`container_contents.py`)
- **Fields:** 11
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### stock.lot.attribute (`stock_lot.py`)
- **Fields:** 8
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### prod.ext (`product.py`)
- **Fields:** 8
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### shredding.picklist.item (`shredding_inventory.py`)
- **Fields:** 8
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### paper.load.shipment (`paper_load_shipment.py`)
- **Fields:** 11
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### shredding.bin (`shredding_bin_models.py`)
- **Fields:** 8
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### records_management.bale (`bale.py`)
- **Fields:** 8
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### records.billing (`billing.py`)
- **Fields:** 23
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### res.partner.key.restriction (`res_partner_key_restriction.py`)
- **Fields:** 7
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### naid.audit.log (`naid_audit_log.py`)
- **Fields:** 8
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### fsm.task.placeholder (`fsm_task.py`)
- **Fields:** 1
- **Inheritance:** []

### records.approval.workflow (`records_approval_workflow.py`)
- **Fields:** 8
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### visitor (`visitor.py`)
- **Fields:** 26
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### survey.feedback.theme (`survey_feedback_theme.py`)
- **Fields:** 8
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### portal.request (`portal_request.py`)
- **Fields:** 11
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### shredding.service (`shredding_service.py`)
- **Fields:** 13
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### naid.performance.history (`naid_performance_history.py`)
- **Fields:** 8
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### work.order.shredding (`work_order_shredding.py`)
- **Fields:** 9
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### hr.emp.naid (`hr_employee_naid.py`)
- **Fields:** 8
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### records.security.audit (`records_security_audit.py`)
- **Fields:** 8
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### records.retention.policy (`records_retention_policy.py`)
- **Fields:** 11
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### records.billing.contact (`customer_billing_profile.py`)
- **Fields:** 11
- **Inheritance:** []

### bin.key.management (`bin_key_management.py`)
- **Fields:** 11
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### records.vehicle (`records_vehicle.py`)
- **Fields:** 26
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### Unknown (`pos_config.py`)
- **Fields:** 0
- **Inheritance:** []

### wizard.template (`wizard_template.py`)
- **Fields:** 1
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### unlock.service.history (`unlock_service_history.py`)
- **Fields:** 10
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### stock.move.sms.validation (`stock_move_sms_validation.py`)
- **Fields:** 4
- **Inheritance:** []

### records.access.log (`records_access_log.py`)
- **Fields:** 8
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### customer.rate.profile (`customer_rate_profile.py`)
- **Fields:** 7
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### portal.feedback (`portal_feedback.py`)
- **Fields:** 11
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### pickup.request.item (`pickup_request_item.py`)
- **Fields:** 8
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### records.document (`records_document.py`)
- **Fields:** 12
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### temp.inventory (`temp_inventory.py`)
- **Fields:** 11
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### naid.compliance.checklist (`naid_compliance_checklist.py`)
- **Fields:** 8
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### Unknown (`res_partner.py`)
- **Fields:** 0
- **Inheritance:** []

### records.audit.log (`records_audit_log.py`)
- **Fields:** 8
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### customer.inventory (`customer_inventory.py`)
- **Fields:** 50
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### load (`load.py`)
- **Fields:** 11
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### file.retrieval.work.order (`file_retrieval_work_order.py`)
- **Fields:** 11
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### customer.retrieval.rates (`customer_retrieval_rates.py`)
- **Fields:** 11
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### records.tag (`records_tag.py`)
- **Fields:** 11
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### naid.custody.event (`naid_custody_event.py`)
- **Fields:** 8
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### records.department.billing.contact (`records_department_billing_contact.py`)
- **Fields:** 8
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### proj.task.ext (`project_task.py`)
- **Fields:** 8
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### pickup.request (`pickup_request.py`)
- **Fields:** 11
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### fsm.route.management.placeholder (`fsm_route_management.py`)
- **Fields:** 1
- **Inheritance:** []

### pickup.route (`pickup_route.py`)
- **Fields:** 12
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### location.report.wizard (`location_report_wizard.py`)
- **Fields:** 18
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### naid.certificate (`naid_certificate.py`)
- **Fields:** 11
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### records.document.type (`records_document_type.py`)
- **Fields:** 31
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### records.container.movement (`records_container_movement.py`)
- **Fields:** 7
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### transitory.field.config (`transitory_field_config.py`)
- **Fields:** 7
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### customer.feedback (`customer_feedback.py`)
- **Fields:** 18
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### records.department (`records_department.py`)
- **Fields:** 14
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### customer.inventory.report (`customer_inventory_report.py`)
- **Fields:** 8
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

### records.policy.version (`records_policy_version.py`)
- **Fields:** 8
- **Inheritance:** ['mail.thread', 'mail.activity.mixin']

## 🏷️ FIELD TYPES DISTRIBUTION

- **Char:** 257
- **Many2one:** 222
- **Text:** 167
- **Selection:** 129
- **Boolean:** 113
- **Date:** 77
- **Datetime:** 54
- **Float:** 45
- **Integer:** 35
- **One2many:** 25
- **Many2many:** 1
- **Binary:** 1

## 💡 RECOMMENDATIONS

### MEDIUM: Add mail.thread inheritance
9 models lack mail.thread inheritance for tracking

**Affected items:**
- hr_employee.py
- fsm.notification.placeholder
- res_config_settings.py
- fsm.task.placeholder
- records.billing.contact
- pos_config.py
- stock.move.sms.validation
- res_partner.py
- fsm.route.management.placeholder

### HIGH: Add @api.depends decorators
55 compute methods missing @api.depends decorators

**Affected items:**
- installer._compute_display_name
- bin.key.history._compute_display_name
- records.advanced.billing.period._compute_price_total
- hr_employee.py._compute_display_name
- field.label.customization._compute_display_name
- partner.bin.key._compute_active_bin_key_count
- partner.bin.key._compute_total_bin_keys_issued
- partner.bin.key._compute_total_unlock_charges
- partner.bin.key._compute_unlock_service_count
- transitory.items._compute_display_name
- ... and 45 more

### HIGH: Add missing security rules
22 models lack access control rules

**Affected items:**
- scrm.records.management
- customer.inventory.report
- file.retrieval.work.order
- naid.compliance
- stock.report_reception_report_label
- stock.lot.attribute
- naid.destruction.record
- wizard.template
- survey.user.input.enhanced
- stock.picking.records.extension
- ... and 12 more

## 🔗 DEPENDENCIES ANALYSIS

**Manifest Dependencies:** 15
**External References:** 5
**Potential Missing Dependencies:** 2

