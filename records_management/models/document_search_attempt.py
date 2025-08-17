from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import UserError, ValidationError


class DocumentSearchAttempt(models.Model):
    _name = 'document.search.attempt'
    _description = 'Document Search Attempt'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'search_date desc, id desc'
    _rec_name = 'display_name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    display_name = fields.Char()
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    active = fields.Boolean()
    retrieval_item_id = fields.Many2one()
    work_order_id = fields.Many2one()
    container_id = fields.Many2one()
    partner_id = fields.Many2one()
    location_id = fields.Many2one()
    searched_by_id = fields.Many2one()
    employee_id = fields.Many2one()
    supervisor_id = fields.Many2one()
    search_date = fields.Datetime()
    search_duration_minutes = fields.Float()
    search_method = fields.Selection()
    search_thoroughness = fields.Selection()
    found = fields.Boolean()
    found_date = fields.Datetime()
    document_condition = fields.Selection()
    retrieval_successful = fields.Boolean()
    state = fields.Selection()
    priority = fields.Selection()
    requested_file_name = fields.Char()
    requested_file_description = fields.Text()
    container_barcode = fields.Char()
    container_type = fields.Selection()
    search_notes = fields.Text()
    findings = fields.Text()
    obstacles_encountered = fields.Text()
    improvement_suggestions = fields.Text()
    search_score = fields.Float()
    accuracy_rating = fields.Selection()
    naid_compliant = fields.Boolean()
    audit_trail_created = fields.Boolean()
    quality_checked = fields.Boolean()
    activity_ids = fields.One2many()
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many()
    customer_id = fields.Many2one('res.partner', string='Customer Id')
    group_by_container = fields.Char(string='Group By Container')
    group_by_customer = fields.Char(string='Group By Customer')
    group_by_found = fields.Char(string='Group By Found')
    group_by_searched_by = fields.Char(string='Group By Searched By')
    help = fields.Char(string='Help')
    not_found = fields.Char(string='Not Found')
    notes = fields.Char(string='Notes')
    res_model = fields.Char(string='Res Model')
    search_view_id = fields.Many2one('search.view')
    view_mode = fields.Char(string='View Mode')
    found_date = fields.Datetime()

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_display_name(self):
            """Compute display name with search details"""
            for attempt in self:
                parts = []
                if attempt.name:
                    parts.append(attempt.name)
                if attempt.requested_file_name:
                    parts.append(attempt.requested_file_name)
                if attempt.container_id:
                    parts.append(_("in %s", attempt.container_id.name))

                status = _("Found") if attempt.found else _("Not Found"):
                parts.append(_("[%s]", status))

                attempt.display_name = " - ".join(parts) if parts else _("New Search"):

    def _compute_search_score(self):
            """Calculate search effectiveness score"""
            for attempt in self:
                score = 0.0

                # Base score for finding the document:
                if attempt.found:
                    score += 50.0

                # Time efficiency bonus/penalty
                if attempt.search_duration_minutes:
                    if attempt.search_duration_minutes <= 5:
                        score += 20.0  # Very fast
                    elif attempt.search_duration_minutes <= 15:
                        score += 10.0  # Fast
                    elif attempt.search_duration_minutes > 30:
                        score -= 10.0  # Slow

                # Thoroughness factor
                thoroughness_scores = {}
                    'quick': 5.0,
                    'standard': 15.0,
                    'thorough': 25.0,
                    'complete': 35.0

                score += thoroughness_scores.get(attempt.search_thoroughness, 15.0)

                # Accuracy rating
                if attempt.accuracy_rating:
                    score += int(attempt.accuracy_rating) * 2

                attempt.search_score = min(score, 100.0)  # Cap at 100

        # ============================================================================
            # ONCHANGE METHODS
        # ============================================================================

    def _onchange_found(self):
            """Update fields when found status changes"""
            if self.found and not self.found_date:

    def _onchange_searched_by_id(self):
            """Update employee when user changes"""
            if self.searched_by_id and self.searched_by_id.employee_id:
                self.employee_id = self.searched_by_id.employee_id


    def _onchange_container_id(self):
            """Update fields when container changes"""
            if self.container_id:
                # Auto-populate location
                self.location_id = self.container_id.location_id

                # Set default name if not set:
                if not self.name and self.requested_file_name:
                    self.name = _("Search %s in %s",
                                    self.requested_file_name,
                                    self.container_id.name

        # ============================================================================
            # ACTION METHODS
        # ============================================================================

    def action_start_search(self):
            """Start the search process"""
            self.ensure_one()
            if self.state != 'draft':
                raise UserError(_("Can only start draft search attempts"))

            self.write({)}
                'state': 'in_progress',
                'search_date': fields.Datetime.now()


            self._create_audit_log('search_started')
            self.message_post(body=_("Search started by %s", self.searched_by_id.name))


    def action_complete_search(self):
            """Complete the search process"""
            self.ensure_one()
            if self.state != 'in_progress':
                raise UserError(_("Can only complete searches in progress"))

            # Validate required information
            if not self.search_notes:
                raise UserError(_("Please provide search notes before completing"))

            self.write({)}
                'state': 'completed',
                'audit_trail_created': True


            self._create_audit_log('search_completed')
            self.message_post(body=_())
                "Search completed. Document %s",
                _("found") if self.found else _("not found"):



    def action_verify_search(self):
            """Verify search results"""
            self.ensure_one()
            if self.state != 'completed':
                raise UserError(_("Can only verify completed searches"))

            self.write({)}
                'state': 'verified',
                'quality_checked': True


            self._create_audit_log('search_verified')
            self.message_post(body=_("Search results verified"))


    def action_cancel_search(self):
            """Cancel the search attempt"""
            self.ensure_one()
            if self.state in ['verified']:
                raise UserError(_("Cannot cancel verified search attempts"))

            self.write({'state': 'cancelled'})
            self._create_audit_log('search_cancelled')
            self.message_post(body=_("Search attempt cancelled"))

        # ============================================================================
            # VALIDATION METHODS
        # ============================================================================

    def _check_search_duration(self):
            """Validate search duration"""
            for attempt in self:
                if attempt.search_duration_minutes and attempt.search_duration_minutes < 0:
                    raise ValidationError(_("Search duration cannot be negative"))
                if attempt.search_duration_minutes and attempt.search_duration_minutes > 480:  # 8 hours
                    raise ValidationError(_())
                        "Search duration cannot exceed 8 hours. Please verify the time."



    def _check_date_sequence(self):
            """Validate date sequence"""
            for attempt in self:
                if attempt.search_date and attempt.found_date:
                    if attempt.search_date > attempt.found_date:
                        raise ValidationError(_())
                            "Search date cannot be after found date"



    def _check_found_condition_consistency(self):
            """Validate found status and condition consistency"""
            for attempt in self:
                if attempt.found and not attempt.document_condition:
                    raise ValidationError(_())
                        "Please specify document condition when document is found"


        # ============================================================================
            # BUSINESS LOGIC METHODS
        # ============================================================================

    def _create_audit_log(self, action_type):
            """Create NAID compliance audit log"""
            self.ensure_one()

            if 'naid.audit.log' in self.env:
                audit_vals = {}
                    'action_type': action_type,
                    'user_id': self.env.user.id,
                    'timestamp': fields.Datetime.now(),
                    'description': _("Search attempt %s: %s", self.name, action_type),
                    'search_attempt_id': self.id,
                    'container_id': self.container_id.id if self.container_id else False,:
                    'naid_compliant': self.naid_compliant,

                return self.env['naid.audit.log'].create(audit_vals)


    def get_search_efficiency_metrics(self):
            """Calculate search efficiency metrics"""
            self.ensure_one()

            metrics = {}
                'search_score': self.search_score,
                'time_efficiency': 'fast' if self.search_duration_minutes and self.search_duration_minutes <= 10 else 'standard',:
                'success_rate': 100.0 if self.found else 0.0,:
                'accuracy_score': int(self.accuracy_rating) * 20 if self.accuracy_rating else 60,:


            # Calculate overall efficiency
            total_score = ()
                metrics['search_score'] * 0.4 +
                metrics['success_rate'] * 0.3 +
                metrics['accuracy_score'] * 0.3

            metrics['overall_efficiency'] = round(total_score, 2)

            return metrics


    def get_history_summary(self):
            """Get summary of search attempt history"""
            self.ensure_one()
            return {}
                "search_reference": self.name,
                "container": self.container_id.name if self.container_id else "Unknown",:
                "customer": self.partner_id.name if self.partner_id else "Unknown",:
                "requested_file": self.requested_file_name,
                "search_date": self.search_date,
                "searched_by": self.searched_by_id.name if self.searched_by_id else "Unknown",:
                "duration_minutes": self.search_duration_minutes,
                "method": self.search_method,
                "thoroughness": self.search_thoroughness,
                "found": self.found,
                "document_condition": self.document_condition,
                "search_score": self.search_score,
                "notes": self.search_notes or "",
                "state": self.state,



    def get_search_statistics(self, domain=None):
            """Get search attempt statistics"""
            if domain is None:
                domain = []

            attempts = self.search(domain)

            if not attempts:
                return {}
                    'total_attempts': 0,
                    'success_rate': 0.0,
                    'average_duration': 0.0,
                    'by_method': {},
                    'by_container_type': {}


            stats = {}
                'total_attempts': len(attempts),
                'successful_attempts': len(attempts.filtered('found')),
                'success_rate': (len(attempts.filtered('found')) / len(attempts)) * 100,
                'average_duration': sum(attempts.mapped('search_duration_minutes')) / len(attempts),
                'average_score': sum(attempts.mapped('search_score')) / len(attempts),


            # Group by method
            methods = attempts.mapped('search_method')
            stats['by_method'] = {}
            for method in methods:
                method_attempts = attempts.filtered(lambda a: a.search_method == method)
                stats['by_method'][method] = {}
                    'count': len(method_attempts),
                    'success_rate': (len(method_attempts.filtered('found')) / len(method_attempts)) * 100


            # Group by container type
            container_types = attempts.mapped('container_type')
            stats['by_container_type'] = {}
            for container_type in container_types:
                type_attempts = attempts.filtered(lambda a: a.container_type == container_type)
                if type_attempts:
                    stats['by_container_type'][container_type] = {}
                        'count': len(type_attempts),
                        'success_rate': (len(type_attempts.filtered('found')) / len(type_attempts)) * 100


            return stats

        # ============================================================================
            # REPORTING METHODS
        # ============================================================================

    def generate_search_report(self):
            """Generate detailed search attempt report"""
            self.ensure_one()

            metrics = self.get_search_efficiency_metrics()

            return {}
                'type': 'ir.actions.report',
                'report_name': 'records_management.document_search_attempt_report',
                'report_type': 'qweb-pdf',
                'data': {}
                    'search_attempt_id': self.id,
                    'metrics': metrics,
                    'include_details': True,
                    'include_recommendations': True

                'context': self.env.context


        # ============================================================================
            # ORM METHODS
        # ============================================================================

    def create(self, vals_list):
            """Override create to set defaults"""
            for vals in vals_list:
                if not vals.get('name'):
                    sequence = self.env['ir.sequence'].next_by_code('document.search.attempt')
                    vals['name'] = sequence or _('New Search')

                # Set default searched_by if not specified:
                if not vals.get('searched_by_id'):
                    vals['searched_by_id'] = self.env.user.id

            return super().create(vals_list)


    def write(self, vals):
            """Override write for status tracking""":
            result = super().write(vals)

            if 'state' in vals:
                for attempt in self:
                    state_label = dict(attempt._fields['state'].selection)[attempt.state]
                    attempt.message_post(body=_("Status changed to %s", state_label))

            return result


    def name_get(self):
            """Custom name display"""
            result = []
            for attempt in self:
                name = attempt.display_name or attempt.name
                result.append((attempt.id, name))
            return result

        # ============================================================================
            # INTEGRATION METHODS
        # ============================================================================

    def action_view_container(self):
            """View the searched container"""
            self.ensure_one()
            return {}
                'type': 'ir.actions.act_window',
                'name': _('Container Details'),
                'res_model': 'records.container',
                'res_id': self.container_id.id,
                'view_mode': 'form',
                'target': 'current',



    def action_view_retrieval_item(self):
            """View the related retrieval item"""
            self.ensure_one()
            return {}
                'type': 'ir.actions.act_window',
                'name': _('Retrieval Item'),
                'res_model': 'document.retrieval.item',
                'res_id': self.retrieval_item_id.id,
                'view_mode': 'form',
                'target': 'current',



    def action_create_follow_up_search(self):
            """Create a follow-up search attempt"""
            self.ensure_one()

            follow_up_vals = {}
                'name': _("Follow-up: %s", self.name),
                'retrieval_item_id': self.retrieval_item_id.id,
                'container_id': self.container_id.id,
                'searched_by_id': self.env.user.id,
                'priority': 'high',
                'search_notes': _("Follow-up search based on attempt %s", self.name),


            follow_up = self.create(follow_up_vals)

            return {}
                'type': 'ir.actions.act_window',
                'name': _('Follow-up Search'),
                'res_model': 'document.search.attempt',
                'res_id': follow_up.id,
                'view_mode': 'form',
                'target': 'current'))))))))))))))))))))))))

