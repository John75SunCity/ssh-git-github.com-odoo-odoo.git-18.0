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
        attendance_created = 0
        attendance_updated = 0
        AnalyticLine = self.env["account.analytic.line"].sudo()
        Attendance = self.env["hr.attendance"].sudo()
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

            # Log missing start/end times for debugging
            if not start_dt_entry or not end_dt_entry:
                _logger.warning(
                    "TSheets entry %s missing start/end times. start=%s, end=%s, duration=%s",
                    entry.get("id"),
                    entry.get("start"),
                    entry.get("end"),
                    duration_seconds
                )

            # Calculate duration if not provided
            if duration_seconds <= 0 and start_dt_entry and end_dt_entry:
                duration_seconds = int((end_dt_entry - start_dt_entry).total_seconds())
            if duration_seconds <= 0:
                skipped += 1
                continue

            unit_amount = duration_seconds / 3600.0
            tsheets_notes = entry.get("notes") or ""
            jobcode_name = entry.get("jobcode_name") or ""
            description = tsheets_notes or jobcode_name or "TSheets Entry"

            # Get the actual timesheet date from TSheets (not clock-in time)
            # TSheets provides a 'date' field which is the work date (YYYY-MM-DD)
            tsheets_date_str = entry.get("date")
            if tsheets_date_str:
                try:
                    # Parse YYYY-MM-DD format
                    date_value = fields.Date.from_string(tsheets_date_str)
                except (ValueError, TypeError):
                    # Fallback to start date if parsing fails
                    date_value = start_dt_entry.date() if start_dt_entry else now_utc.date()
            else:
                # Fallback to start date if no date field
                date_value = start_dt_entry.date() if start_dt_entry else now_utc.date()

            # Use jobcode_name for description if available (shows "Lunch Break", etc.)
            entry_description = tsheets_notes or jobcode_name or "TSheets Entry"

            # Prepare values with all TSheets data
            existing = AnalyticLine.search([("tsheets_id", "=", tsheets_id)], limit=1)

            values = {
                "name": entry_description,
                "employee_id": mapping.employee_id.id,
                "tsheets_id": tsheets_id,
                "unit_amount": unit_amount,  # Use the actual duration from TSheets
                "date": date_value,
                "company_id": config.company_id.id,
                # TSheets notes
                "tsheets_notes": tsheets_notes,
                # Job code info (shows "Lunch Break", job names, etc.)
                "tsheets_jobcode_id": str(entry.get("jobcode_id", "")),
                "tsheets_jobcode_name": jobcode_name,
                # Entry type and status
                "tsheets_type": self._map_tsheets_type(entry.get("type", "regular")),
                "tsheets_on_the_clock": entry.get("on_the_clock", False),
            }

            if config.default_project_id:
                values["project_id"] = config.default_project_id.id
            if config.default_task_id:
                values["task_id"] = config.default_task_id.id
            user = mapping.employee_id.user_id
            if user:
                values["user_id"] = user.id

            # STEP 1: Create/update hr.attendance record FIRST from TSheets start/end times
            attendance_record = None
            if start_dt_entry and end_dt_entry:
                _logger.info(
                    "Creating attendance for employee %s: check_in=%s, check_out=%s",
                    mapping.employee_id.name,
                    start_dt_entry,
                    end_dt_entry
                )

                # Check if attendance record already exists for this TSheets entry
                existing_attendance = Attendance.search([
                    ("employee_id", "=", mapping.employee_id.id),
                    ("check_in", "=", start_dt_entry),
                ], limit=1)

                attendance_values = {
                    "employee_id": mapping.employee_id.id,
                    "check_in": start_dt_entry,
                    "check_out": end_dt_entry,
                }

                # Add overtime if TSheets provides it
                overtime_seconds = entry.get("overtime", 0)
                if overtime_seconds > 0:
                    overtime_hours = overtime_seconds / 3600.0
                    attendance_values["validated_overtime_hours"] = overtime_hours
                    _logger.info("Adding overtime: %s hours", overtime_hours)

                if existing_attendance:
                    existing_attendance.write(attendance_values)
                    attendance_updated += 1
                    attendance_record = existing_attendance
                    _logger.info("Updated existing attendance record ID %s", existing_attendance.id)
                else:
                    attendance_record = Attendance.create(attendance_values)
                    attendance_created += 1
                    _logger.info("Created new attendance record ID %s", attendance_record.id)
            else:
                _logger.warning(
                    "Skipping attendance creation for TSheets entry %s - missing start or end time",
                    tsheets_id
                )

            # STEP 2: Link the timesheet to the attendance record
            if attendance_record:
                values["attendance_id"] = attendance_record.id
                _logger.info("Linking timesheet to attendance record ID %s", attendance_record.id)

            # STEP 3: Create/update the timesheet entry
            if existing:
                existing.write(values)
                updated += 1
            else:
                AnalyticLine.create(values)
                created += 1

            mapping.mark_synced()

        summary_message = _(
            "TSheets synchronization imported %s entries (created: %s, updated: %s, skipped: %s). "
            "Attendance records (created: %s, updated: %s)."
        ) % (
            len(all_entries),
            created,
            updated,
            skipped,
            attendance_created,
            attendance_updated,
        )
        config.write({
            "last_success_at": fields.Datetime.to_string(now_utc),
            "last_message": summary_message,
        })
        config.message_post(body=summary_message)
        return {
            "created": created,
            "updated": updated,
            "skipped": skipped,
            "attendance_created": attendance_created,
            "attendance_updated": attendance_updated,
        }

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
