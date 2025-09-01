from odoo import api, models, fields


class AdvancedBillingLine(models.Model):
    _name = "advanced.billing.line"
    _description = "Advanced Billing Line"
    _order = "sequence, id"

    name = fields.Char(string="Description", required=True, help="Description of the billing line item")
    billing_id = fields.Many2one(
        comodel_name="records.billing", string="Billing Document", ondelete="cascade", index=True
    )
    billing_profile_id = fields.Many2one(
        comodel_name="advanced.billing.profile", string="Billing Profile", ondelete="cascade", index=True
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency", store=True, readonly=True, related="billing_id.currency_id"
    )

    # Line type and categorization
    type = fields.Selection(
        [("storage", "Storage"), ("service", "Service"), ("other", "Other")],
        string="Line Type",
        default="storage",
        required=True,
        help="Type of billing line",
    )

    # Financial fields
    amount = fields.Monetary(currency_field="currency_id", required=True, default=0.0)
    quantity = fields.Float(string="Quantity", default=1.0, help="Quantity for this line item")
    unit_price = fields.Monetary(
        string="Unit Price", currency_field="currency_id", compute="_compute_unit_price", store=True
    )
    discount = fields.Float(string="Discount (%)", default=0.0)
    discount_amount = fields.Monetary(
        string="Discount Amount", currency_field="currency_id", compute="_compute_discount_amount", store=True
    )
    subtotal = fields.Monetary(string="Subtotal", currency_field="currency_id", compute="_compute_subtotal", store=True)

    # Additional details
    product_id = fields.Many2one("product.product", string="Product/Service")
    notes = fields.Text(string="Notes")

    # Organization
    sequence = fields.Integer(string="Sequence", default=10)
    active = fields.Boolean(default=True)

    @api.depends("amount", "quantity")
    def _compute_unit_price(self):
        """Compute unit price from total amount and quantity"""
        for line in self:
            if line.quantity and line.quantity != 0:
                line.unit_price = line.amount / line.quantity
            else:
                line.unit_price = line.amount

    @api.depends("amount", "discount")
    def _compute_discount_amount(self):
        """Compute discount amount"""
        for line in self:
            line.discount_amount = line.amount * (line.discount / 100)

    @api.depends("amount", "discount_amount")
    def _compute_subtotal(self):
        """Compute subtotal after discount"""
        for line in self:
            line.subtotal = line.amount - line.discount_amount

    @api.onchange("product_id")
    def _onchange_product_id(self):
        """Update line details when product changes"""
        if self.product_id:
            self.name = self.product_id.name
            if self.product_id.list_price:
                self.unit_price = self.product_id.list_price
                self.amount = self.unit_price * self.quantity

    @api.onchange("quantity", "unit_price")
    def _onchange_quantity_unit_price(self):
        """Update amount when quantity or unit price changes"""
        self.amount = self.quantity * self.unit_price

    @api.onchange("discount")
    def _onchange_discount(self):
        """Update discount amount when discount percentage changes"""
        self.discount_amount = self.amount * (self.discount / 100)
