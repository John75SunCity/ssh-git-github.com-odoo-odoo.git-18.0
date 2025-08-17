from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression


class PaperBale(models.Model):
    _name = 'paper.bale'
    _description = 'Paper Bale'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'
    _rec_name = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    active = fields.Boolean()
    sequence = fields.Integer()
    reference_number = fields.Char()
    external_reference = fields.Char()
    barcode = fields.Char(string='Barcode')
    state = fields.Selection()
    weight = fields.Float()
    weight_unit = fields.Selection()
    paper_type = fields.Selection()
    bale_type = fields.Selection()
    paper_grade = fields.Selection()
    contamination_level = fields.Selection()
    pickup_location_id = fields.Many2one()
    current_location_id = fields.Many2one()
    destination_location_id = fields.Many2one()
    transportation_method = fields.Selection()
    creation_date = fields.Date()
    weigh_date = fields.Date()
    quality_check_date = fields.Date()
    pickup_date = fields.Date()
    delivery_date = fields.Date()
    recycling_date = fields.Date()
    customer_id = fields.Many2one()
    recycling_vendor_id = fields.Many2one()
    driver_id = fields.Many2one()
    trailer_id = fields.Many2one()
    confidentiality_level = fields.Selection()
    certificate_of_destruction = fields.Boolean()
    chain_of_custody_verified = fields.Boolean()
    naid_compliant = fields.Boolean()
    currency_id = fields.Many2one()
    sale_price = fields.Monetary()
    processing_cost = fields.Monetary()
    transportation_cost = fields.Monetary()
    net_value = fields.Monetary()
    recycling_category = fields.Selection()
    carbon_footprint = fields.Float()
    trees_saved = fields.Float()
    quality_grade_qc = fields.Char()
    quality_notes = fields.Text()
    moisture_content = fields.Float()
    density = fields.Float()
    action_date = fields.Date()
    action_type = fields.Selection()
    bale_number = fields.Char()
    bale_status = fields.Selection()
    contamination_found = fields.Boolean()
    contamination_percentage = fields.Float()
    customer_name = fields.Char()
    destruction_date = fields.Date()
    document_name = fields.Char()
    document_type = fields.Char()
    estimated_value = fields.Monetary()
    grade_assigned = fields.Char()
    inspection_date = fields.Date()
    inspection_type = fields.Selection()
    inspector = fields.Char()
    loaded_by = fields.Char()
    loaded_on_trailer = fields.Boolean()
    loading_date = fields.Date()
    loading_notes = fields.Text()
    loading_order = fields.Integer()
    loading_position = fields.Char()
    market_price_per_lb = fields.Float()
    measured_by = fields.Char()
    measurement_date = fields.Date()
    measurement_type = fields.Selection()
    moisture_reading = fields.Float()
    naid_compliance_verified = fields.Boolean()
    passed_inspection = fields.Boolean()
    performed_by = fields.Char()
    processing_time = fields.Float()
    quality_grade = fields.Selection()
    quality_score = fields.Float()
    revenue_potential = fields.Monetary()
    scale_used = fields.Char()
    source_facility = fields.Char()
    special_handling = fields.Boolean()
    trailer_info = fields.Char()
    trailer_load_count = fields.Integer()
    variance_from_previous = fields.Float()
    weighed_by = fields.Char()
    weight_contributed = fields.Float()
    weight_efficiency = fields.Float()
    weight_recorded = fields.Float()
    carbon_footprint_saved = fields.Float()
    carbon_neutral = fields.Boolean()
    energy_saved = fields.Float()
    environmental_certification = fields.Selection()
    sustainable_source = fields.Boolean()
    trees_saved_equivalent = fields.Float()
    water_saved = fields.Float()
    loading_history_ids = fields.One2many()
    quality_inspection_ids = fields.One2many()
    weight_history_count = fields.Integer()
    weight_measurement_ids = fields.One2many()
    total_volume = fields.Float()
    document_count = fields.Integer()
    description = fields.Text()
    notes = fields.Text()
    special_instructions = fields.Text()
    source_document_ids = fields.One2many()
    movement_ids = fields.One2many()
    inspection_ids = fields.One2many()
    partner_id = fields.Many2one()
    activity_ids = fields.One2many()
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many()
    load_shipment_id = fields.Many2one()
    load_id = fields.Many2one('load')
    action_load_trailer = fields.Char(string='Action Load Trailer')
    action_move_to_storage = fields.Char(string='Action Move To Storage')
    action_print_label = fields.Char(string='Action Print Label')
    action_quality_inspection = fields.Char(string='Action Quality Inspection')
    action_view_inspection_details = fields.Char(string='Action View Inspection Details')
    action_view_source_documents = fields.Char(string='Action View Source Documents')
    action_view_trailer_info = fields.Char(string='Action View Trailer Info')
    action_view_weight_history = fields.Char(string='Action View Weight History')
    action_weigh_bale = fields.Char(string='Action Weigh Bale')
    analytics = fields.Char(string='Analytics')
    button_box = fields.Char(string='Button Box')
    card = fields.Char(string='Card')
    context = fields.Char(string='Context')
    created = fields.Char(string='Created')
    environmental = fields.Char(string='Environmental')
    grade_a = fields.Char(string='Grade A')
    grade_b = fields.Char(string='Grade B')
    grade_c = fields.Char(string='Grade C')
    group_by_date = fields.Date(string='Group By Date')
    group_by_grade = fields.Char(string='Group By Grade')
    group_by_paper_type = fields.Selection(string='Group By Paper Type')
    group_by_source = fields.Char(string='Group By Source')
    group_by_status = fields.Selection(string='Group By Status')
    group_by_trailer = fields.Char(string='Group By Trailer')
    help = fields.Char(string='Help')
    in_storage = fields.Char(string='In Storage')
    loaded = fields.Char(string='Loaded')
    on_trailer = fields.Char(string='On Trailer')
    quality = fields.Char(string='Quality')
    quality_inspector = fields.Char(string='Quality Inspector')
    ready_loading = fields.Char(string='Ready Loading')
    res_model = fields.Char(string='Res Model')
    search_view_id = fields.Many2one('search.view')
    shipped = fields.Char(string='Shipped')
    source_documents = fields.Char(string='Source Documents')
    sustainable = fields.Char(string='Sustainable')
    this_month = fields.Char(string='This Month')
    this_week = fields.Char(string='This Week')
    today = fields.Char(string='Today')
    trailer_loading = fields.Char(string='Trailer Loading')
    view_mode = fields.Char(string='View Mode')
    weighed = fields.Char(string='Weighed')
    weight_history = fields.Char(string='Weight History')

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_net_value(self):
            """Calculate net value after costs"""
            for record in self:
                costs = (record.processing_cost or 0) + (record.transportation_cost or 0)
                record.net_value = (record.sale_price or 0) - costs


    def _compute_density(self):
            """Calculate bale density"""
            for record in self:
                if record.weight and record.total_volume > 0:
                    weight_kg = record.get_weight_in_kg()
                    record.density = weight_kg / record.total_volume
                else:
                    record.density = 0.0


    def _compute_environmental_impact(self):
            """Calculate environmental impact metrics"""
            for record in self:
                if record.weight and record.weight > 0:
                    # Rough calculation: 17 trees per ton of paper
                    weight_tons = record.weight
                    if record.weight_unit == "lb":
                        weight_tons = record.weight / 2204.62
                    elif record.weight_unit == "kg":
                        weight_tons = record.weight / 1000
                    record.trees_saved = weight_tons * 17
                else:
                    record.trees_saved = 0.0


    def _compute_document_count(self):
            """Count source documents"""
            for record in self:
                record.document_count = len(record.source_document_ids)

        # ============================================================================
            # ORM OVERRIDES
        # ============================================================================

    def create(self, vals_list):
            """Override create to set sequence and initial state"""
            for vals in vals_list:
                if not vals.get("name") or vals.get("name") == "/":
                    vals["name") = (]
                        self.env["ir.sequence"].next_by_code("paper.bale") or "BALE-NEW"

            return super().create(vals_list)


    def write(self, vals):
            """Override write for state change tracking""":
            if "state" in vals:
                for record in self:
                    old_state = record.state
                    new_state = vals["state"]
                    if old_state != new_state:
                        record.message_post()
                            body=_()
                                "State changed from %s to %s", old_state, new_state


            return super().write(vals)


    def unlink(self):
            """Override unlink to prevent deletion of shipped bales"""
            for record in self:
                if record.state in ["shipped", "delivered", "recycled"]:
                    raise UserError()
                        _()
                            "Cannot delete bale %s in state %s",
                            record.name,
                            record.state,


            return super().unlink()

        # ============================================================================
            # ACTION METHODS
        # ============================================================================

    def action_weigh_bale(self):
            """Weigh the bale"""
            self.ensure_one()
            return {}
                "type": "ir.actions.act_window",
                "name": _("Weigh Bale"),
                "res_model": "paper.bale.weigh.wizard",
                "view_mode": "form",
                "target": "new",
                "context": {"default_bale_id": self.id},



    def action_quality_inspection(self):
            """Perform quality inspection"""
            self.ensure_one()
            return {}
                "type": "ir.actions.act_window",
                "name": _("Quality Inspection"),
                "res_model": "paper.bale.inspection.wizard",
                "view_mode": "form",
                "target": "new",
                "context": {"default_bale_id": self.id},



    def action_load_on_trailer(self):
            """Load bale on trailer"""
            self.ensure_one()
            if self.state != "approved":
                raise UserError(_("Only approved bales can be loaded"))
            self.write({"state": "loaded", "pickup_date": fields.Date.today()})
            self.message_post(body=_("Bale loaded on trailer"))


    def action_ship_bale(self):
            """Ship the bale"""
            self.ensure_one()
            if self.state != "loaded":
                raise UserError(_("Only loaded bales can be shipped"))
            self.write({"state": "shipped"})
            self.message_post(body=_("Bale shipped"))


    def action_confirm_delivery(self):
            """Confirm bale delivery"""
            self.ensure_one()
            if self.state != "shipped":
                raise UserError(_("Only shipped bales can be delivered"))
            self.write()
                {"state": "delivered", "delivery_date": fields.Date.today()}

            self.message_post(body=_("Bale delivery confirmed"))


    def action_mark_recycled(self):
            """Mark bale as recycled"""
            self.ensure_one()
            if self.state != "delivered":
                raise UserError(_("Only delivered bales can be marked as recycled"))
            self.write()
                {"state": "recycled", "recycling_date": fields.Date.today()}

            self.message_post(body=_("Bale marked as recycled"))


    def action_reject_bale(self):
            """Reject the bale"""
            self.ensure_one()
            self.write({"state": "rejected"})
            self.message_post(body=_("Bale rejected"))


    def action_print_label(self):
            """Print bale label"""
            self.ensure_one()
            return self.env.ref()
                "records_management.action_report_bale_label"
            ).report_action(self


    def action_view_source_documents(self):
            """View source documents"""
            self.ensure_one()
            return {}
                "type": "ir.actions.act_window",
                "name": _("Source Documents"),
                "res_model": "paper.bale.source.document",
                "view_mode": "tree,form",
                "domain": [("bale_id", "=", self.id)],
                "context": {"default_bale_id": self.id},



    def action_view_movements(self):
            """View bale movements"""
            self.ensure_one()
            return {}
                "type": "ir.actions.act_window",
                "name": _("Bale Movements"),
                "res_model": "paper.bale.movement",
                "view_mode": "tree,form",
                "domain": [("bale_id", "=", self.id)],
                "context": {"default_bale_id": self.id},



    def action_view_inspections(self):
            """View quality inspections"""
            self.ensure_one()
            return {}
                "type": "ir.actions.act_window",
                "name": _("Quality Inspections"),
                "res_model": "paper.bale.inspection",
                "view_mode": "tree,form",
                "domain": [("bale_id", "=", self.id)],
                "context": {"default_bale_id": self.id},


        # ============================================================================
            # BUSINESS METHODS
        # ============================================================================

    def create_movement_record(:):
            self, from_location_id, to_location_id, movement_type="transfer"

            """Create movement record"""
            self.ensure_one()
            return self.env["paper.bale.movement"].create()
                {}
                    "bale_id": self.id,
                    "from_location_id": from_location_id,
                    "to_location_id": to_location_id,
                    "movement_type": movement_type,
                    "movement_date": fields.Datetime.now(),
                    "user_id": self.env.user.id,




    def get_weight_in_kg(self):
            """Get weight converted to kilograms"""
            self.ensure_one()
            if not self.weight:
                return 0.0
            if self.weight_unit == "kg":
                return self.weight
            elif self.weight_unit == "lb":
                return self.weight * 0.453592
            elif self.weight_unit == "ton":
                return self.weight * 1000
            return self.weight


    def calculate_recycling_value(self):
            """Calculate estimated recycling value"""
            self.ensure_one()
            rates = {}
                "office": 0.15,
                "cardboard": 0.12,
                "newspaper": 0.8,
                "magazine": 0.10,
                "mixed": 0.6,
                "shredded": 0.4,
                "confidential": 0.5,

            weight_kg = self.get_weight_in_kg()
            base_rate = rates.get(self.paper_type, 0.5)
            quality_multipliers = {"high": 1.2, "medium": 1.0, "low": 0.8}
            quality_mult = quality_multipliers.get(self.paper_grade, 1.0)
            contamination_multipliers = {}
                "none": 1.0,
                "low": 0.9,
                "medium": 0.7,
                "high": 0.5,

            contamination_mult = contamination_multipliers.get()
                self.contamination_level, 1.0

            return weight_kg * base_rate * quality_mult * contamination_mult

        # ============================================================================
            # VALIDATION METHODS
        # ============================================================================

    def _check_weight(self):
            """Validate weight is positive"""
            for record in self:
                if record.weight and record.weight <= 0:
                    raise ValidationError(_("Weight must be positive"))


    def _check_dates(self):
            """Validate date sequence"""
            for record in self:
                if record.pickup_date and record.delivery_date:
                    if record.pickup_date > record.delivery_date:
                        raise ValidationError()
                            _("Pickup date cannot be after delivery date")



    def _check_moisture_content(self):
            """Validate moisture content percentage"""
            for record in self:
                if record.moisture_content and (:)
                    record.moisture_content < 0 or record.moisture_content > 100

                    raise ValidationError()
                        _("Moisture content must be between 0 and 100 percent")


        # ============================================================================
            # UTILITY METHODS
        # ============================================================================

    def name_get(self):
            """Custom name display"""
            result = []
            for record in self:
                name = record.name
                if record.paper_type:
                    paper_type_label = dict()
                        record._fields["paper_type"].selection
                    ).get(record.paper_type, ""
                    name = _("%s (%s)", record.name, paper_type_label)
                result.append((record.id, name))
            return result


    def _name_search(:):
            self, name, args=None, operator="ilike", limit=100, name_get_uid=None

            """Enhanced search by name, reference, barcode, or paper type"""
            args = list(args or [])

            if name:
                # Search in multiple fields: name, reference_number, barcode, external_reference
                domain = []
                    "|",
                    "|",
                    "|",
                    ("name", operator, name),
                    ("reference_number", operator, name),
                    ("barcode", operator, name),
                    ("external_reference", operator, name),

                return self._search()
                    expression.AND([domain, args]),
                    limit=limit,
                    access_rights_uid=name_get_uid,


            return super()._name_search(name, args, operator, limit, name_get_uid)
