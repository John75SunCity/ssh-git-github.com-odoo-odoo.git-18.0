import logging
from datetime import datetime

import requests
from dateutil.relativedelta import relativedelta

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class TsheetsSyncService(models.AbstractModel):
    _name = "qb.tsheets.sync.service"
    _description = "TSheets Synchronization Service"

    def cleanup_action_bindings(self):
        """
        Manual cleanup method to remove action bindings.
        Call this from Settings → Technical → Server Actions if wizard still auto-pops.
        """
        # Remove bindings from wizard action
        wizard_action = self.env.ref('qb_tsheet_sync.action_tsheets_sync_wizard', raise_if_not_found=False)
        if wizard_action:
            wizard_action.write({
                'binding_model_id': False,
                'binding_view_types': False,
            })

        # Find and remove bindings from any TSheets server actions
        server_actions = self.env['ir.actions.server'].search([
            ('name', 'ilike', 'tsheet')
        ])
        for action in server_actions:
            if action.binding_model_id:
                action.write({
                    'binding_model_id': False,
                    'binding_view_types': False,
                })

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Action Bindings Cleaned"),
                "message": _("Removed all TSheets action bindings. Please refresh your browser."),
                "type": "success",
                "sticky": False,
            },
        }

    def manual_sync(self, config, date_from=None, date_to=None, force_resync=False):
        self._validate_config(config)
        summary = self._run_sync(config, manual=True, date_from=date_from, date_to=date_to, force_resync=force_resync)
        message = _("TSheets synchronization complete: %s created, %s updated, %s skipped.") % (
            summary["created"],
            summary["updated"],
            summary["skipped"],
        )
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("TSheets Sync"),
                "message": message,
                "type": "success",
                "sticky": False,
            },
        }

    def cron_sync(self):
        configs = self.env["qb.tsheets.sync.config"].search([
            ("active", "=", True),
            ("auto_sync", "=", True),
            ("api_token", "!=", False),
        ])
        for config in configs:
            try:
                self._validate_config(config)
            except UserError as exc:
                _logger.error("Skipping TSheets sync for %s: %s", config.display_name, exc)
                continue
            try:
                self._run_sync(config, manual=False)
            except Exception as exc:  # broad to ensure cron never crashes
                _logger.exception("TSheets sync failed for %s: %s", config.display_name, exc)

    def _validate_config(self, config):
        if not config.api_token:
            raise UserError(_("Please configure the API token before synchronizing."))
        if not config.employee_map_ids:
            raise UserError(_("Add at least one employee mapping before synchronizing."))

    def _run_sync(self, config, manual=False, date_from=None, date_to=None, force_resync=False):
        now_utc = fields.Datetime.from_string(fields.Datetime.now())
        config.write({
            "last_attempt_at": fields.Datetime.to_string(now_utc),
        })

        # Use provided date range or fall back to config lookback
        if date_from and date_to:
            start_dt = fields.Datetime.from_string(str(date_from))
            end_dt = fields.Datetime.from_string(str(date_to))
        else:
            lookback = config.sync_lookback_days or 0
            if config.last_success_at and not force_resync:
                start_dt = config.last_success_at - relativedelta(days=lookback)
            else:
                start_dt = now_utc - relativedelta(days=max(lookback, 1))
            end_dt = now_utc

        headers = {
            "Authorization": "Bearer %s" % config.api_token,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        base_url = config.base_url.rstrip("/")
        endpoint = "%s/timesheets" % base_url
        page = 1
        created = 0
        updated = 0
        skipped = 0
        AnalyticLine = self.env["account.analytic.line"].sudo()
        mapping_by_user = {
            str(mapping.tsheets_user_id): mapping for mapping in config.employee_map_ids.filtered(lambda m: m.active)
        }
        if not mapping_by_user:
            raise UserError(_("All employee mappings are inactive; cannot synchronize."))

        params = {
            "modified_since": self._format_datetime(start_dt),
            "start_date": start_dt.date().isoformat(),
            "end_date": end_dt.date().isoformat(),
            "per_page": 100,
        }
        all_entries = []
        try:
            while True:
                params["page"] = page
                response = requests.get(endpoint, headers=headers, params=params, timeout=30)
                if response.status_code != 200:
                    raise UserError(
                        _("TSheets API returned status %s: %s")
                        % (response.status_code, response.text),
                    )
                payload = response.json()
                timesheets = payload.get("results", {}).get("timesheets", {})
                all_entries.extend(timesheets.values())
                if not payload.get("more"):
                    break
                page += 1
        except requests.RequestException as exc:
            raise UserError(_("Unable to reach the TSheets API: %s") % exc) from exc

        for entry in all_entries:
            tsheets_id = str(entry.get("id"))
            if not tsheets_id:
                skipped += 1
                continue
            mapping = mapping_by_user.get(str(entry.get("user_id")))
            if not mapping:
                skipped += 1
                continue

            # Get time data
            duration_seconds = entry.get("duration") or 0
            start_dt_entry = self._safe_datetime(entry.get("start"))
            end_dt_entry = self._safe_datetime(entry.get("end"))

            # Calculate duration if not provided
            if duration_seconds <= 0 and start_dt_entry and end_dt_entry:
                duration_seconds = int((end_dt_entry - start_dt_entry).total_seconds())
            if duration_seconds <= 0:
                skipped += 1
                continue

            unit_amount = duration_seconds / 3600.0
            tsheets_notes = entry.get("notes") or ""
            description = tsheets_notes or entry.get("jobcode_name") or "TSheets Entry"
            date_value = start_dt_entry.date() if start_dt_entry else now_utc.date()

            # Detect break entries (typically 0.5 hours or marked as unpaid_break type)
            entry_type = entry.get("type", "regular")
            is_break = (entry_type == "unpaid_break" or
                       (unit_amount == 0.5 and not entry.get("jobcode_id")) or
                       "break" in description.lower() or
                       "lunch" in description.lower())

            # Prepare values with all TSheets data
            existing = AnalyticLine.search([("tsheets_id", "=", tsheets_id)], limit=1)

            # If this is a break entry, make it negative (deduction)
            if is_break:
                actual_unit_amount = -unit_amount  # Negative for breaks
                break_duration = unit_amount  # Store positive break duration
                entry_description = f"[BREAK] {description}"
            else:
                actual_unit_amount = unit_amount
                break_duration = 0
                entry_description = description

            values = {
                "name": entry_description,
                "employee_id": mapping.employee_id.id,
                "tsheets_id": tsheets_id,
                "unit_amount": actual_unit_amount,
                "date": date_value,
                "company_id": config.company_id.id,
                # TSheets notes
                "tsheets_notes": tsheets_notes,
                # Break duration (positive value even though unit_amount is negative)
                "tsheets_break_duration": break_duration,
                # Clock in/out times
                "tsheets_clock_in": start_dt_entry,
                "tsheets_clock_out": end_dt_entry,
                # Job code info
                "tsheets_jobcode_id": str(entry.get("jobcode_id", "")),
                "tsheets_jobcode_name": entry.get("jobcode_name", ""),
                # Entry type and status
                "tsheets_type": self._map_tsheets_type(entry.get("type", "regular")),
                "tsheets_on_the_clock": entry.get("on_the_clock", False),
            }

            # Handle overtime
            tz_str = entry.get("tz_str") or entry.get("tz") or "UTC"
            overtime_hours = 0
            if entry.get("overtime", 0) > 0:
                overtime_hours = entry.get("overtime") / 3600.0  # Convert seconds to hours
                values["tsheets_overtime"] = True
                values["tsheets_overtime_hours"] = overtime_hours
            else:
                values["tsheets_overtime"] = False
                values["tsheets_overtime_hours"] = 0

            if config.default_project_id:
                values["project_id"] = config.default_project_id.id
            if config.default_task_id:
                values["task_id"] = config.default_task_id.id
            user = mapping.employee_id.user_id
            if user:
                values["user_id"] = user.id

            if existing:
                existing.write(values)
                updated += 1
            else:
                AnalyticLine.create(values)
                created += 1
            mapping.mark_synced()

        summary_message = _("TSheets synchronization imported %s entries (created: %s, updated: %s, skipped: %s).") % (
            len(all_entries),
            created,
            updated,
            skipped,
        )
        config.write({
            "last_success_at": fields.Datetime.to_string(now_utc),
            "last_message": summary_message,
        })
        config.message_post(body=summary_message)
        return {"created": created, "updated": updated, "skipped": skipped}

    @staticmethod
    def _format_datetime(value):
        if isinstance(value, datetime):
            dt_value = value
        elif value:
            dt_value = fields.Datetime.from_string(value)
        else:
            dt_value = fields.Datetime.now()
        return fields.Datetime.to_string(dt_value).replace(" ", "T") + "Z"

    @staticmethod
    def _safe_datetime(value):
        if not value:
            return None
        try:
            if isinstance(value, datetime):
                return value
            return fields.Datetime.from_string(value)
        except Exception:
            return None

    @staticmethod
    def _map_tsheets_type(tsheets_type):
        """Map TSheets entry type to our selection field"""
        type_mapping = {
            'regular': 'regular',
            'pto': 'pto',
            'paid_time_off': 'pto',
            'holiday': 'holiday',
            'sick': 'sick',
            'vacation': 'vacation',
            'unpaid_break': 'unpaid_break',
            'break': 'unpaid_break',
        }
        return type_mapping.get(str(tsheets_type).lower(), 'other')
