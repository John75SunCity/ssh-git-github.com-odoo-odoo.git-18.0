from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class RecordsContainerTypeConverter(models.TransientModel):
    _name = 'records.container.type.converter'
    _description = 'Wizard: Convert Container Type'

    # ============================================================================
    # WIZARD FIELDS
    # ============================================================================
    container_ids = fields.Many2many('records.container', string="Containers to Convert", readonly=True)
    source_container_type_id = fields.Many2one('records.container.type', string="Source Type", readonly=True, compute='_compute_source_type')
    target_container_type_id = fields.Many2one('records.container.type', string="New Container Type", required=True)
    container_count = fields.Integer(string="Number of Containers", readonly=True, compute='_compute_container_count')

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('container_ids')
    def _compute_container_count(self):
        """Computes the number of containers selected for conversion."""
        for wizard in self:
            wizard.container_count = len(wizard.container_ids)

    @api.depends('container_ids')
    def _compute_source_type(self):
        """
        Determines the source container type.
        Assumes all selected containers are of the same type for simplicity.
        """
        for wizard in self:
            if wizard.container_ids:
                # All containers selected via the context action will have the same type.
                wizard.source_container_type_id = wizard.container_ids[0].container_type_id.id
            else:
                wizard.source_container_type_id = False

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('source_container_type_id', 'target_container_type_id')
    def _check_different_types(self):
        """Ensures the source and target types are not the same."""
        for wizard in self:
            if wizard.source_container_type_id and wizard.target_container_type_id and wizard.source_container_type_id == wizard.target_container_type_id:
                raise ValidationError(_("The new container type must be different from the current type."))

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_convert_containers(self):
        """
        Executes the conversion process.
        Updates the container type for all selected containers.
        """
        self.ensure_one()
        if not self.container_ids:
            raise UserError(_("There are no containers to convert."))
        if not self.target_container_type_id:
            raise UserError(_("You must select a new container type."))

        # Prepare a log message for the chatter of each container
        log_message = _("Container type converted from <b>%s</b> to <b>%s</b> by %s.") % (
            self.source_container_type_id.name,
            self.target_container_type_id.name,
            self.env.user.name)

        # Perform the bulk update
        self.container_ids.write({
            'container_type_id': self.target_container_type_id.id
        })

        # Post the log message to each affected container
        for container in self.container_ids:
            container.message_post(body=log_message)

        # Return a success notification to the user
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Conversion Successful"),
                'message': _('%d containers have been successfully converted to type "%s".') % (self.container_count, self.target_container_type_id.name),
                'type': 'success',
                'sticky': False,
            }
        }
