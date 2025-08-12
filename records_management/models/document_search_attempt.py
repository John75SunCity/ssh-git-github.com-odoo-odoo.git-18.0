# -*- coding: utf-8 -*-
"""
Document Search Attempt Model

Track individual search attempts for files during document retrieval operations.
"""

from odoo import models, fields, api




class DocumentSearchAttempt(models.Model):
    """Track individual search attempts for files"""

    _name = "document.search.attempt"
    _description = "Document Search Attempt"
    _order = "search_date desc"

    retrieval_item_id = fields.Many2one(
        "document.retrieval.item",
        string="Retrieval Item",
        required=True,
        ondelete="cascade",
    )

    container_id = fields.Many2one(
        "records.container",
        string="Container Searched",
        required=True,
    )

    searched_by_id = fields.Many2one(  # FIXED: Added _id suffix
        "res.users",
        string="Searched By",
        required=True,
    )

    search_date = fields.Datetime(
        string="Search Date",
        required=True,
        default=fields.Datetime.now,
    )

    found = fields.Boolean(
        string="Found",
        default=False,
    )

    notes = fields.Text(
        string="Search Notes",
        help="Notes about what was found or why file wasn't found in this container",
    )

    # Reference fields for easy access
    requested_file_name = fields.Char(
        related="retrieval_item_id.requested_file_name",
        string="Requested File",
        readonly=True,
    )

    customer_id = fields.Many2one(
        related="retrieval_item_id.partner_id",
        string="Customer",
        readonly=True,
    )

    def get_history_summary(self):
        """Get summary of search attempt history"""
        self.ensure_one()
        return {
            "container": self.container_id.name if self.container_id else "Unknown",
            "customer": self.customer_id.name if self.customer_id else "Unknown",
            "date": self.search_date,
            "searched_by": self.searched_by_id.name if self.searched_by_id else "Unknown",
            "found": self.found,
            "notes": self.notes or "",
        }
