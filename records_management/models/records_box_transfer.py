from odoo import models, fields, api
from datetime import datetime, timedelta

class RecordsBoxTransfer(models.Model):
    _name = 'records.box.transfer'
    _description = 'Records Box Transfer Log'
    _order = 'transfer_date desc'

    box_id = fields.Many2one('records.box', string='Box', required=True, ondelete='cascade')
    transfer_date = fields.Datetime('Transfer Date', required=True, default=fields.Datetime.now)
    
    # Transfer details
    from_location_id = fields.Many2one('records.location', string='From Location', required=True)
    to_location_id = fields.Many2one('records.location', string='To Location', required=True)
    
    from_user_id = fields.Many2one('res.users', string='From User')
    to_user_id = fields.Many2one('res.users', string='To User', required=True)
    authorized_by = fields.Many2one('res.users', string='Authorized By', default=lambda self: self.env.user)
    
    # Transfer reasons and documentation
    transfer_reason = fields.Selection([
        ('routine', 'Routine Move'),
        ('retrieval', 'Document Retrieval'),
        ('audit', 'Audit Requirement'),
        ('destruction', 'Scheduled Destruction'),
        ('digitization', 'Digitization Process'),
        ('customer_request', 'Customer Request'),
        ('maintenance', 'Facility Maintenance'),
        ('reorganization', 'Storage Reorganization'),
        ('emergency', 'Emergency Move')
    
    transfer_notes = fields.Text('Transfer Notes')
    special_instructions = fields.Text('Special Instructions')
    
    # Transfer method and logistics
    transport_method = fields.Selection([
        ('manual', 'Manual Carry'),
        ('cart', 'Storage Cart'),
        ('truck', 'Truck/Vehicle'),
        ('forklift', 'Forklift'),
        ('conveyor', 'Conveyor System')
    
    # Tracking and verification
    tracking_number = fields.Char('Tracking Number')
    barcode_scanned = fields.Boolean('Barcode Scanned', default=False)
    verification_code = fields.Char('Verification Code')
    
    # Condition assessment
    condition_before = fields.Selection([
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
        ('damaged', 'Damaged')
    
    condition_after = fields.Selection([
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
        ('damaged', 'Damaged')
    
    # Digital signatures
    from_signature = fields.Binary('From User Signature')
    to_signature = fields.Binary('To User Signature')
    
    # Status tracking
    transfer_status = fields.Selection([
        ('pending', 'Pending'),
        ('in_transit', 'In Transit'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled')
    
    completion_date = fields.Datetime('Completion Date')
    
    # Analytics
    transfer_duration = fields.Float('Transfer Duration (minutes)', compute='_compute_transfer_duration', store=True)
    efficiency_score = fields.Float('Transfer Efficiency Score', compute='_compute_efficiency_score', store=True)
    
    @api.depends('transfer_date', 'completion_date')
    def _compute_transfer_duration(self):
        """Compute transfer duration in minutes"""
        for transfer in self:
            if transfer.completion_date and transfer.transfer_date:
                delta = transfer.completion_date - transfer.transfer_date
                transfer.transfer_duration = delta.total_seconds() / 60
            else:
                transfer.transfer_duration = 0
    
    @api.depends('transfer_duration', 'condition_before', 'condition_after', 'barcode_scanned', 'from_signature', 'to_signature')
    def _compute_efficiency_score(self):
        """Compute transfer efficiency score"""
        for transfer in self:
            score = 50  # Base score
            
            # Duration efficiency (assuming 15 minutes is optimal)
            if transfer.transfer_duration > 0:
                if transfer.transfer_duration <= 15:
                    score += 20
                elif transfer.transfer_duration <= 30:
                    score += 15
                elif transfer.transfer_duration <= 60:
                    score += 10
                else:
                    score += 5
            
            # Condition maintenance
            condition_values = {'excellent': 5, 'good': 4, 'fair': 3, 'poor': 2, 'damaged': 1}
            before_val = condition_values.get(transfer.condition_before, 3)
            after_val = condition_values.get(transfer.condition_after, 3)
            
            if after_val >= before_val:
                score += 15
            else:
                score -= 10  # Condition deteriorated
            
            # Process compliance
            if transfer.barcode_scanned:
                score += 10
            if transfer.from_signature:
                score += 5
            if transfer.to_signature:
                score += 5
            
            transfer.efficiency_score = min(max(score, 0), 100)
    
    def action_start_transfer(self):
        """Mark transfer as started"""
        self.write({
            'transfer_status': 'in_transit',
            'transfer_date': fields.Datetime.now()
        })
    
    def action_complete_transfer(self):
        """Mark transfer as completed"""
        self.write({
            'transfer_status': 'completed',
            'completion_date': fields.Datetime.now()
        })
        
        # Update box location
        if self.box_id and self.to_location_id:
            self.box_id.write({'location_id': self.to_location_id.id})
    
    def action_cancel_transfer(self):
        """Cancel the transfer"""
        self.write({'transfer_status': 'cancelled'})
    
    @api.model
    def create_transfer(self, box_id, to_location_id, reason='routine', **kwargs):
        """Helper method to create transfers"""
        box = self.env['records.box'].browse(box_id)
        values = {
            'box_id': box_id,
            'from_location_id': box.location_id.id if box.location_id else False,
            'to_location_id': to_location_id,
            'transfer_reason': reason,
        }
        values.update(kwargs)
        return self.create(values)
