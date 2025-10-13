# Views and JavaScript Files Outline
## Records Management & Records Management FSM Modules

**Generated:** 2025-10-13  
**Odoo Version:** 18.0  
**Total View Files:** 305 (296 in records_management, 9 in records_management_fsm)  
**Total JavaScript Files:** 30 in records_management, 2 in records_management_fsm

---

## Table of Contents
1. [Module Overview](#module-overview)
2. [Records Management Module](#records-management-module)
   - [View Files (296)](#view-files-records_management)
   - [JavaScript Files (30)](#javascript-files-records_management)
3. [Records Management FSM Module](#records-management-fsm-module)
   - [View Files (9)](#view-files-records_management_fsm)
   - [JavaScript Files (2)](#javascript-files-records_management_fsm)
4. [Dependencies & Configuration](#dependencies--configuration)
5. [Integration Points](#integration-points)
6. [Development Guidelines](#development-guidelines)

---

## Module Overview

### Records Management (`records_management`)
**Purpose:** Complete Enterprise Records Management System with NAID AAA Compliance  
**Category:** Document Management  
**License:** LGPL-3  

**Key Features:**
- Physical & digital records lifecycle management
- NAID AAA + ISO 15489 compliance
- Portal integration for customer access
- Shredding, retention, and audit capabilities
- Billing and invoicing systems
- Barcode management and tracking
- Container and location management
- Chain of custody tracking

### Records Management FSM (`records_management_fsm`)
**Purpose:** Field Service Management integration for Records Management  
**Category:** Records Management  
**License:** LGPL-3  

**Key Features:**
- FSM task integration
- Fleet management integration
- Mobile FSM integration
- Notification management
- Reschedule wizards
- Service line tracking

---

## Records Management Module

### View Files (records_management)

Total: **296 XML view files**

#### Accounting & Billing Views (42 files)

1. **account_move_line_views.xml**
   - Purpose: Account move line customizations for records management
   - Dependencies: account module
   - Models: account.move.line

2. **advanced_billing_contact_views.xml**
   - Purpose: Advanced billing contact management
   - Models: advanced.billing.contact

3. **advanced_billing_line_actions_menus.xml**
   - Purpose: Menu items and actions for billing lines
   - Dependencies: Billing line views

4. **advanced_billing_line_form_views.xml**
   - Purpose: Form views for advanced billing lines
   - Models: advanced.billing.line

5. **advanced_billing_line_search_views.xml**
   - Purpose: Search/filter views for billing lines
   - Models: advanced.billing.line

6. **advanced_billing_line_tree_views.xml**
   - Purpose: List/tree views for billing lines
   - Models: advanced.billing.line

7. **advanced_billing_profile_views.xml**
   - Purpose: Billing profile configuration
   - Models: advanced.billing.profile

8. **billing_period_views.xml**
   - Purpose: Billing period management
   - Models: billing.period

9. **customer_negotiated_rate_views.xml**
   - Purpose: Customer-specific negotiated rates
   - Models: customer.negotiated.rate

10. **customer_negotiated_rates_views.xml**
    - Purpose: Negotiated rates list and management
    - Models: customer.negotiated.rate

11. **departmental_billing_menus.xml**
    - Purpose: Department-based billing menu structure
    - Dependencies: Department and billing views

12. **invoice_generation_log_views.xml**
    - Purpose: Invoice generation tracking and logs
    - Models: invoice.generation.log

13. **payment_split_line_views.xml**
    - Purpose: Payment split line items
    - Models: payment.split.line

14. **payment_split_views.xml**
    - Purpose: Payment splitting functionality
    - Models: payment.split

15. **records_billing_config_views.xml**
    - Purpose: Billing system configuration
    - Models: records.billing.config

16. **records_billing_rate_views.xml**
    - Purpose: Billing rate definitions
    - Models: records.billing.rate

17. **records_billing_views.xml**
    - Purpose: Main billing record views
    - Models: records.billing

18. **records_customer_billing_profile_views.xml**
    - Purpose: Customer-specific billing profiles
    - Models: records.customer.billing.profile

19. **records_department_billing_approval_views.xml**
    - Purpose: Department billing approval workflow
    - Models: records.department.billing.approval

20. **records_department_billing_contact_views.xml**
    - Purpose: Department billing contact management
    - Models: records.department.billing.contact

21. **records_promotional_discount_views.xml**
    - Purpose: Promotional discount management
    - Models: records.promotional.discount

22. **revenue_analytic_views.xml**
    - Purpose: Revenue analytics and reporting
    - Models: revenue.analytic

23. **revenue_forecast_line_views.xml**
    - Purpose: Revenue forecast line items
    - Models: revenue.forecast.line

24. **revenue_forecast_views.xml**
    - Purpose: Revenue forecasting views
    - Models: revenue.forecast

25. **revenue_forecaster_views.xml**
    - Purpose: Revenue forecasting tool
    - Models: revenue.forecaster

26. **base_rate_views.xml**
    - Purpose: Base rate definitions
    - Models: base.rate

27. **base_rates_views.xml**
    - Purpose: Base rates management
    - Models: base.rates

28. **discount_rule_views.xml**
    - Purpose: Discount rule configuration
    - Models: discount.rule

29. **shredding_rate_views.xml**
    - Purpose: Shredding service rates
    - Models: shredding.rate

30-42. **Additional billing-related views** (rate management, approval workflows, etc.)

#### Barcode & Inventory Views (18 files)

43. **barcode_generation_history_views.xml**
    - Purpose: Track barcode generation history
    - Models: barcode.generation.history

44. **barcode_menus.xml**
    - Purpose: Barcode system menu structure
    - Dependencies: Barcode views

45. **barcode_models_enhanced_views.xml**
    - Purpose: Enhanced barcode model views
    - Models: Multiple barcode models

46. **barcode_pricing_tier_views.xml**
    - Purpose: Barcode pricing tier management
    - Models: barcode.pricing.tier

47. **barcode_product_views.xml**
    - Purpose: Barcode product integration
    - Models: barcode.product
    - Dependencies: product module

48. **barcode_seasonal_pricing_views.xml**
    - Purpose: Seasonal pricing for barcodes
    - Models: barcode.seasonal.pricing

49. **barcode_storage_box_views.xml**
    - Purpose: Storage box barcode management
    - Models: barcode.storage.box

50. **bin_barcode_inventory_views.xml**
    - Purpose: Bin barcode inventory tracking
    - Models: bin.barcode.inventory

51. **bin_issue_report_wizard_views.xml**
    - Purpose: Bin issue reporting wizard
    - Models: bin.issue.report.wizard

52. **bin_key_history_views.xml**
    - Purpose: Bin key access history
    - Models: bin.key.history

53. **bin_key_unlock_service_views.xml**
    - Purpose: Bin key unlock service management
    - Models: bin.key.unlock.service

54. **bin_key_views.xml**
    - Purpose: Bin key management
    - Models: bin.key

55. **bin_unlock_service_views.xml**
    - Purpose: Unlock service tracking
    - Models: bin.unlock.service

56. **key_inventory_views.xml**
    - Purpose: Key inventory management
    - Models: key.inventory

57. **key_restriction_checker_views.xml**
    - Purpose: Key restriction validation
    - Models: key.restriction.checker

58. **serial_number_views.xml**
    - Purpose: Serial number tracking
    - Models: serial.number

59. **shredding_bin_barcode_wizard_views.xml**
    - Purpose: Shredding bin barcode generation wizard
    - Models: shredding.bin.barcode.wizard

60. **records_storage_box_views.xml**
    - Purpose: Storage box management
    - Models: records.storage.box

#### Container Management Views (28 files)

61. **container_access_activity_views.xml**
    - Purpose: Container access activity logging
    - Models: container.access.activity

62. **container_access_document_views.xml**
    - Purpose: Container access documentation
    - Models: container.access.document

63. **container_access_photo_views.xml**
    - Purpose: Container access photo management
    - Models: container.access.photo

64. **container_access_report_views.xml**
    - Purpose: Container access reporting
    - Models: container.access.report

65. **container_access_visitor_views.xml**
    - Purpose: Container visitor access tracking
    - Models: container.access.visitor

66. **container_access_work_order_views.xml**
    - Purpose: Container access work orders
    - Models: container.access.work.order

67. **container_content_views.xml**
    - Purpose: Container content management
    - Models: container.content

68. **container_destruction_work_order_views.xml**
    - Purpose: Container destruction work orders
    - Models: container.destruction.work.order

69. **container_retrieval_item_views.xml**
    - Purpose: Container retrieval item tracking
    - Models: container.retrieval.item

70. **container_retrieval_views.xml**
    - Purpose: Container retrieval management
    - Models: container.retrieval

71. **container_retrieval_work_order_views.xml**
    - Purpose: Container retrieval work orders
    - Models: container.retrieval.work.order

72. **records_container_content_views.xml**
    - Purpose: Records container content
    - Models: records.container.content

73. **records_container_line_views.xml**
    - Purpose: Container line items
    - Models: records.container.line

74. **records_container_log_views.xml**
    - Purpose: Container activity logs
    - Models: records.container.log

75. **records_container_movement_views.xml**
    - Purpose: Container movement tracking
    - Models: records.container.movement

76. **records_container_transfer_views.xml**
    - Purpose: Container transfer management
    - Models: records.container.transfer

77. **records_container_views.xml**
    - Purpose: Main container management views
    - Models: records.container
    - Key Features: NAID compliance, barcode integration, location tracking

78-88. **Additional container-related views** (types, configurations, workflows, etc.)

#### Chain of Custody & Audit Views (12 files)

89. **chain_of_custody_event_views.xml**
    - Purpose: Chain of custody event tracking
    - Models: chain.of.custody.event

90. **chain_of_custody_views.xml**
    - Purpose: Main chain of custody management
    - Models: chain.of.custody
    - Key Features: NAID AAA compliance, audit trails

91. **custody_transfer_event_views.xml**
    - Purpose: Custody transfer event logging
    - Models: custody.transfer.event

92. **naid_audit_log_views.xml**
    - Purpose: NAID audit log management
    - Models: naid.audit.log

93. **naid_compliance_action_plan_views.xml**
    - Purpose: NAID compliance action plans
    - Models: naid.compliance.action.plan

94. **naid_compliance_alert_views.xml**
    - Purpose: NAID compliance alerts
    - Models: naid.compliance.alert

95. **naid_compliance_report_views.xml**
    - Purpose: NAID compliance reporting
    - Models: naid.compliance.report

96. **records_audit_log_views.xml**
    - Purpose: General records audit logs
    - Models: records.audit.log

97. **records_security_audit_views.xml**
    - Purpose: Security audit tracking
    - Models: records.security.audit

98. **signed_document_audit_views.xml**
    - Purpose: Signed document audit trail
    - Models: signed.document.audit

99. **signed_document_views.xml**
    - Purpose: Signed document management
    - Models: signed.document

100. **records_access_log_views.xml**
     - Purpose: Records access logging
     - Models: records.access.log

#### Destruction & Certificate Views (8 files)

101. **certificate_template_data_views.xml**
     - Purpose: Certificate template management
     - Models: certificate.template.data

102. **destruction_certificate_views.xml**
     - Purpose: Destruction certificate management
     - Models: destruction.certificate
     - Key Features: NAID compliance, legal documentation

103. **destruction_event_views.xml**
     - Purpose: Destruction event tracking
     - Models: destruction.event

104. **destruction_item_views.xml**
     - Purpose: Destruction item management
     - Models: destruction.item

105. **shredding_certificate_views.xml**
     - Purpose: Shredding certificate generation
     - Models: shredding.certificate

106. **inventory_item_destruction_line_views.xml**
     - Purpose: Inventory item destruction lines
     - Models: inventory.item.destruction.line

107. **inventory_item_destruction_views.xml**
     - Purpose: Inventory item destruction management
     - Models: inventory.item.destruction

108. **records_deletion_request_enhanced_views.xml**
     - Purpose: Enhanced deletion request workflow
     - Models: records.deletion.request

#### Document Retrieval Views (16 files)

109. **document_retrieval_item_views.xml**
     - Purpose: Document retrieval item tracking
     - Models: document.retrieval.item

110. **document_retrieval_menus.xml**
     - Purpose: Document retrieval menu structure
     - Dependencies: Document retrieval views

111. **document_retrieval_metrics_views.xml**
     - Purpose: Document retrieval metrics and KPIs
     - Models: document.retrieval.metrics

112. **document_retrieval_team_views.xml**
     - Purpose: Document retrieval team management
     - Models: document.retrieval.team

113. **document_search_attempt_views.xml**
     - Purpose: Document search attempt tracking
     - Models: document.search.attempt

114. **file_retrieval_item_views.xml**
     - Purpose: File retrieval item management
     - Models: file.retrieval.item

115. **file_retrieval_views.xml**
     - Purpose: File retrieval operations
     - Models: file.retrieval

116. **retrieval_item_base_views.xml**
     - Purpose: Base retrieval item functionality
     - Models: retrieval.item.base

117. **retrieval_metric_views.xml**
     - Purpose: Retrieval metrics tracking
     - Models: retrieval.metric

118. **records_retrieval_order_views.xml**
     - Purpose: Records retrieval order management
     - Models: records.retrieval.order

119. **records_retrieval_work_order_menus.xml**
     - Purpose: Retrieval work order menus
     - Dependencies: Work order views

120. **records_retrieval_work_order_views.xml**
     - Purpose: Retrieval work order management
     - Models: records.retrieval.work.order

121. **scan_retrieval_item_views.xml**
     - Purpose: Scan retrieval item tracking
     - Models: scan.retrieval.item

122. **scan_retrieval_views.xml**
     - Purpose: Scan retrieval operations
     - Models: scan.retrieval

123. **scan_retrieval_work_order_views.xml**
     - Purpose: Scan retrieval work orders
     - Models: scan.retrieval.work.order

124. **work_order_retrieval_views.xml**
     - Purpose: General work order retrieval
     - Models: work.order.retrieval

#### Portal & Customer Views (26 files)

125. **customer_category_views.xml**
     - Purpose: Customer category management
     - Models: customer.category

126. **customer_feedback_views.xml**
     - Purpose: Customer feedback collection
     - Models: customer.feedback

127. **customer_inventory_line_views.xml**
     - Purpose: Customer inventory line items
     - Models: customer.inventory.line

128. **customer_inventory_report_line_views.xml**
     - Purpose: Customer inventory report lines
     - Models: customer.inventory.report.line

129. **customer_inventory_report_views.xml**
     - Purpose: Customer inventory reporting
     - Models: customer.inventory.report

130. **customer_inventory_report_wizard_views.xml**
     - Purpose: Customer inventory report wizard
     - Models: customer.inventory.report.wizard

131. **customer_inventory_views.xml**
     - Purpose: Customer inventory management
     - Models: customer.inventory

132. **customer_portal_diagram_views.xml**
     - Purpose: Customer portal diagram visualization
     - Models: customer.portal.diagram
     - Dependencies: vis.js library

133. **portal_feedback_escalation_views.xml**
     - Purpose: Portal feedback escalation workflow
     - Models: portal.feedback.escalation

134. **portal_feedback_resolution_views.xml**
     - Purpose: Portal feedback resolution tracking
     - Models: portal.feedback.resolution

135. **portal_feedback_views.xml**
     - Purpose: Portal feedback management
     - Models: portal.feedback

136. **portal_request_line_views.xml**
     - Purpose: Portal request line items
     - Models: portal.request.line

137. **portal_request_views.xml**
     - Purpose: Portal request management
     - Models: portal.request

138. **records_request_line_views.xml**
     - Purpose: Records request line items
     - Models: records.request.line

139. **records_request_type_views.xml**
     - Purpose: Records request type configuration
     - Models: records.request.type

140. **records_request_views.xml**
     - Purpose: Records request management
     - Models: records.request

141. **visitor_pos_wizard_views.xml**
     - Purpose: Visitor POS wizard
     - Models: visitor.pos.wizard

142. **visitor_views.xml**
     - Purpose: Visitor management
     - Models: visitor

143. **records_user_invitation_wizard_views.xml**
     - Purpose: User invitation wizard
     - Models: records.user.invitation.wizard

144-150. **Additional portal views** (notifications, dashboards, etc.)

#### Shredding Service Views (18 files)

151. **shred_bin_views.xml**
     - Purpose: Shred bin management
     - Models: shred.bin

152. **shred_model_bin_views.xml**
     - Purpose: Shred model bin definitions
     - Models: shred.model.bin

153. **shredding_bin_views.xml**
     - Purpose: Shredding bin tracking
     - Models: shredding.bin

154. **shredding_hard_drive_views.xml**
     - Purpose: Hard drive shredding management
     - Models: shredding.hard.drive

155. **shredding_inventory_batch_views.xml**
     - Purpose: Shredding inventory batch processing
     - Models: shredding.inventory.batch

156. **shredding_inventory_views.xml**
     - Purpose: Shredding inventory management
     - Models: shredding.inventory

157. **shredding_service_bin_views.xml**
     - Purpose: Shredding service bin tracking
     - Models: shredding.service.bin

158. **shredding_service_event_views.xml**
     - Purpose: Shredding service event logging
     - Models: shredding.service.event

159. **shredding_service_log_views.xml**
     - Purpose: Shredding service activity logs
     - Models: shredding.service.log

160. **shredding_service_photo_views.xml**
     - Purpose: Shredding service photo documentation
     - Models: shredding.service.photo

161. **shredding_service_views.xml**
     - Purpose: Main shredding service views
     - Models: shredding.service

162. **shredding_team_views.xml**
     - Purpose: Shredding team management
     - Models: shredding.team

163. **work_order_shredding_views.xml**
     - Purpose: Shredding work order management
     - Models: work.order.shredding

164. **hard_drive_scan_wizard_line_views.xml**
     - Purpose: Hard drive scan wizard lines
     - Models: hard.drive.scan.wizard.line

165. **hard_drive_scan_wizard_views.xml**
     - Purpose: Hard drive scanning wizard
     - Models: hard.drive.scan.wizard

166-168. **Additional shredding views** (schedules, reports, etc.)

#### Location & Facility Views (14 files)

169. **location_group_views.xml**
     - Purpose: Location group management
     - Models: location.group

170. **location_report_wizard_views.xml**
     - Purpose: Location reporting wizard
     - Models: location.report.wizard

171. **records_center_location_views.xml**
     - Purpose: Records center location management
     - Models: records.center.location

172. **records_location_views.xml**
     - Purpose: Records location tracking
     - Models: records.location

173. **inventory_item_location_transfer_views.xml**
     - Purpose: Location transfer for inventory items
     - Models: inventory.item.location.transfer

174. **route_optimizer_views.xml**
     - Purpose: Route optimization for retrievals
     - Models: route.optimizer

175. **pickup_route_views.xml**
     - Purpose: Pickup route planning
     - Models: pickup.route

176. **mobile_photo_views.xml**
     - Purpose: Mobile photo management
     - Models: mobile.photo

177-182. **Additional location views** (zones, capacity, etc.)

#### Paper & Load Management Views (12 files)

183. **load_views.xml**
     - Purpose: Load management (paper bales)
     - Models: paper.bale.load

184. **paper_bale_load_truck_views.xml**
     - Purpose: Paper bale load truck tracking
     - Models: paper.bale.load.truck

185. **paper_bale_movement_views.xml**
     - Purpose: Paper bale movement tracking
     - Models: paper.bale.movement

186. **paper_bale_views.xml**
     - Purpose: Paper bale management
     - Models: paper.bale

187. **paper_load_shipment_views.xml**
     - Purpose: Paper load shipment tracking
     - Models: paper.load.shipment

188. **paper_model_bale_views.xml**
     - Purpose: Paper model bale definitions
     - Models: paper.model.bale

189. **records_management_bale_views.xml**
     - Purpose: Records management bale integration
     - Models: records.management.bale

190-194. **Additional paper management views** (pricing, processing, etc.)

#### Inventory & Stock Views (16 files)

195. **inventory_adjustment_reason_views.xml**
     - Purpose: Inventory adjustment reason tracking
     - Models: inventory.adjustment.reason

196. **inventory_item_profile_views.xml**
     - Purpose: Inventory item profile management
     - Models: inventory.item.profile

197. **inventory_item_retrieval_line_views.xml**
     - Purpose: Inventory item retrieval lines
     - Models: inventory.item.retrieval.line

198. **inventory_item_retrieval_views.xml**
     - Purpose: Inventory item retrieval operations
     - Models: inventory.item.retrieval

199. **inventory_item_type_views.xml**
     - Purpose: Inventory item type configuration
     - Models: inventory.item.type

200. **inventory_item_views.xml**
     - Purpose: Main inventory item views
     - Models: inventory.item

201. **stock_lot_attribute_option_views.xml**
     - Purpose: Stock lot attribute options
     - Models: stock.lot.attribute.option
     - Dependencies: stock module

202. **stock_lot_attribute_value_views.xml**
     - Purpose: Stock lot attribute values
     - Models: stock.lot.attribute.value

203. **stock_lot_attribute_views.xml**
     - Purpose: Stock lot attributes
     - Models: stock.lot.attribute

204. **stock_lot_views.xml**
     - Purpose: Stock lot management
     - Models: stock.lot

205. **stock_move_sms_validation_views.xml**
     - Purpose: SMS validation for stock moves
     - Models: stock.move.sms.validation

206. **stock_picking_records_extension_views.xml**
     - Purpose: Records extension for stock picking
     - Models: stock.picking

207. **temp_inventory_reject_wizard_views.xml**
     - Purpose: Temporary inventory rejection wizard
     - Models: temp.inventory.reject.wizard

208. **temp_inventory_views.xml**
     - Purpose: Temporary inventory management
     - Models: temp.inventory

209. **transitory_field_config_views.xml**
     - Purpose: Transitory field configuration
     - Models: transitory.field.config

210. **transitory_item_views.xml**
     - Purpose: Transitory item management
     - Models: transitory.item

#### Work Order & Task Views (20 files)

211. **work_order_bin_assignment_wizard_views.xml**
     - Purpose: Work order bin assignment wizard
     - Models: work.order.bin.assignment.wizard

212. **work_order_coordinator_views.xml**
     - Purpose: Work order coordinator management
     - Models: work.order.coordinator

213. **work_order_dashboard_views.xml**
     - Purpose: Work order dashboard
     - Models: work.order.dashboard

214. **mobile_work_order_views.xml**
     - Purpose: Mobile work order management
     - Models: mobile.work.order

215. **project_task_views.xml**
     - Purpose: Project task integration
     - Models: project.task
     - Dependencies: project module

216-230. **Additional work order views** (types, assignments, tracking, etc.)

#### Configuration & System Views (30 files)

231. **approval_history_views.xml**
     - Purpose: Approval history tracking
     - Models: approval.history

232. **field_label_helper_wizard_views.xml**
     - Purpose: Field label customization wizard
     - Models: field.label.helper.wizard

233. **full_customization_name_view_form.xml**
     - Purpose: Full customization name form
     - Models: full.customization.name

234. **full_customization_name_views.xml**
     - Purpose: Full customization name management
     - Models: full.customization.name

235. **ir_model_views.xml**
     - Purpose: IR model customizations
     - Models: ir.model

236. **ir_ui_view_views.xml**
     - Purpose: IR UI view customizations
     - Models: ir.ui.view

237. **records_approval_step_views.xml**
     - Purpose: Approval step configuration
     - Models: records.approval.step

238. **records_approval_workflow_line_views.xml**
     - Purpose: Approval workflow lines
     - Models: records.approval.workflow.line

239. **records_approval_workflow_views.xml**
     - Purpose: Approval workflow management
     - Models: records.approval.workflow

240. **records_category_views.xml**
     - Purpose: Records category management
     - Models: records.category

241. **records_policy_version_views.xml**
     - Purpose: Records policy version management
     - Models: records.policy.version

242. **records_retention_policy_version_views.xml**
     - Purpose: Retention policy version tracking
     - Models: records.retention.policy.version

243. **records_retention_policy_views.xml**
     - Purpose: Retention policy management
     - Models: records.retention.policy
     - Key Features: NAID compliance, ISO 15489 compliance

244. **records_retention_rule_views.xml**
     - Purpose: Retention rule configuration
     - Models: records.retention.rule

245. **records_series_views.xml**
     - Purpose: Records series management
     - Models: records.series

246. **records_service_type_views.xml**
     - Purpose: Service type configuration
     - Models: records.service.type

247. **records_tag_category_views.xml**
     - Purpose: Tag category management
     - Models: records.tag.category

248. **records_tag_views.xml**
     - Purpose: Records tag management
     - Models: records.tag

249. **res_config_settings_views.xml**
     - Purpose: System configuration settings
     - Models: res.config.settings
     - Dependencies: base_setup module

250. **res_partner_key_restriction_views.xml**
     - Purpose: Partner key restriction management
     - Models: res.partner.key.restriction

251. **res_partner_views.xml**
     - Purpose: Partner/contact customizations
     - Models: res.partner

252. **res_users_records_profile_views.xml**
     - Purpose: User records profile
     - Models: res.users

253. **rm_module_configurator_views.xml**
     - Purpose: Records management module configurator
     - Models: rm.module.configurator
     - Key Features: Central configuration toggles

254. **system_diagram_data_views.xml**
     - Purpose: System diagram data management
     - Models: system.diagram.data

255. **system_flowchart_wizard_views.xml**
     - Purpose: System flowchart wizard
     - Models: system.flowchart.wizard

256. **wizard_template_views.xml**
     - Purpose: Wizard template base
     - Models: wizard.template

257. **workflow_visualization_manager_views.xml**
     - Purpose: Workflow visualization management
     - Models: workflow.visualization.manager

258-260. **Additional configuration views** (departments, users, profiles, etc.)

#### Menu & Dashboard Views (10 files)

261. **departmental_billing_menus.xml**
     - Purpose: Departmental billing menu structure

262. **document_retrieval_menus.xml**
     - Purpose: Document retrieval menu structure

263. **enhanced_features_menus.xml**
     - Purpose: Enhanced features menu structure

264. **records_management_dashboard_views.xml**
     - Purpose: Main dashboard views
     - Models: records.management.dashboard

265. **records_management_menus.xml**
     - Purpose: Records management menu structure

266. **records_management_root_menus.xml**
     - Purpose: Root menu definitions (loaded first)

267. **records_retrieval_work_order_menus.xml**
     - Purpose: Retrieval work order menus

268. **service_item_menus.xml**
     - Purpose: Service item menus

269. **barcode_menus.xml**
     - Purpose: Barcode system menus

270. **work_order_dashboard_views.xml**
     - Purpose: Work order dashboard

#### Specialized & Integration Views (26 files)

271. **fleet_vehicle_views.xml**
     - Purpose: Fleet vehicle integration
     - Models: fleet.vehicle
     - Dependencies: fleet module

272. **hr_employee_views.xml**
     - Purpose: HR employee integration
     - Models: hr.employee
     - Dependencies: hr module

273. **maintenance_equipment_views.xml**
     - Purpose: Maintenance equipment integration
     - Models: maintenance.equipment
     - Dependencies: maintenance module

274. **pos_config_views.xml**
     - Purpose: Point of sale configuration
     - Models: pos.config
     - Dependencies: point_of_sale module

275. **processing_log_resolution_wizard_views.xml**
     - Purpose: Processing log resolution wizard
     - Models: processing.log.resolution.wizard

276. **processing_log_views.xml**
     - Purpose: Processing log management
     - Models: processing.log

277. **product_container_type_views.xml**
     - Purpose: Product container type
     - Models: product.container.type

278. **product_template_views.xml**
     - Purpose: Product template customizations
     - Models: product.template
     - Dependencies: product module

279. **rate_change_confirmation_wizard_views.xml**
     - Purpose: Rate change confirmation wizard
     - Models: rate.change.confirmation.wizard

280. **records_bulk_user_import_views.xml**
     - Purpose: Bulk user import functionality
     - Models: records.bulk.user.import

281. **records_department_views.xml**
     - Purpose: Records department management
     - Models: records.department

282. **records_permanent_flag_wizard_views.xml**
     - Purpose: Permanent flag wizard
     - Models: records.permanent.flag.wizard

283. **records_storage_department_user_views.xml**
     - Purpose: Storage department user management
     - Models: records.storage.department.user

284. **records_survey_user_input_views.xml**
     - Purpose: Survey user input integration
     - Models: records.survey.user.input
     - Dependencies: survey module

285. **records_usage_tracking_views.xml**
     - Purpose: Usage tracking and analytics
     - Models: records.usage.tracking

286. **records_work_vehicle_views.xml**
     - Purpose: Work vehicle management
     - Models: records.work.vehicle

287. **report_window_actions_views.xml**
     - Purpose: Report window actions configuration
     - Models: Multiple report models

288. **required_document_views.xml**
     - Purpose: Required document management
     - Models: required.document

289. **scan_digital_asset_views.xml**
     - Purpose: Digital asset scanning
     - Models: scan.digital.asset

290. **survey_feedback_theme_views.xml**
     - Purpose: Survey feedback theme configuration
     - Models: survey.feedback.theme

291. **survey_improvement_action_views.xml**
     - Purpose: Survey improvement action tracking
     - Models: survey.improvement.action

292. **unlock_service_history_views.xml**
     - Purpose: Unlock service history tracking
     - Models: unlock.service.history

293. **unlock_service_part_views.xml**
     - Purpose: Unlock service part management
     - Models: unlock.service.part

294. **custom_box_volume_calculator_views.xml**
     - Purpose: Custom box volume calculator
     - Models: custom.box.volume.calculator

295. **feedback_improvement_area_views.xml**
     - Purpose: Feedback improvement area tracking
     - Models: feedback.improvement.area

296. **description_views.xml**
     - Purpose: Description field management
     - Models: Various models

---

### JavaScript Files (records_management)

Total: **30 JavaScript files**

#### Modern Owl Components (4 files)

**Location:** `records_management/static/src/portal_components/`

1. **portal_document_center.js**
   - Purpose: Modern Owl component for portal document center
   - Framework: Owl (Odoo 19+ recommended approach)
   - Features:
     - Reactive state management
     - Component-based architecture
     - Document listing and filtering
     - Export functionality
   - Dependencies: @odoo/owl, @web/core/registry, @web/core/network/rpc
   - Integration: Portal document management

2. **portal_document_center_enhancements.js**
   - Purpose: Supplemental behavior for legacy fallback
   - Framework: Vanilla JavaScript with Owl imports
   - Features:
     - Graceful degradation
     - Legacy support
     - Accordion navigation
     - View switching (tabs/accordion)
     - Export all documents functionality
   - Dependencies: @odoo/owl (onMounted)
   - Integration: Portal document center page

3. **portal_inventory.js**
   - Purpose: Modern interactive inventory management for portal users
   - Framework: Owl Component
   - Class: PortalInventoryComponent
   - Features:
     - Reactive state with useState
     - Item normalization and filtering
     - Client-side search and filtering
     - Sorting (date, name)
     - Bulk selection
     - Status color coding
     - Pagination
   - Dependencies: @odoo/owl (Component, useState, onMounted, onWillUnmount), @web/core/registry, @web/core/network/rpc
   - Registry: "public_components" → "records_management.PortalInventoryComponent"
   - Integration: Portal inventory pages

4. **portal_search.js**
   - Purpose: Portal search functionality (Owl component)
   - Framework: Owl Component
   - Features:
     - Search interface
     - Result filtering
     - Advanced search options
   - Dependencies: @odoo/owl, @web/core/registry
   - Integration: Portal search pages

#### Legacy Portal JavaScript (15 files)

**Location:** `records_management/static/src/js/`

**Note:** These files are marked for gradual migration to Owl components

5. **portal_tour.js**
   - Purpose: Portal tour/walkthrough functionality
   - Framework: Vanilla JavaScript
   - Features:
     - User onboarding
     - Feature highlights
     - Step-by-step guides
   - CSS: portal_tour.css
   - Migration Status: To be migrated to Owl

6. **portal_inventory_highlights.js**
   - Purpose: Inventory highlights and visualization
   - Framework: Vanilla JavaScript
   - Features:
     - Highlight key inventory items
     - Visual indicators
     - Quick stats
   - Migration Status: Being replaced by portal_inventory.js (Owl)

7. **portal_inventory_search.js**
   - Purpose: Portal inventory search functionality
   - Framework: Vanilla JavaScript
   - Features:
     - Search interface
     - Filter controls
     - Results display
   - Migration Status: To be migrated to Owl

8. **portal_quote_generator.js**
   - Purpose: Portal quote generation
   - Framework: Vanilla JavaScript
   - Features:
     - Quote configuration
     - Price calculation
     - Quote generation
   - Migration Status: To be migrated to Owl

9. **portal_signature.js**
   - Purpose: Portal signature capture
   - Framework: Vanilla JavaScript
   - Features:
     - Signature pad integration
     - Signature validation
     - Document signing
   - Dependencies: sign module
   - Migration Status: To be migrated to Owl

10. **portal_user_import.js**
    - Purpose: Portal user import functionality
    - Framework: Vanilla JavaScript
    - Features:
      - CSV file upload
      - User validation
      - Bulk user import
    - Migration Status: To be migrated to Owl

11. **portal_docs.js**
    - Purpose: Portal document management
    - Framework: Vanilla JavaScript
    - Features:
      - Document listing
      - Document filtering
      - Document download
    - Migration Status: Being replaced by portal_document_center.js (Owl)

12. **portal_search.js** (legacy version)
    - Purpose: Legacy portal search
    - Framework: Vanilla JavaScript
    - Migration Status: Being replaced by Owl version

13. **intelligent_search.js**
    - Purpose: Intelligent search functionality
    - Framework: Vanilla JavaScript
    - Features:
      - AI-powered search
      - Search suggestions
      - Result ranking
    - CSS: intelligent_search.css
    - Migration Status: To be migrated to Owl

14-19. **Additional portal scripts** (organization diagrams, barcode management, document retrieval)

#### Portal Subdirectory (Externalized Logic) (3 files)

**Location:** `records_management/static/src/js/portal/`

20. **portal_barcode_management.js**
    - Purpose: Portal barcode management logic (extracted from inline script)
    - Framework: Vanilla JavaScript
    - Features:
      - Barcode generation
      - Barcode scanning integration
      - Barcode validation
    - Integration: Portal barcode pages
    - Note: Externalized from inline scripts for better maintainability

21. **portal_document_retrieval.js**
    - Purpose: Portal document retrieval logic
    - Framework: Vanilla JavaScript
    - Features:
      - Document retrieval requests
      - Retrieval status tracking
      - Document download
    - Integration: Portal document retrieval pages
    - Note: Externalized from inline scripts

22. **portal_organization_diagram.js**
    - Purpose: Organization diagram visualization
    - Framework: Vanilla JavaScript with vis.js
    - Features:
      - Hierarchical organization chart
      - Interactive diagram
      - Node customization
    - Dependencies: vis.js library
    - CSS: customer_portal_diagram.css
    - Integration: Portal organization pages

#### Backend/Business Logic JavaScript (8 files)

**Location:** `records_management/static/src/js/`

23. **customer_portal_diagram.js**
    - Purpose: Customer portal diagram backend logic
    - Framework: Odoo web framework
    - Features:
      - Diagram data generation
      - Relationship mapping
      - Visualization backend
    - Dependencies: vis.js
    - Integration: Backend diagram generation

24. **customer_portal_diagram_view.js**
    - Purpose: Customer portal diagram view widget
    - Framework: Odoo web framework
    - Features:
      - Custom view type
      - Diagram rendering
      - View integration
    - Dependencies: web module

25. **field_label_customizer.js**
    - Purpose: Field label customization widget
    - Framework: Odoo web framework
    - Features:
      - Dynamic label editing
      - Field customization
      - Label persistence
    - Integration: Field customization system

26. **map_widget.js**
    - Purpose: Map widget for location visualization
    - Framework: Odoo web widget
    - Features:
      - Location mapping
      - Interactive maps
      - Marker placement
    - Dependencies: Mapping library (Google Maps/OpenStreetMap)

27. **paper_load_progress_field.js**
    - Purpose: Paper load progress field widget
    - Framework: Odoo web widget
    - Features:
      - Progress visualization
      - Load tracking
      - Visual indicators
    - Integration: Paper load management

28. **paper_load_truck_widget.js**
    - Purpose: Paper load truck visualization widget
    - Framework: Odoo web widget
    - Features:
      - Truck load visualization
      - Capacity display
      - Load distribution
    - Integration: Paper load truck views

29. **truck_widget.js**
    - Purpose: Generic truck widget
    - Framework: Odoo web widget
    - Features:
      - Truck visualization
      - Status display
      - Load information
    - Integration: Fleet and logistics views

30. **trailer_visualization.js**
    - Purpose: Trailer visualization widget
    - Framework: Odoo web widget
    - Features:
      - Trailer status visualization
      - Load display
      - Capacity tracking
    - Integration: Logistics views

#### Specialized Widgets (4 files)

31. **pos_customer_history.js**
    - Purpose: POS customer history widget
    - Framework: Odoo POS framework
    - Features:
      - Customer purchase history
      - Transaction display
      - Customer insights
    - Dependencies: point_of_sale module
    - Integration: POS interface

32. **system_flowchart_view.js**
    - Purpose: System flowchart view
    - Framework: Odoo web framework
    - Features:
      - Flowchart visualization
      - Process mapping
      - Interactive flowcharts
    - Integration: System diagram wizard

33. **visualization_dynamic_loader.js**
    - Purpose: Dynamic loader for visualization libraries
    - Framework: Odoo web framework
    - Features:
      - Lazy loading
      - Library management
      - Resource optimization
    - Integration: All visualization components

#### External Libraries (2 files)

**Location:** `records_management/static/src/lib/vis/`

34. **vis-network.js**
    - Purpose: Vis.js network library (full version)
    - Type: Third-party library
    - Version: Latest compatible version
    - Usage: Organization diagrams, network visualizations
    - License: Apache-2.0 / MIT

35. **vis-network.min.js**
    - Purpose: Vis.js network library (minified)
    - Type: Third-party library (production version)
    - Usage: Production deployments

---

## Records Management FSM Module

### View Files (records_management_fsm)

Total: **9 XML view files**

#### FSM Integration Views (9 files)

1. **enhanced_fsm_integration_views.xml**
   - Purpose: Enhanced FSM integration views
   - Models: enhanced.fsm.integration
   - Features:
     - FSM task integration
     - Enhanced field service features
     - Records management integration
   - Dependencies: project, industry_fsm (optional)

2. **fleet_fsm_integration_menus.xml**
   - Purpose: Fleet FSM integration menu structure
   - Dependencies: fleet, fsm views
   - Features:
     - Fleet management menus
     - FSM task menus
     - Vehicle assignment menus

3. **fsm_notification_manager_views.xml**
   - Purpose: FSM notification manager views
   - Models: fsm.notification.manager
   - Features:
     - Notification configuration
     - Alert management
     - Notification rules

4. **fsm_notification_views.xml**
   - Purpose: FSM notification views
   - Models: fsm.notification
   - Features:
     - Notification listing
     - Notification details
     - Notification history

5. **fsm_reschedule_wizard_placeholder_views.xml**
   - Purpose: FSM reschedule wizard placeholder
   - Models: fsm.reschedule.wizard.placeholder
   - Features:
     - Placeholder for reschedule functionality
     - Future expansion point

6. **fsm_reschedule_wizard_views.xml**
   - Purpose: FSM reschedule wizard
   - Models: fsm.reschedule.wizard
   - Features:
     - Task rescheduling
     - Date/time selection
     - Resource reallocation

7. **fsm_task_service_line_views.xml**
   - Purpose: FSM task service line views
   - Models: fsm.task.service.line
   - Features:
     - Service line items
     - Task breakdown
     - Service tracking

8. **fsm_task_views.xml**
   - Purpose: FSM task views
   - Models: fsm.task (extends project.task)
   - Features:
     - FSM-specific task fields
     - Field service integration
     - Task management

9. **mobile_fsm_integration_views.xml**
   - Purpose: Mobile FSM integration views
   - Models: mobile.fsm.integration
   - Features:
     - Mobile interface
     - Field technician views
     - Offline capability support

### JavaScript Files (records_management_fsm)

Total: **2 JavaScript files** (in assets)

**Location:** `records_management_fsm/static/src/js/`

1. **fleet_fsm_dashboard.js**
   - Purpose: Fleet FSM dashboard component
   - Framework: Odoo web framework
   - Features:
     - Fleet overview
     - FSM task integration
     - Vehicle status display
     - Task assignment visualization
   - Dependencies: fleet, project modules
   - Template: fleet_fsm_dashboard.xml
   - Integration: Backend dashboard

**Location:** `records_management_fsm/static/src/xml/`

2. **fleet_fsm_dashboard.xml**
   - Purpose: Fleet FSM dashboard template
   - Type: QWeb template
   - Features:
     - Dashboard layout
     - Widget templates
     - Data visualization templates
   - Integration: fleet_fsm_dashboard.js

---

## Dependencies & Configuration

### Records Management Module Dependencies

#### Core Odoo Modules (Always Available)
- **base**: Foundation framework
- **mail**: Email and messaging
- **web**: Web client framework
- **product**: Product management
- **stock**: Inventory and warehouse management
- **account**: Accounting and invoicing
- **sale**: Sales management
- **portal**: Customer portal
- **website**: Website builder
- **contacts**: Contact management
- **calendar**: Calendar and scheduling
- **hr**: Human resources
- **project**: Project management
- **fleet**: Fleet management
- **crm**: Customer relationship management
- **purchase**: Purchase management
- **repair**: Repair management
- **board**: Dashboard framework
- **resource**: Resource management
- **web_tour**: User tours
- **utm**: UTM tracking
- **digest**: Digest emails
- **rating**: Rating system
- **bus**: Real-time messaging bus
- **http_routing**: HTTP routing
- **base_setup**: Base setup wizard
- **base_import**: Import functionality

#### Enterprise/Optional Modules
- **sms**: SMS messaging
- **maintenance**: Maintenance management
- **point_of_sale**: Point of sale system
- **barcodes**: Barcode scanning
- **industry_fsm**: Field service management
- **sign**: Document signing
- **survey**: Survey management
- **documents**: Document management
- **helpdesk**: Helpdesk/support
- **mass_mailing**: Mass mailing
- **website_slides**: eLearning/slides
- **quality**: Quality management

### Records Management FSM Dependencies

#### Required Modules
- **records_management**: Base records management module
- **project**: Project management (for tasks)
- **fleet**: Fleet management (for vehicles)

#### Optional Modules
- **industry_fsm**: Enhanced FSM features (can be uncommented)

### Asset Configuration

#### Records Management Assets

**Backend Assets (`web.assets_backend`):**
- Portal components (Owl framework)
- Business logic widgets
- Visualization libraries (vis.js)
- Custom field widgets
- Dashboard components

**Frontend Assets (`web.assets_frontend`):**
- Portal components (Owl framework)
- Customer-facing JavaScript
- Portal CSS styles
- Interactive features

**Key Asset Groups:**
1. **Modern Owl Portal Components:**
   - `records_management/static/src/portal_components/**/*`

2. **Legacy Portal Assets:**
   - CSS: `portal_tour.css`, `intelligent_search.css`, `customer_portal_diagram.css`
   - JS: Portal scripts (portal_tour.js, portal_inventory_*.js, etc.)

3. **Portal-specific Scripts:**
   - `portal_barcode_management.js`
   - `portal_document_retrieval.js`

#### Records Management FSM Assets

**Backend Assets (`web.assets_backend`):**
- `records_management_fsm/static/src/xml/fleet_fsm_dashboard.xml`
- `records_management_fsm/static/src/js/fleet_fsm_dashboard.js`

---

## Integration Points

### Inter-Module Integration

#### Records Management ↔ Records Management FSM
- **Task Integration**: FSM tasks linked to records management operations
- **Fleet Integration**: Vehicles used for retrievals and shredding services
- **Notification System**: FSM notifications for records management events

#### Records Management ↔ Odoo Core Modules

1. **Account Module**
   - Invoice generation from billing records
   - Payment tracking and reconciliation
   - Account move line customizations

2. **Stock Module**
   - Container inventory management
   - Location tracking
   - Stock moves for retrievals and transfers

3. **Portal Module**
   - Customer portal access
   - Document retrieval requests
   - Inventory viewing
   - Certificate downloads

4. **Project Module**
   - Work order management
   - Task tracking
   - Team coordination

5. **Fleet Module**
   - Vehicle management
   - Route optimization
   - Service scheduling

6. **Sign Module**
   - Document signing
   - Certificate authentication
   - Audit trail

### External Library Integration

#### Vis.js Network Library
- **Purpose**: Network and hierarchical visualizations
- **Usage**: Organization diagrams, relationship mapping
- **Files**: vis-network.js, vis-network.min.js
- **Integration**: customer_portal_diagram.js, portal_organization_diagram.js

### API Integration Points

#### RPC Endpoints
- **Portal Inventory**: Data fetching and filtering
- **Document Center**: Document listing and downloads
- **Barcode Management**: Barcode generation and validation
- **Search**: Intelligent search queries

---

## Development Guidelines

### Owl Component Migration Strategy

#### Priority Order
1. **High Traffic Portal Pages** (In Progress)
   - ✅ portal_inventory.js (Completed)
   - ✅ portal_document_center.js (Completed)
   - ✅ portal_search.js (Completed)
   - ⏳ portal_quote_generator.js (Pending)

2. **Interactive Features** (Planned)
   - ⏳ portal_signature.js
   - ⏳ portal_user_import.js
   - ⏳ intelligent_search.js

3. **Visualization Components** (Future)
   - ⏳ customer_portal_diagram.js
   - ⏳ portal_organization_diagram.js

#### Migration Checklist
- [ ] Convert to Owl Component class
- [ ] Implement reactive state with useState
- [ ] Use Owl lifecycle hooks (onMounted, onWillUnmount)
- [ ] Register in appropriate registry
- [ ] Create QWeb template
- [ ] Update asset bundles
- [ ] Test functionality
- [ ] Update documentation

### View Development Guidelines

#### XML View Naming Conventions
- **Pattern**: `{model_name}_view_{type}`
- **Examples**:
  - `records_container_view_form`
  - `records_container_view_tree`
  - `records_container_view_kanban`
  - `records_container_view_search`

#### Menu Structure
- **Root menus**: Load first (records_management_root_menus.xml)
- **Child menus**: Load after all views and actions
- **Action menus**: Load with corresponding views

#### Security Considerations
- Always define access rules in `security/ir.model.access.csv`
- Use record rules for data filtering
- Portal access rules in separate security files
- Group-based permissions

### JavaScript Development Guidelines

#### Modern Approach (Recommended)
```javascript
/** @odoo-module **/
import { Component, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

export class MyComponent extends Component {
    setup() {
        this.state = useState({ /* ... */ });
    }
    // Component logic
}

registry.category("public_components").add("my_component", MyComponent);
```

#### Legacy Support
- Maintain backward compatibility
- Provide fallback for non-Owl browsers
- Gradual migration approach

#### Code Organization
- **Owl Components**: `static/src/portal_components/`
- **Legacy Scripts**: `static/src/js/`
- **Widgets**: `static/src/js/` (backend widgets)
- **Libraries**: `static/src/lib/`

### Testing Recommendations

#### View Testing
- Verify all referenced models exist
- Check field references
- Validate menu hierarchy
- Test access permissions

#### JavaScript Testing
- Unit tests for Owl components
- Integration tests for RPC calls
- Browser compatibility testing
- Portal user testing

### Performance Optimization

#### View Optimization
- Use appropriate view types (tree for lists, kanban for cards)
- Implement search views with proper filters
- Use domain filters effectively
- Optimize related field usage

#### JavaScript Optimization
- Lazy load libraries
- Use minified versions in production
- Implement pagination for large datasets
- Cache RPC results where appropriate

---

## Summary Statistics

### Records Management Module
- **Total View Files**: 296
- **Total JavaScript Files**: 30
  - Owl Components: 4
  - Legacy Portal Scripts: 15
  - Backend Widgets: 8
  - External Libraries: 2
  - Specialized Widgets: 4

### Records Management FSM Module
- **Total View Files**: 9
- **Total JavaScript Files**: 2

### Key Functional Areas
- **Billing & Accounting**: 42 view files
- **Barcode & Inventory**: 18 view files
- **Container Management**: 28 view files
- **Chain of Custody & Audit**: 12 view files
- **Destruction & Certificates**: 8 view files
- **Document Retrieval**: 16 view files
- **Portal & Customer**: 26 view files
- **Shredding Services**: 18 view files
- **Location & Facility**: 14 view files
- **Paper & Load Management**: 12 view files
- **Inventory & Stock**: 16 view files
- **Work Orders & Tasks**: 20 view files
- **Configuration & System**: 30 view files
- **Menus & Dashboards**: 10 view files
- **Specialized Integration**: 26 view files

### Framework Distribution
- **Modern Owl Components**: 4 (growing)
- **Legacy JavaScript**: 26 (being migrated)
- **Backend Widgets**: 8 (stable)

---

## Conclusion

This outline provides a comprehensive overview of all views and JavaScript files in the `records_management` and `records_management_fsm` modules. The system is built on a solid foundation of Odoo's framework with a clear migration path from legacy JavaScript to modern Owl components.

**Key Takeaways:**
1. The module is well-structured with clear separation of concerns
2. Ongoing migration to Owl framework for better performance and maintainability
3. Comprehensive coverage of records management workflows
4. Strong integration with Odoo core and enterprise modules
5. NAID AAA compliance throughout the system

**Next Steps:**
1. Continue Owl component migration
2. Update documentation as components are migrated
3. Enhance test coverage
4. Optimize performance for large datasets
5. Expand FSM integration features

---

**Document Version:** 1.0  
**Last Updated:** 2025-10-13  
**Maintained By:** Records Management Development Team
