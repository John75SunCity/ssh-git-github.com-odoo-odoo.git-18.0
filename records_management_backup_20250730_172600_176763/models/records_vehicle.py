# -*- coding: utf-8 -*-
""",
Records Management Vehicle Model
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class RecordsVehicle(models.Model):
    """,
    Vehicle Management for Records Management Pickup Routes:
    Simple vehicle model focused on capacity tracking for document pickup:
    """

    _name = "records.vehicle",
    _description = "Records Management Vehicle",
    _inherit = ["mail.thread", "mail.activity.mixin"],
    _order = "name",
    _rec_name = "name"

    # ==========================================
    # CORE FIELDS
    # ==========================================
    name = fields."status": "available"("status": "available")

def action_set_in_use(self):
                                                                                            """Mark vehicle as in use""",
                                                                                            self.write({"status": "in_use"})

def action_set_maintenance(self):
    pass
"""Mark vehicle for maintenance""":
                                                                                                    self.write({"status": "maintenance"})

def action_view_pickup_routes(self):
    pass
"""View pickup routes for this vehicle""":
                                                                                                            action = self.env.ref("records_management.action_pickup_request").read()[0],
                                                                                                            action["domain"] = [("vehicle_id", "=", self.id)],
                                                                                                            action["context"] = {"default_vehicle_id": self.id}
                                                                                                            return action