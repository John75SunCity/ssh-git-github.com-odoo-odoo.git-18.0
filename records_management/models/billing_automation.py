# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class RecordsBillingService(models.TransientModel):
    """Service for managing billing generation and automation"""
    _name = 'records.billing.service'
    _description = 'Billing Generation Service'

    def generate_monthly_billing(self, reference_date=None):
        """Generate all monthly billing for customers"""
        if not reference_date:
            reference_date = fields.Date.today()
        
        # Get all active billing profiles
        billing_profiles = self.env['records.customer.billing.profile'].search([('active', '=', True)])
        
        generated_periods = []
        
        for profile in billing_profiles:
            # Generate storage billing if due
            if self._is_storage_billing_due(profile, reference_date):
                storage_period = self._generate_storage_billing(profile, reference_date)
                if storage_period:
                    generated_periods.append(storage_period)
            
            # Generate service billing if due
            if self._is_service_billing_due(profile, reference_date):
                service_period = self._generate_service_billing(profile, reference_date)
                if service_period:
                    generated_periods.append(service_period)
        
        return generated_periods
    
    def _is_storage_billing_due(self, profile, reference_date):
        """Check if storage billing is due for this profile"""
        if not profile.auto_generate_storage_invoices:
            return False
        
        # Check if we already have a billing period for this month
        next_billing_date = profile.get_next_billing_date('storage', reference_date)
        
        # If next billing date is today or in the past, billing is due
        return next_billing_date <= reference_date
    
    def _is_service_billing_due(self, profile, reference_date):
        """Check if service billing is due for this profile"""
        if not profile.auto_generate_service_invoices:
            return False
        
        # Service billing is typically monthly in arrears
        # Check if we have unbilled completed services from previous month
        last_month_start = reference_date.replace(day=1) - relativedelta(months=1)
        last_month_end = reference_date.replace(day=1) - timedelta(days=1)
        
        # Check for unbilled work orders
        retrieval_orders = self._get_unbilled_retrieval_orders(profile.partner_id, last_month_start, last_month_end)
        shredding_orders = self._get_unbilled_shredding_orders(profile.partner_id, last_month_start, last_month_end)
        
        return len(retrieval_orders) > 0 or len(shredding_orders) > 0
    
    def _generate_storage_billing(self, profile, reference_date):
        """Generate storage billing period for a profile"""
        # Calculate period dates
        start_date, end_date = profile.get_billing_period_dates('storage', reference_date)
        
        # Check if period already exists
        existing_period = self.env['records.advanced.billing.period'].search([
            ('billing_profile_id', '=', profile.id),
            ('billing_type', 'in', ['storage', 'combined']),
            ('period_start_date', '=', start_date),
            ('period_end_date', '=', end_date)
        ], limit=1)
        
        if existing_period:
            return existing_period
        
        # Create new billing period
        period_vals = {
            'name': f"Storage Billing - {profile.partner_id.name} - {start_date.strftime('%B %Y')}",
            'billing_profile_id': profile.id,
            'billing_type': 'storage',
            'invoice_date': reference_date,
            'period_start_date': start_date,
            'period_end_date': end_date,
        }
        
        period = self.env['records.advanced.billing.period'].create(period_vals)
        
        # Generate storage lines
        period.action_generate_storage_lines()
        
        # Auto-confirm if configured
        if profile.auto_generate_storage_invoices:
            period.write({'state': 'confirmed'})
            
            # Auto-generate invoice if configured
            if profile.auto_send_invoices:
                period.action_generate_invoice()
        
        return period
    
    def _generate_service_billing(self, profile, reference_date):
        """Generate service billing period for a profile"""
        # Service billing is in arrears for previous month
        end_date = reference_date.replace(day=1) - timedelta(days=1)
        start_date = end_date.replace(day=1)
        
        # Check if period already exists
        existing_period = self.env['records.advanced.billing.period'].search([
            ('billing_profile_id', '=', profile.id),
            ('billing_type', 'in', ['service', 'combined']),
            ('period_start_date', '=', start_date),
            ('period_end_date', '=', end_date)
        ], limit=1)
        
        if existing_period:
            return existing_period
        
        # Create new billing period
        period_vals = {
            'name': f"Service Billing - {profile.partner_id.name} - {start_date.strftime('%B %Y')}",
            'billing_profile_id': profile.id,
            'billing_type': 'service',
            'invoice_date': reference_date,
            'period_start_date': start_date,
            'period_end_date': end_date,
        }
        
        period = self.env['records.advanced.billing.period'].create(period_vals)
        
        # Generate service lines
        period.action_generate_service_lines()
        
        # Only create if there are actual services to bill
        if period.service_amount > 0:
            # Auto-confirm if configured
            if profile.auto_generate_service_invoices:
                period.write({'state': 'confirmed'})
                
                # Auto-generate invoice if configured
                if profile.auto_send_invoices:
                    period.action_generate_invoice()
            
            return period
        else:
            # Delete empty period
            period.unlink()
            return None
    
    def _get_unbilled_retrieval_orders(self, partner, start_date, end_date):
        """Get unbilled retrieval work orders for period"""
        return self.env['document.retrieval.work.order'].search([
            ('partner_id', '=', partner.id),
            ('state', '=', 'completed'),
            ('actual_completion_time', '>=', fields.Datetime.combine(start_date, datetime.min.time())),
            ('actual_completion_time', '<=', fields.Datetime.combine(end_date, datetime.max.time())),
            # Add condition to check if not already billed
            ('id', 'not in', self._get_billed_retrieval_order_ids(partner))
        ])
    
    def _get_unbilled_shredding_orders(self, partner, start_date, end_date):
        """Get unbilled shredding work orders for period"""
        return self.env['work.order.shredding'].search([
            ('partner_id', '=', partner.id),
            ('state', '=', 'completed'),
            ('actual_completion_time', '>=', fields.Datetime.combine(start_date, datetime.min.time())),
            ('actual_completion_time', '<=', fields.Datetime.combine(end_date, datetime.max.time())),
            # Add condition to check if not already billed
            ('id', 'not in', self._get_billed_shredding_order_ids(partner))
        ])
    
    def _get_billed_retrieval_order_ids(self, partner):
        """Get IDs of already billed retrieval orders"""
        billed_lines = self.env['records.billing.line'].search([
            ('customer_id', '=', partner.id),
            ('retrieval_work_order_id', '!=', False)
        ])
        return billed_lines.mapped('retrieval_work_order_id').ids
    
    def _get_billed_shredding_order_ids(self, partner):
        """Get IDs of already billed shredding orders"""
        billed_lines = self.env['records.billing.line'].search([
            ('customer_id', '=', partner.id),
            ('shredding_work_order_id', '!=', False)
        ])
        return billed_lines.mapped('shredding_work_order_id').ids
    
    def generate_combined_billing(self, partner_id, reference_date=None):
        """Generate combined storage and service billing for a customer"""
        if not reference_date:
            reference_date = fields.Date.today()
        
        partner = self.env['res.partner'].browse(partner_id)
        profile = self.env['records.customer.billing.profile'].search([
            ('partner_id', '=', partner_id),
            ('active', '=', True)
        ], limit=1)
        
        if not profile:
            raise UserError(_('No active billing profile found for customer %s') % partner.name)
        
        # Calculate storage period (forward billing)
        storage_start, storage_end = profile.get_billing_period_dates('storage', reference_date)
        
        # Calculate service period (arrears billing)
        service_end = reference_date.replace(day=1) - timedelta(days=1)
        service_start = service_end.replace(day=1)
        
        # Create combined billing period
        period_vals = {
            'name': f"Combined Billing - {partner.name} - {reference_date.strftime('%B %Y')}",
            'billing_profile_id': profile.id,
            'billing_type': 'combined',
            'invoice_date': reference_date,
            'period_start_date': storage_start,  # Use storage period as primary
            'period_end_date': storage_end,
        }
        
        period = self.env['records.advanced.billing.period'].create(period_vals)
        
        # Generate both storage and service lines
        period.action_generate_storage_lines()
        
        # Generate service lines for the service period
        period.period_start_date = service_start
        period.period_end_date = service_end
        period.action_generate_service_lines()
        
        # Reset period dates to storage period
        period.period_start_date = storage_start
        period.period_end_date = storage_end
        
        return period

class RecordsBillingCronJobs(models.Model):
    """Cron job management for automated billing"""
    _name = 'records.billing.cron'
    _description = 'Billing Cron Jobs'

    @api.model
    def run_monthly_billing_generation(self):
        """Cron job to run monthly billing generation"""
        billing_service = self.env['records.billing.service']
        
        try:
            generated_periods = billing_service.generate_monthly_billing()
            
            # Log success
            self.env['ir.logging'].create({
                'name': 'Monthly Billing Generation',
                'level': 'info',
                'message': f'Successfully generated {len(generated_periods)} billing periods'
            })
            
        except Exception as e:
            # Log error
            self.env['ir.logging'].create({
                'name': 'Monthly Billing Generation',
                'level': 'error',
                'message': f'Error generating monthly billing: {str(e)}'
            })
            raise
    
    @api.model
    def run_quarterly_storage_billing(self):
        """Cron job specifically for quarterly storage billing"""
        profiles = self.env['records.customer.billing.profile'].search([
            ('storage_billing_cycle', '=', 'quarterly'),
            ('active', '=', True)
        ])
        
        billing_service = self.env['records.billing.service']
        
        for profile in profiles:
            try:
                if billing_service._is_storage_billing_due(profile, fields.Date.today()):
                    billing_service._generate_storage_billing(profile, fields.Date.today())
            except Exception as e:
                # Log individual profile errors but continue processing
                self.env['ir.logging'].create({
                    'name': 'Quarterly Storage Billing',
                    'level': 'error',
                    'message': f'Error billing customer {profile.partner_id.name}: {str(e)}'
                })
