from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    def action_create_work_order(self):
        self.ensure_one()
        if self.state != 'sale':
            raise UserError(_('Please confirm the quote first.'))
        
        # Assume shredding if any line is shredding
        is_shredding = any(line.product_id.name == 'Shredding Box' for line in self.order_line)
        
        wo_model = 'work.order.shredding' if is_shredding else 'project.task'  # or other model
        
        wo_vals = {
            'name': self.name,
            'partner_id': self.partner_id.id,
            'sale_order_id': self.id,
            # Add more mappings as needed
        }
        
        if is_shredding:
            boxes = sum(line.product_uom_qty for line in self.order_line if line.product_id.name == 'Shredding Box')
            wo_vals['boxes_count'] = boxes
        
        wo = self.env[wo_model].create(wo_vals)
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': wo_model,
            'view_mode': 'form',
            'res_id': wo.id,
            'target': 'current',
        }
