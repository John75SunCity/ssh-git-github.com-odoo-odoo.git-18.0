from odoo import models, fields, api
from datetime import datetime, timedelta

class RecordsChainCustody(models.Model):
    _name = 'records.chain.custody'
    _description = 'Records Chain of Custody Log'
    _order = 'custody_timestamp desc'

    document_id = fields.Many2one('records.document', string='Document', required=True, ondelete='cascade')
    box_id = fields.Many2one('records.box', string='Box', ondelete='cascade')
    custody_timestamp = fields.Datetime('Custody Time', required=True, default=fields.Datetime.now)
    
    # Custody transfer details
    from_user_id = fields.Many2one('res.users', string='From User')
    to_user_id = fields.Many2one('res.users', string='To User', required=True)
    current_user_id = fields.Many2one('res.users', string='Current Custodian', default=lambda self: self.env.user)
    
    custody_action = fields.Selection([
        ('created', 'Document Created'),
        ('transferred', 'Custody Transferred'),
        ('accessed', 'Document Accessed'),
        ('modified', 'Document Modified'),
        ('copied', 'Document Copied'),
        ('moved', 'Document Moved'),
        ('archived', 'Document Archived'),
        ('destroyed', 'Document Destroyed'),
        ('digitized', 'Document Digitized'),
        ('reviewed', 'Document Reviewed')
    ], string='Custody Action', required=True, default='transferred')
    
    # Location tracking
    from_location_id = fields.Many2one('records.location', string='From Location')
    to_location_id = fields.Many2one('records.location', string='To Location')
    current_location_id = fields.Many2one('records.location', string='Current Location')
    
    # Transfer details
    transfer_reason = fields.Text('Transfer Reason', required=True)
    authorization_code = fields.Char('Authorization Code')
    witness_user_id = fields.Many2one('res.users', string='Witness')
    
    # Documentation
    transfer_notes = fields.Text('Transfer Notes')
    condition_before = fields.Text('Document Condition Before')
    condition_after = fields.Text('Document Condition After')
    
    # Digital signatures
    from_signature = fields.Binary('From User Signature')
    to_signature = fields.Binary('To User Signature')
    witness_signature = fields.Binary('Witness Signature')
    
    # Compliance and security
    security_level = fields.Selection([
        ('standard', 'Standard'),
        ('high', 'High Security'),
        ('classified', 'Classified'),
        ('restricted', 'Restricted Access')
    ], string='Security Level', default='standard')
    
    compliance_verified = fields.Boolean('Compliance Verified', default=False)
    audit_required = fields.Boolean('Audit Required', default=False)
    
    # Chain integrity
    previous_custody_id = fields.Many2one('records.chain.custody', string='Previous Custody Record')
    next_custody_id = fields.Many2one('records.chain.custody', string='Next Custody Record')
    chain_broken = fields.Boolean('Chain Broken', default=False)
    break_reason = fields.Text('Chain Break Reason')
    
    # Analytics
    custody_duration = fields.Float('Custody Duration (hours)', compute='_compute_custody_duration', store=True)
    compliance_score = fields.Float('Compliance Score', compute='_compute_compliance_score', store=True)
    
    @api.depends('custody_timestamp', 'next_custody_id.custody_timestamp')
    def _compute_custody_duration(self):
        """Compute how long custody was held"""
        for record in self:
            if record.next_custody_id and record.next_custody_id.custody_timestamp:
                delta = record.next_custody_id.custody_timestamp - record.custody_timestamp
                record.custody_duration = delta.total_seconds() / 3600  # Convert to hours
            else:
                # Still in custody - calculate current duration
                delta = fields.Datetime.now() - record.custody_timestamp
                record.custody_duration = delta.total_seconds() / 3600
    
    @api.depends('from_signature', 'to_signature', 'witness_signature', 'compliance_verified', 'chain_broken')
    def _compute_compliance_score(self):
        """Compute compliance score for this custody transfer"""
        for record in self:
            score = 50  # Base score
            
            # Signature completeness
            if record.from_signature:
                score += 15
            if record.to_signature:
                score += 15
            if record.witness_signature:
                score += 10
            
            # Compliance verification
            if record.compliance_verified:
                score += 10
            
            # Chain integrity
            if record.chain_broken:
                score -= 30
            
            # Required fields completeness
            if record.transfer_reason:
                score += 5
            if record.authorization_code:
                score += 5
            
            record.compliance_score = min(max(score, 0), 100)
    
    def action_verify_compliance(self):
        """Mark custody transfer as compliance verified"""
        self.write({'compliance_verified': True})
    
    def action_break_chain(self, reason):
        """Mark chain of custody as broken with reason"""
        self.write({
            'chain_broken': True,
            'break_reason': reason
        })
    
    @api.model
    def create_custody_record(self, document_id, action, to_user_id, **kwargs):
        """Helper method to create custody records"""
        values = {
            'document_id': document_id,
            'custody_action': action,
            'to_user_id': to_user_id,
            'transfer_reason': kwargs.get('reason', f'Document {action}'),
        }
        values.update(kwargs)
        return self.create(values)
