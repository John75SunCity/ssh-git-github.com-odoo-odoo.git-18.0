# -*- coding: utf-8 -*-
"""
Service Attachment Hub

This model provides a centralized view of all attachments (photos, documents, PDFs)
from service-related records like work orders, invoices, and certificates.

It uses Odoo's native ir.attachment system and filters by:
- work.order.shredding
- pickup.request
- records.retrieval.order
- destruction.certificate
- account.move (invoices)
- project.task (FSM tasks)

This allows technicians to upload photos via the standard "Attach File" button
on any work order, and they automatically appear in the Service Attachments Hub.

Portal visibility is controlled by partner_id relationships on the source documents.
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ServiceAttachment(models.Model):
    """
    Virtual/SQL model to provide a unified view of service-related attachments.
    This extends ir.attachment with service-specific computed fields.
    """
    _name = 'service.attachment'
    _description = 'Service Attachment Hub'
    _auto = False  # SQL view - no physical table
    _order = 'create_date desc'

    # Core attachment fields (from ir.attachment)
    name = fields.Char(string="File Name", readonly=True)
    mimetype = fields.Char(string="MIME Type", readonly=True)
    file_size = fields.Integer(string="File Size", readonly=True)
    create_date = fields.Datetime(string="Upload Date", readonly=True)
    create_uid = fields.Many2one(comodel_name='res.users', string="Uploaded By", readonly=True)

    # Source document info
    res_model = fields.Char(string="Source Model", readonly=True)
    res_id = fields.Integer(string="Source ID", readonly=True)

    # Customer/Partner relationship (computed from source document)
    partner_id = fields.Many2one(comodel_name='res.partner', string="Customer", readonly=True)

    # Attachment category (computed from mimetype)
    attachment_category = fields.Selection([
        ('image', 'Photo/Image'),
        ('pdf', 'PDF Document'),
        ('document', 'Other Document'),
    ], string="Category", readonly=True)

    # Portal visibility
    is_portal_visible = fields.Boolean(string="Portal Visible", readonly=True)

    # Original attachment reference - used for accessing binary data and res_name
    attachment_id = fields.Many2one(comodel_name='ir.attachment', string="Attachment", readonly=True)

    # Related fields to get data from the original attachment
    datas = fields.Binary(string="File Content", related='attachment_id.datas', readonly=True)
    res_name = fields.Char(string="Source Document", related='attachment_id.res_name', readonly=True)

    def init(self):
        """Create SQL view for service attachments"""
        self.env.cr.execute("""
            DROP VIEW IF EXISTS service_attachment;
            CREATE OR REPLACE VIEW service_attachment AS (
                SELECT
                    att.id as id,
                    att.id as attachment_id,
                    att.name as name,
                    att.mimetype as mimetype,
                    att.file_size as file_size,
                    att.create_date as create_date,
                    att.create_uid as create_uid,
                    att.res_model as res_model,
                    att.res_id as res_id,
                    CASE
                        WHEN att.mimetype LIKE 'image/%%' THEN 'image'
                        WHEN att.mimetype = 'application/pdf' THEN 'pdf'
                        ELSE 'document'
                    END as attachment_category,
                    CASE
                        WHEN att.res_model = 'work.order.shredding' THEN wo.partner_id
                        WHEN att.res_model = 'pickup.request' THEN pr.partner_id
                        WHEN att.res_model = 'records.retrieval.order' THEN rro.partner_id
                        WHEN att.res_model = 'destruction.certificate' THEN dc.partner_id
                        WHEN att.res_model = 'account.move' THEN am.partner_id
                        WHEN att.res_model = 'project.task' THEN pt.partner_id
                        ELSE NULL
                    END as partner_id,
                    CASE
                        WHEN att.res_model IN (
                            'work.order.shredding', 'pickup.request', 'records.retrieval.order',
                            'destruction.certificate', 'account.move', 'project.task'
                        ) THEN TRUE
                        ELSE FALSE
                    END as is_portal_visible
                FROM ir_attachment att
                LEFT JOIN work_order_shredding wo ON att.res_model = 'work.order.shredding' AND att.res_id = wo.id
                LEFT JOIN pickup_request pr ON att.res_model = 'pickup.request' AND att.res_id = pr.id
                LEFT JOIN records_retrieval_order rro ON att.res_model = 'records.retrieval.order' AND att.res_id = rro.id
                LEFT JOIN destruction_certificate dc ON att.res_model = 'destruction.certificate' AND att.res_id = dc.id
                LEFT JOIN account_move am ON att.res_model = 'account.move' AND att.res_id = am.id
                LEFT JOIN project_task pt ON att.res_model = 'project.task' AND att.res_id = pt.id
                WHERE att.res_model IN (
                    'work.order.shredding',
                    'pickup.request',
                    'records.retrieval.order',
                    'destruction.certificate',
                    'account.move',
                    'project.task'
                )
                AND att.res_id IS NOT NULL
            )
        """)

    def action_open_source_document(self):
        """Open the source document this attachment belongs to"""
        self.ensure_one()
        if not self.res_model or not self.res_id:
            raise UserError(_("No source document linked to this attachment."))

        return {
            'type': 'ir.actions.act_window',
            'name': self.res_name or _('Source Document'),
            'res_model': self.res_model,
            'res_id': self.res_id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_download(self):
        """Download the attachment"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{self.attachment_id.id}?download=true',
            'target': 'self',
        }
