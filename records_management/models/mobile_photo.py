from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class MobilePhoto(models.Model):
    _name = 'mobile.photo'
    _description = 'Mobile Photo'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string="Photo Name", required=True, default=lambda self: _('New Photo'))
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    active = fields.Boolean(string="Active", default=True)

    # Relational fields to link photos to operations
    wizard_id = fields.Many2one('mobile.bin.key.wizard', string="Related Wizard")

    # Work Order and FSM Integration
    fsm_task_id = fields.Many2one('project.task', string="FSM Task",
                                  domain=[('is_fsm', '=', True)],
                                  help="Related Field Service Management task")
    work_order_reference = fields.Reference([
        ('container.destruction.work.order', 'Container Destruction Work Order'),
        ('container.retrieval.work.order', 'Container Retrieval Work Order'),
        ('container.access.work.order', 'Container Access Work Order'),
        ('work.order.shredding', 'Shredding Work Order'),
        ('project.task', 'Project Task/FSM Task')
    ], string="Work Order", help="Related work order for this photo")

    # Business Entity Relationships
    container_id = fields.Many2one('records.container', string="Container",
                                   help="Related container for this photo")
    destruction_request_id = fields.Many2one('records.destruction', string="Destruction Request",
                                             help="Related destruction request")
    pickup_request_id = fields.Many2one('pickup.request', string="Pickup Request",
                                        help="Related pickup request")
    partner_id = fields.Many2one('res.partner', string="Customer",
                                 help="Customer related to this photo")

    # Auto-computed from relationships
    project_id = fields.Many2one('project.project', string="Project",
                                 related='fsm_task_id.project_id', store=True)

    # Photo Data
    photo_data = fields.Binary(string="Photo", required=True, attachment=True)
    photo_filename = fields.Char(string="Filename")
    photo_date = fields.Datetime(string="Date Taken", default=fields.Datetime.now)

    # Geolocation
    gps_latitude = fields.Float(string="GPS Latitude", digits=(10, 7))
    gps_longitude = fields.Float(string="GPS Longitude", digits=(10, 7))
    has_gps = fields.Boolean(string="Has GPS Data", compute='_compute_has_gps', store=True)

    # Metadata
    photo_type = fields.Selection([
        ('before_service', 'Before Service'),
        ('after_service', 'After Service'),
        ('damage_report', 'Damage Report'),
        ('compliance_proof', 'Compliance Proof'),
        ('container_condition', 'Container Condition'),
        ('pickup_documentation', 'Pickup Documentation'),
        ('destruction_evidence', 'Destruction Evidence'),
        ('equipment_status', 'Equipment Status'),
        ('other', 'Other')
    ], string="Photo Type", default='other')
    device_info = fields.Char(string="Device Info")
    file_size = fields.Integer(string="File Size (Bytes)")
    resolution = fields.Char(string="Resolution (WxH)")

    # Compliance and Documentation
    is_compliance_photo = fields.Boolean(string="Compliance Photo",
                                         help="Mark if this photo is required for compliance")
    compliance_notes = fields.Text(string="Compliance Notes")

    # ============================================================================
    # COMPUTE & CONSTRAINS
    # ============================================================================
    @api.depends('gps_latitude', 'gps_longitude')
    def _compute_has_gps(self):
        """Check if photo has GPS coordinates."""
        for record in self:
            record.has_gps = bool(record.gps_latitude and record.gps_longitude)

    @api.onchange('fsm_task_id')
    def _onchange_fsm_task_id(self):
        """Auto-populate related fields when FSM task is selected."""
        if self.fsm_task_id:
            self.partner_id = self.fsm_task_id.partner_id
            # Set FSM task as work order reference
            self.work_order_reference = self.fsm_task_id

    @api.onchange('work_order_reference')
    def _onchange_work_order_reference(self):
        """Auto-populate related fields when work order is selected."""
        if self.work_order_reference:
            if hasattr(self.work_order_reference, 'partner_id'):
                self.partner_id = self.work_order_reference.partner_id
            if hasattr(self.work_order_reference, 'fsm_task_id'):
                self.fsm_task_id = self.work_order_reference.fsm_task_id

    @api.onchange('container_id')
    def _onchange_container_id(self):
        """Auto-populate customer from container."""
        if self.container_id:
            self.partner_id = self.container_id.partner_id

    @api.constrains('gps_latitude')
    def _check_gps_latitude(self):
        """Validate GPS latitude range."""
        for record in self:
            if record.gps_latitude and not -90 <= record.gps_latitude <= 90:
                raise ValidationError(_('GPS latitude must be between -90 and 90 degrees.'))

    @api.constrains('gps_longitude')
    def _check_gps_longitude(self):
        """Validate GPS longitude range."""
        for record in self:
            if record.gps_longitude and not -180 <= record.gps_longitude <= 180:
                raise ValidationError(_('GPS longitude must be between -180 and 180 degrees.'))

    @api.constrains('file_size')
    def _check_file_size(self):
        """Validate reasonable file size limits."""
        for record in self:
            if record.file_size and record.file_size > 50 * 1024 * 1024:  # 50MB limit
                raise ValidationError(_('Photo file size cannot exceed 50MB.'))
            if record.file_size and record.file_size < 0:
                raise ValidationError(_('Photo file size cannot be negative.'))

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_view_photo(self):
        """Open photo in a new form view."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Photo: %s', self.name),
            'res_model': 'mobile.photo',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_view_related_fsm_task(self):
        """Open related FSM task."""
        self.ensure_one()
        if not self.fsm_task_id:
            raise UserError(_('No FSM task linked to this photo.'))

        return {
            'type': 'ir.actions.act_window',
            'name': _('FSM Task: %s', self.fsm_task_id.name),
            'res_model': 'project.task',
            'res_id': self.fsm_task_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_related_work_order(self):
        """Open related work order."""
        self.ensure_one()
        if not self.work_order_reference:
            raise UserError(_('No work order linked to this photo.'))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Work Order: %s', self.work_order_reference.name),
            'res_model': self.work_order_reference._name,
            'res_id': self.work_order_reference.id,
            'view_mode': 'form',
            'target': 'current',
        }

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    def get_gps_coordinates_string(self):
        """Get formatted GPS coordinates string."""
        self.ensure_one()
        if self.has_gps:
            return _("Lat: %s, Lon: %s", self.gps_latitude, self.gps_longitude)
        return _("No GPS coordinates available")

    def get_related_entity_name(self):
        """Get the name of the primary related entity."""
        self.ensure_one()
        if self.fsm_task_id:
            return f"FSM Task: {self.fsm_task_id.name}"
        elif self.work_order_reference:
            return f"Work Order: {self.work_order_reference.name}"
        elif self.container_id:
            return f"Container: {self.container_id.name}"
        elif self.destruction_request_id:
            return f"Destruction: {self.destruction_request_id.name}"
        elif self.pickup_request_id:
            return f"Pickup: {self.pickup_request_id.name}"
        return _("No related entity")

    @api.model
    def create_from_mobile_data(self, mobile_data):
        """Create a photo record from mobile device data payload."""
        vals = {
            'name': mobile_data.get('name', _('Mobile Photo')),
            'photo_data': mobile_data.get('photo_data'),
            'photo_filename': mobile_data.get('filename'),
            'photo_type': mobile_data.get('photo_type', 'other'),
            'gps_latitude': mobile_data.get('gps_latitude'),
            'gps_longitude': mobile_data.get('gps_longitude'),
            'device_info': mobile_data.get('device_info'),
            'file_size': mobile_data.get('file_size'),
            'resolution': mobile_data.get('resolution'),
            'wizard_id': mobile_data.get('wizard_id'),
            'fsm_task_id': mobile_data.get('fsm_task_id'),
            'work_order_reference': mobile_data.get('work_order_reference'),
            'container_id': mobile_data.get('container_id'),
            'destruction_request_id': mobile_data.get('destruction_request_id'),
            'pickup_request_id': mobile_data.get('pickup_request_id'),
            'partner_id': mobile_data.get('partner_id'),
            'is_compliance_photo': mobile_data.get('is_compliance_photo', False),
            'compliance_notes': mobile_data.get('compliance_notes'),
        }
        return self.create(vals)

    def link_to_fsm_task(self, task_id):
        """Link this photo to an FSM task."""
        self.ensure_one()
        task = self.env['project.task'].browse(task_id)
        if not task.exists() or not task.is_fsm:
            raise UserError(_('Invalid FSM task.'))

        self.write({
            'fsm_task_id': task_id,
            'partner_id': task.partner_id.id,
            'project_id': task.project_id.id,
        })

    def link_to_work_order(self, work_order_id):
        """Link this photo to a work order."""
        self.ensure_one()
        work_order = self.env['records.work.order'].browse(work_order_id)
        if not work_order.exists():
            raise UserError(_('Invalid work order.'))

        vals = {
            'work_order_id': work_order_id,
            'partner_id': work_order.partner_id.id,
        }

        # Also link FSM task if work order has one
        if hasattr(work_order, 'fsm_task_id') and work_order.fsm_task_id:
            vals['fsm_task_id'] = work_order.fsm_task_id.id
            vals['project_id'] = work_order.fsm_task_id.project_id.id

        self.write(vals)

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    def name_get(self):
        """Custom display name for photo records."""
        result = []
        for record in self:
            name = record.photo_filename or record.name or _('Unnamed Photo')
            if record.photo_date:
                name = f"{name} ({record.photo_date.strftime('%Y-%m-%d')})"

            # Add related entity info
            related_entity = record.get_related_entity_name()
            if related_entity != _("No related entity"):
                name = f"{name} - {related_entity}"

            result.append((record.id, name))
        return result

    @api.model
    def get_photos_for_fsm_task(self, task_id):
        """Get all photos linked to a specific FSM task."""
        return self.search([('fsm_task_id', '=', task_id)])

    @api.model
    def get_photos_for_work_order(self, work_order_id):
        """Get all photos linked to a specific work order."""
        return self.search([('work_order_id', '=', work_order_id)])

    @api.model
    def get_compliance_photos(self, entity_type=None, entity_id=None):
        """Get compliance photos, optionally filtered by entity."""
        domain = [('is_compliance_photo', '=', True)]

        if entity_type and entity_id:
            if entity_type == 'fsm_task':
                domain.append(('fsm_task_id', '=', entity_id))
            elif entity_type == 'work_order':
                domain.append(('work_order_id', '=', entity_id))
            elif entity_type == 'container':
                domain.append(('container_id', '=', entity_id))
            elif entity_type == 'destruction_request':
                domain.append(('destruction_request_id', '=', entity_id))

        return self.search(domain)

