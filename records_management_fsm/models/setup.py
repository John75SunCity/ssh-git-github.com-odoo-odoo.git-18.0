# -*- coding: utf-8 -*-
"""Utility helpers for Records Management FSM installation."""

from odoo import SUPERUSER_ID, api, models


class RecordsManagementFSMSetup(models.AbstractModel):
    """Setup helpers executed during module data loading."""

    _name = "records.management.fsm.setup"
    _description = "Records Management FSM Setup Utilities"

    def _ensure_fleet_vehicle_action(self):
        """Ensure the fleet work vehicle action exists before menu creation.

        The paired records_management module normally defines
        ``records_management.action_fleet_vehicle_records_work``. In older
        databases that predate the action, installing the FSM bridge would
        fail when the menu tried to reference the missing external ID. This
        helper recreates the action on the fly, falling back to standard
        fleet views so the FSM module remains installable.
        """

        env = self.env
        try:
            env.ref("records_management.action_fleet_vehicle_records_work")
            return
        except ValueError:
            # Missing action must be recreated with a sensible fallback.
            pass

        view_order = [
            ("records_management.fleet_vehicle_view_kanban_records_work", "kanban"),
            ("records_management.fleet_vehicle_view_list_records_work", "list"),
            ("records_management.fleet_vehicle_view_form_records_work", "form"),
        ]
        fallback_views = {
            "kanban": "fleet.fleet_vehicle_kanban_view",
            "list": "fleet.fleet_vehicle_view_tree",
            "form": "fleet.fleet_vehicle_view_form",
        }

        view_ids = []
        active_modes = []
        for xmlid, mode in view_order:
            view = env.ref(xmlid, raise_if_not_found=False)
            if not view:
                fallback_xmlid = fallback_views.get(mode)
                view = env.ref(fallback_xmlid, raise_if_not_found=False)
            if view:
                view_ids.append((0, 0, {"view_mode": mode, "view_id": view.id}))
                active_modes.append(mode)

        view_mode = ",".join(active_modes) if active_modes else "list,form"

        action_vals = {
            "name": "Records Work Vehicles",
            "res_model": "fleet.vehicle",
            "view_mode": view_mode,
            "view_ids": view_ids,
            "domain": "[('records_vehicle_type','!=',False)]",
            "context": "{'search_default_available_work': 1}",
            "help": "<p class=\"o_view_nocontent_smiling_face\"><i class=\"fa fa-truck\" title=\"Vehicle\"/> Configure your first Records Work Vehicle!</p>",
        }
        action = env["ir.actions.act_window"].create(action_vals)

        env["ir.model.data"].create({
            "module": "records_management",
            "name": "action_fleet_vehicle_records_work",
            "model": "ir.actions.act_window",
            "res_id": action.id,
            "noupdate": False,
        })

        return action
