"""Post-init hooks for Records Management module.

This module needs to support environments where scheduled action (ir.cron)
fields differ between Odoo versions / forks. Some deployments expose the
legacy field pair:
    - numbercall
    - doall
while others expose the newer API equivalents:
    - max_calls
    - catchup

Previous attempts to hard-code either style in XML led to alternating
installation failures ("Invalid field 'numbercall'" vs "Invalid field 'max_calls'").

Strategy:
1. Keep cron XML definitions *minimal* (only universally supported fields).
2. In this post-init hook, detect which field set exists on the model.
3. Apply sane defaults (-1 == unlimited runs, and disable catch-up behavior).
4. Fail gracefully if a cron XML id is absent (e.g., feature later removed).

This provides forward / backward compatibility without repeated manual edits.
"""

from odoo import api, SUPERUSER_ID


def post_init_hook(cr, registry):  # pragma: no cover - executed at install
    """Resolve cron field schema differences dynamically.

    Detection logic:
        If 'numbercall' in ir.cron fields -> use (numbercall=-1, doall=False)
        If 'max_calls' in ir.cron fields  -> use (max_calls=-1, catchup=False)

    Both may co-exist in some patched environments; in that case we set both.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    cron_model = env['ir.cron']
    cron_fields = cron_model._fields

    legacy_supported = 'numbercall' in cron_fields
    legacy_doall = 'doall' in cron_fields
    modern_supported = 'max_calls' in cron_fields
    modern_catchup = 'catchup' in cron_fields

    # If neither style is present, nothing to do.
    if not (legacy_supported or modern_supported):
        return

    # Collect cron XML IDs belonging to this module that deliberately omit
    # version-specific fields in their XML definitions.
    xml_ids = [
        'records_management.ir_cron_records_retrieval_order_sla_escalation',
        'records_management.ir_cron_compute_monthly_storage_fees',
        'records_management.ir_cron_generate_monthly_inventory_reports',
        'records_management.ir_cron_storage_fee_automation_workflow',
        'records_management.ir_cron_monthly_inventory_report_automation',
        'records_management.ir_cron_naid_training_reminders',
        'records_management.ir_cron_naid_certification_expiry_check',
        'records_management.cron_check_employee_credentials',
        'records_management.cron_cleanup_audit_logs',
        'records_management.cron_compliance_check',
        'records_management.cron_equipment_calibration_check',
        'records_management.cron_training_expiry_check',
        'records_management.cron_certificate_generation',
    ]

    # Prepare value dictionaries once.
    legacy_vals = {}
    if legacy_supported:
        legacy_vals['numbercall'] = -1  # Unlimited repetitions
        if legacy_doall:
            legacy_vals['doall'] = False  # Do not run missed executions in bulk

    modern_vals = {}
    if modern_supported:
        modern_vals['max_calls'] = -1  # Unlimited repetitions
        if modern_catchup:
            modern_vals['catchup'] = False  # Skip backlog processing

    for xml_id in xml_ids:
        try:
            record = env.ref(xml_id, raise_if_not_found=False)
        except Exception:
            record = False
        if not record:
            continue
        # Merge applicable values (do legacy first so modern can override if conflicting semantics ever arise)
        vals = {}
        if legacy_vals:
            vals.update(legacy_vals)
        if modern_vals:
            vals.update(modern_vals)
        if vals:
            try:
                record.write(vals)
            except Exception:
                # Never block installation; silently continue to next cron.
                continue
