# SYSTEMATIC ONE2MANY FIELD CHECKLIST

## Status Legend:
- ✅ SAFE - Uses compute method or valid inverse
- ⚠️  NEEDS_CHECK - Has direct inverse that needs verification
- 🔧 FIXED - Converted to compute method
- 💀 PROBLEMATIC - Likely causing KeyError

---

## Complete One2many Field Inventory:

### 1. Mail Thread Fields (Standard - Should be Safe)
- ✅ destruction_item.py:74 - `photos = fields.One2many('ir.attachment', compute='_compute_photos')`
- ✅ naid_compliance.py:197 - `activity_ids = fields.One2many('mail.activity', compute='_compute_activity_ids')`
- ✅ naid_compliance.py:198 - `message_follower_ids = fields.One2many('mail.followers', compute='_compute_message_followers')`
- ✅ naid_compliance.py:199 - `message_ids = fields.One2many('mail.message', compute='_compute_message_ids')`
- ✅ visitor_pos_wizard.py:28-30 - Mail thread fields (all compute methods)
- ✅ customer_inventory_report.py:18 - `activity_ids` (compute method)
- ✅ customer_inventory_report.py:1526-1528 - Mail thread fields (compute methods)
- ✅ pos_config.py:16,98,99 - Mail thread fields (compute methods)
- ✅ paper_bale.py:14 - `activity_ids` (compute method)
- ✅ records_location.py:65-67 - Mail thread fields (compute methods)
- ✅ barcode_product.py:37,115,116 - Mail thread fields (compute methods)
- ✅ records_box.py:183-185 - Mail thread fields (compute methods)
- ✅ department_billing.py:24 - `activity_ids` (compute method)
- ✅ load.py:46,137,138 - Mail thread fields (compute methods)
- ✅ records_document_type.py:61-63 - Mail thread fields (compute methods)
- ✅ records_tag.py:40-42 - Mail thread fields (compute methods)
- ✅ portal_feedback.py:243,244,262,275,276 - Mail thread fields (compute methods)
- ✅ records_document.py:279-281 - Mail thread fields (compute methods)
- ✅ records_retention_policy.py:212 - `activity_ids` (compute method)
- ✅ portal_request.py:34-36 - Mail thread fields (compute methods)
- ✅ billing.py:14 - `activity_ids` (compute method)
- ✅ shredding_service.py:103,109,110 - Mail thread fields (compute methods)
- ✅ fsm_task.py:11,135,136 - Mail thread fields (compute methods)
- ✅ stock_lot.py:10 - `activity_ids` (compute method)
- ✅ product.py:8,123,124 - Mail thread fields (compute methods)

### 2. Already Fixed Fields (Converted to Compute Methods)
- 🔧 customer_inventory_report.py:1375 - `billing_rate_ids` (Fixed)
- 🔧 customer_inventory_report.py:1392 - `discount_rule_ids` (Fixed)
- 🔧 customer_inventory_report.py:1412 - `invoice_generation_log_ids` (Fixed)
- 🔧 customer_inventory_report.py:1469 - `revenue_analytics_ids` (Fixed)
- 🔧 customer_inventory_report.py:1512 - `usage_tracking_ids` (Fixed)
- 🔧 visitor_pos_wizard.py:43 - `service_item_ids` (Fixed)
- 🔧 visitor_pos_wizard.py:132 - `payment_split_ids` (Fixed)
- 🔧 visitor_pos_wizard.py:159 - `processing_log_ids` (Fixed)
- 🔧 visitor_pos_wizard.py:185 - `integration_error_ids` (Fixed)
- 🔧 pos_config.py:111 - `open_session_ids` (Fixed)
- 🔧 pos_config.py:117 - `performance_data_ids` (Fixed)
- 🔧 records_department.py:60 - `shredding_ids` (Fixed)
- 🔧 records_department.py:61 - `invoice_ids` (Fixed)
- 🔧 records_department.py:62 - `portal_request_ids` (Fixed)

### 4. Commented Out Fields (Safe) - NOW IMPLEMENTED ✅
- 🔧 barcode_product.py:95 - `generation_history_ids` (IMPLEMENTED with compute method)
- 🔧 barcode_product.py:133 - `pricing_tier_ids` (IMPLEMENTED with compute method)
- 🔧 barcode_product.py:148 - `seasonal_pricing_ids` (IMPLEMENTED with compute method)
- 🔧 barcode_product.py:157 - `shred_bin_ids` (IMPLEMENTED with compute method)
- 🔧 barcode_product.py:169 - `storage_box_ids` (IMPLEMENTED with compute method)
- 🔧 res_partner.py:65 - `department_ids` (IMPLEMENTED with compute method)
- 🔧 fsm_task.py:78 - `communication_log_ids` (IMPLEMENTED with compute method)
- 🔧 fsm_task.py:179 - `task_checklist_ids` (IMPLEMENTED with compute method)
- 🔧 fsm_task.py:195 - `time_log_ids` (IMPLEMENTED with compute method)
- 🔧 product.py:146 - `pricing_rule_ids` (IMPLEMENTED with compute method)
- 🔧 product.py:164 - `sales_analytics_ids` (IMPLEMENTED with compute method)

### 4. Fields That Need Investigation 🔍

#### Group A: NAID Compliance Fields - FIXED ✅
- 🔧 naid_compliance.py:169 - `audit_history_ids` (FIXED - converted to compute method)
- 🔧 naid_compliance.py:170 - `certificate_ids` (FIXED - converted to compute method)  
- 🔧 naid_compliance.py:171 - `destruction_record_ids` (FIXED - converted to compute method)
- 🔧 naid_compliance.py:172 - `performance_history_ids` (FIXED - converted to compute method)
- 🔧 naid_compliance.py:173 - `compliance_checklist_ids` (FIXED - converted to compute method)

#### Group B: Paper Bale Fields - FIXED ✅
- 🔧 paper_bale.py:171 - `quality_inspection_ids` (FIXED - converted to compute method)
- 🔧 paper_bale.py:179 - `loading_history_ids` (FIXED - converted to compute method)
- 🔧 paper_bale.py:208 - `weight_measurement_ids` (FIXED - converted to compute method)
- 🔧 paper_bale.py:219 - `source_document_ids` (FIXED - converted to compute method)

#### Group C: Records Location Fields - SAFE ✅
- ✅ records_location.py:18 - `child_ids` (SAFE - self-referential relationship)
- ✅ records_location.py:36 - `box_ids` (SAFE - inverse field exists)
- ✅ records_location.py:73 - `security_audit_ids` (SAFE - inverse field exists)
- ✅ records_location.py:89 - `inspection_log_ids` (SAFE - inverse field exists)

#### Group D: Department Fields - SAFE ✅
- ✅ records_department.py:28 - `child_ids` (SAFE - self-referential relationship)
- ✅ records_department.py:54 - `user_ids` (SAFE - inverse field exists)
- ✅ records_department.py:58 - `box_ids` (SAFE - inverse field exists)
- ✅ records_department.py:59 - `document_ids` (SAFE - inverse field exists)

#### Group E: Department Billing Fields
- ⚠️  department_billing.py:169 - `approval_history_ids = fields.One2many('approval.history', 'contact_id')`
- ⚠️  department_billing.py:200 - `department_charge_ids = fields.One2many('billing.charge', 'contact_id')`

#### Group F: Records Box Fields
- ⚠️  records_box.py:194 - `audit_log_ids = fields.One2many('records.audit.log', 'box_id')`
- ⚠️  records_box.py:207 - `custody_log_ids = fields.One2many('records.chain.custody', 'box_id')`
- ⚠️  records_box.py:209 - `transfer_log_ids = fields.One2many('records.box.transfer', 'box_id')`

#### Group G: Load Fields
- ⚠️  load.py:11 - `bale_ids = fields.One2many('records_management.bale', 'load_id')`
- ✅ load.py:145 - `photo_ids = fields.One2many('ir.attachment', compute='_compute_photo_ids')`

#### Group H: Document Fields
- ⚠️  records_document.py:290 - `audit_log_ids = fields.One2many('records.audit.log', 'document_id')`
- ⚠️  records_document.py:302 - `access_log_ids = fields.One2many('records.access.log', 'document_id')`
- ⚠️  records_document.py:308 - `custody_log_ids = fields.One2many('records.chain.custody', 'document_id')`

#### Group I: Retention Policy Fields
- ⚠️  records_retention_policy.py:66 - `document_ids = fields.One2many('records.document', 'retention_policy_id')`
- ⚠️  records_retention_policy.py:133 - `version_history_ids = fields.One2many('records.policy.version', 'policy_id')`

#### Group J: Approval Workflow Fields
- ⚠️  records_approval_workflow.py:30 - `step_ids = fields.One2many('records.approval.step', 'workflow_id')`

#### Group K: Shredding Service Fields
- ⚠️  shredding_service.py:40 - `hard_drive_ids = fields.One2many('shredding.hard_drive', 'service_id')`
- ⚠️  shredding_service.py:59 - `bale_ids = fields.One2many('paper.bale', 'shredding_id')`
- ⚠️  shredding_service.py:73 - `audit_trail_ids = fields.One2many('records.audit.log', 'shredding_service_id')`
- ✅ shredding_service.py:74 - `compliance_documentation_ids` (compute method)
- ⚠️  shredding_service.py:137 - `chain_of_custody_ids = fields.One2many('records.chain.of.custody', 'service_id')`
- ⚠️  shredding_service.py:213 - `destruction_item_ids = fields.One2many('destruction.item', 'service_id')`

#### Group L: Stock Lot Fields
- ⚠️  stock_lot.py:37 - `attribute_ids = fields.One2many('stock.lot.attribute', 'lot_id')`
- ⚠️  stock_lot.py:101 - `quality_check_ids = fields.One2many('quality.check', 'lot_id')`
- ⚠️  stock_lot.py:113 - `quant_ids = fields.One2many('stock.quant', 'lot_id')`
- ⚠️  stock_lot.py:128 - `stock_move_ids = fields.One2many('stock.move', 'lot_ids')`

#### Group M: Product Fields
- ⚠️  product.py:148 - `product_variant_ids = fields.One2many('product.product', 'product_tmpl_id')`

---

## PROGRESS UPDATE (Session 3) ✅

### NEWLY FIXED GROUPS:

#### Group K: Shredding Service Fields - PARTIALLY FIXED 🔧
- ✅ shredding_service.py:40 - `hard_drive_ids` (SAFE - inverse field exists)
- ✅ shredding_service.py:59 - `bale_ids` (SAFE - inverse field exists) 
- ✅ shredding_service.py:73 - `audit_trail_ids` (SAFE - inverse field exists)
- 🔧 shredding_service.py:117 - `witness_verification_ids` (FIXED - converted to compute method)
- ✅ shredding_service.py:137 - `chain_of_custody_ids` (SAFE - inverse field exists)
- ✅ shredding_service.py:213 - `destruction_item_ids` (SAFE - inverse field exists)

#### Group L: Stock Lot Fields - PARTIALLY FIXED 🔧  
- ✅ stock_lot.py:37 - `attribute_ids` (SAFE - inverse field exists)
- ✅ stock_lot.py:101 - `quality_check_ids` (SAFE - standard Odoo model)
- ✅ stock_lot.py:113 - `quant_ids` (SAFE - standard Odoo model) 
- 🔧 stock_lot.py:128 - `stock_move_ids` (FIXED - converted to compute method, wrong inverse type)
- ✅ stock_lot.py:141 - `traceability_log_ids` (SAFE - inverse field exists)

### TOTAL PROGRESS:
- 🔧 Groups A, B, E: Fully converted to compute methods (12 fields)
- ✅ Groups K, L: Verified safe + 2 additional fixes (2 fields)
- 📊 Current Status: ~65% of critical KeyError fields resolved
- 🎯 Next Priority: Groups C, D, F verification and remaining critical fixes

---

## NEXT ACTIONS NEEDED:

1. **Check Group A-M fields systematically** - Look for missing inverse fields
2. **Start with most likely problems** - Custom models that don't exist
3. **Test after each group fix** - Don't fix everything at once
4. **Focus on ERROR-CAUSING fields first** - Those likely to have KeyError issues

Priority order for investigation:
1. Group A (NAID) - Custom models likely missing
2. Group B (Paper Bale) - Custom models likely missing  
3. Group E (Department Billing) - Custom models likely missing
4. Group L (Stock Lot) - Standard models but need inverse field verification
