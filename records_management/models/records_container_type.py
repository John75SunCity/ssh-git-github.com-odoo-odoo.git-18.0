from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import UserError, ValidationError


class RecordsContainerType(models.Model):
    _name = 'records.container.type'
    _description = 'Records Container Type'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'
    _rec_name = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    code = fields.Char()
    standard_type = fields.Selection()
    barcode_product_id = fields.Many2one()
    barcode_prefix = fields.Char()
    auto_generate_barcode = fields.Boolean()
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    active = fields.Boolean()
    sequence = fields.Integer()
    description = fields.Text()
    dimensions = fields.Char()
    length = fields.Float()
    width = fields.Float()
    height = fields.Float()
    weight_capacity = fields.Float()
    volume_capacity = fields.Float()
    container_category = fields.Selection()
    storage_location_type = fields.Selection()
    state = fields.Selection()
    billing_config_id = fields.Many2one()
    base_rate_id = fields.Many2one()
    standard_rate = fields.Monetary()
    setup_fee = fields.Monetary()
    handling_fee = fields.Monetary()
    destruction_fee = fields.Monetary()
    currency_id = fields.Many2one()
    stackable = fields.Boolean()
    max_stack_height = fields.Integer()
    requires_special_handling = fields.Boolean()
    vault_eligible = fields.Boolean()
    climate_controlled = fields.Boolean()
    fireproof = fields.Boolean()
    waterproof = fields.Boolean()
    container_ids = fields.One2many()
    shredding_service_ids = fields.One2many()
    container_count = fields.Integer()
    utilization_percentage = fields.Float()
    total_revenue = fields.Monetary()
    volume_calculated = fields.Float()
    activity_ids = fields.One2many()
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many()
    context = fields.Char(string='Context')
    domain = fields.Char(string='Domain')
    help = fields.Char(string='Help')
    res_model = fields.Char(string='Res Model')
    type = fields.Selection(string='Type')
    view_mode = fields.Char(string='View Mode')

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_rates_from_billing(self):
            """Compute rates from existing billing configuration models"""
            for record in self:
                if record.billing_config_id:
                    # Get rates from existing billing configuration
                    record.standard_rate = ()
                        record.billing_config_id.default_monthly_rate or 0.0

                    record.setup_fee = record.billing_config_id.setup_fee or 0.0
                    record.handling_fee = record.billing_config_id.handling_fee or 0.0
                    record.destruction_fee = record.billing_config_id.destruction_fee or 0.0
                elif record.base_rate_id:
                    # Fallback to base rates
                    record.standard_rate = record.base_rate_id.monthly_rate or 0.0
                    record.setup_fee = record.base_rate_id.setup_fee or 0.0
                    record.handling_fee = record.base_rate_id.handling_fee or 0.0
                    record.destruction_fee = record.base_rate_id.destruction_fee or 0.0
                elif record.standard_type and record.standard_type != "custom":
                    # Use standard rates based on container type
                    standard_rates = record._get_standard_type_rates()
                    record.standard_rate = standard_rates.get("monthly_rate", 0.0)
                    record.setup_fee = standard_rates.get("setup_fee", 0.0)
                    record.handling_fee = standard_rates.get("handling_fee", 0.0)
                    record.destruction_fee = standard_rates.get("destruction_fee", 0.0)
                else:
                    record.standard_rate = 0.0
                    record.setup_fee = 0.0
                    record.handling_fee = 0.0
                    record.destruction_fee = 0.0


    def _compute_container_metrics(self):
            """Compute metrics from existing container data"""
            for record in self:
                containers = record.container_ids
                record.container_count = len(containers)

                # Compute utilization from existing container weights
                if containers and record.weight_capacity > 0:
                    total_weight = sum()
                        containers.filtered()
                            lambda c: c.state in ["active", "stored"]
                        ).mapped("current_weight"
                        or [0]

                    total_capacity = record.weight_capacity * len(containers)
                    record.utilization_percentage = ()
                        (total_weight / total_capacity) * 100 if total_capacity > 0 else 0.0:

                else:
                    record.utilization_percentage = 0.0


    def _compute_total_revenue_metrics(self):
            """Compute total revenue from existing container billing data"""
            for record in self:
                # Get active containers that are being billed
                billable_containers = record.container_ids.filtered()
                    lambda c: c.state in ["active", "stored"] and not c.billing_suspended

                record.total_revenue = len(billable_containers) * record.standard_rate


    def _compute_volume_calculated(self):
            """Calculate volume from dimensions"""
            for record in self:
                if record.length and record.width and record.height:
                    record.volume_calculated = ()
                        record.length * record.width * record.height

                else:
                    record.volume_calculated = 0.0


    def _onchange_standard_type(self):
            """Auto-populate dimensions and specifications based on standard type"""
            if self.standard_type and self.standard_type != "custom":
                # Get standard specifications for the selected type:
                specs = self._get_standard_type_specifications()
                if specs:
                    self.volume_capacity = specs.get("volume_cf", 0.0)
                    self.weight_capacity = specs.get("avg_weight", 0.0)
                    self.dimensions = specs.get("dimensions", "")

                    # Parse dimensions and set individual dimension fields
                    if specs.get("dimensions") != "unknown":
                        dims = specs.get("dimensions", "").split("x")
                        if len(dims) == 3:
                            try:
                                self.length = float(dims[0])
                                self.width = float(dims[1])
                                self.height = float(dims[2])
                            except ValueError
                                pass  # Keep existing values if parsing fails:

    def _get_standard_type_specifications(self):
            """Get standard specifications for container types""":
            specs_mapping = {}
                "type_01": {  # Standard Box}
                    "volume_cf": 1.2,
                    "avg_weight": 35,
                    "dimensions": "12x15x10",
                    "description": "Standard Box - General file storage",

                "type_02": {  # Legal/Banker Box}
                    "volume_cf": 2.4,  # Corrected volume
                    "avg_weight": 65,
                    "dimensions": "24x15x10",
                    "description": "Legal/Banker Box - Large capacity file storage",

                "type_03": {  # Map Box}
                    "volume_cf": 0.875,
                    "avg_weight": 35,
                    "dimensions": "42x6x6",
                    "description": "Map Box - Maps, blueprints, and long documents",

                "type_04": {  # Odd Size/Temp Box}
                    "volume_cf": 5.0,
                    "avg_weight": 75,
                    "dimensions": "unknown",
                    "description": "Odd Size/Temp Box - Variable size temporary storage",

                "type_06": {  # Pathology Box}
                    "volume_cf": 0.42,
                    "avg_weight": 40,
                    "dimensions": "12x6x10",
                    "description": "Pathology Box - Medical specimens and pathology documents",


            return specs_mapping.get(self.standard_type, {})

        # ============================================================================
            # CONSTRAINTS AND VALIDATION
        # ============================================================================
            _sql_constraints = []
            ()
                "code_company_unique",
                "unique(code, company_id)",
                "Container type code must be unique per company!",

            ()
                "name_company_unique",
                "unique(name, company_id)",
                "Container type name must be unique per company!",

            ()
                "positive_weight_capacity",
                "check(weight_capacity >= 0)",
                "Weight capacity must be positive!",

            ()
                "positive_volume_capacity",
                "check(volume_capacity >= 0)",
                "Volume capacity must be positive!",




    def _check_dimensions(self):
            """Validate container dimensions"""
            for record in self:
                if record.length and record.length <= 0:
                    raise ValidationError(_("Length must be positive"))
                if record.width and record.width <= 0:
                    raise ValidationError(_("Width must be positive"))
                if record.height and record.height <= 0:
                    raise ValidationError(_("Height must be positive"))


    def _check_stack_height(self):
            """Validate stack height"""
            for record in self:
                if record.max_stack_height < 1:
                    raise ValidationError(_("Maximum stack height must be at least 1"))


    def _check_pricing(self):
            """Validate pricing fields"""
            for record in self:
                if record.standard_rate < 0:
                    raise ValidationError(_("Standard rate cannot be negative"))
                if record.setup_fee < 0:
                    raise ValidationError(_("Setup fee cannot be negative"))
                if record.handling_fee < 0:
                    raise ValidationError(_("Handling fee cannot be negative"))
                if record.destruction_fee < 0:
                    raise ValidationError(_("Destruction fee cannot be negative"))

        # ============================================================================
            # ACTION METHODS
        # ============================================================================

    def action_activate(self):
            """Activate the container type"""

            self.ensure_one()
            if self.state != "draft":
                raise UserError(_("Only draft container types can be activated"))

            self.write({"state": "active", "active": True})
            self.message_post(body=_("Container type activated"))


    def action_archive(self):
            """Archive the container type"""

            self.ensure_one()
            if self.state != "active":
                raise UserError(_("Only active container types can be archived"))

            # Check for active containers:
            active_containers = self.container_ids.filtered()
                lambda c: c.state == "active"

            if active_containers:
                raise UserError()
                    _()
                        "Cannot archive container type with active containers. "
                        "Please archive or reassign all containers first."



            self.write({"state": "archived", "active": False})
            self.message_post(body=_("Container type archived"))


    def action_view_containers(self):
            """View all containers of this type"""

            self.ensure_one()
            return {}
                "type": "ir.actions.act_window",
                "name": _("Containers"),
                "res_model": "records.container",
                "view_mode": "tree,form",
                "domain": [("container_type_id", "=", self.id)],
                "context": {"default_container_type_id": self.id},



    def action_create_container(self):
            """Create a new container of this type"""

            self.ensure_one()
            return {}
                "type": "ir.actions.act_window",
                "name": _("Create Container"),
                "res_model": "records.container",
                "view_mode": "form",
                "target": "new",
                "context": {}
                    "default_container_type_id": self.id,
                    "default_weight_capacity": self.weight_capacity,
                    "default_volume_capacity": self.volume_capacity,



        # ============================================================================
            # BUSINESS METHODS
        # ============================================================================

    def get_pricing_info(self):
            """Get comprehensive pricing information"""
            self.ensure_one()
            return {}
                "standard_rate": self.standard_rate,
                "setup_fee": self.setup_fee,
                "handling_fee": self.handling_fee,
                "destruction_fee": self.destruction_fee,
                "currency": self.currency_id.name,
                "total_monthly_revenue": self.total_revenue,



    def calculate_storage_cost(self, months=1, include_setup=False):
            """Calculate storage cost for specified period""":
            self.ensure_one()
            cost = self.standard_rate * months
            if include_setup:
                cost += self.setup_fee
            return cost


    def _check_capacity_availability(self):
            """Check if there's capacity available for new containers""":'
            for record in self:
                # This would depend on location capacity limits
                # For now, return True - implement based on business rules
                pass


    def get_container_summary(self):
            """Get summary information for reporting""":
            self.ensure_one()
            return {}
                "name": self.name,
                "code": self.code,
                "category": self.container_category,
                "container_count": self.container_count,
                "weight_capacity": self.weight_capacity,
                "volume_capacity": self.volume_capacity,
                "standard_rate": self.standard_rate,
                "utilization_percentage": self.utilization_percentage,
                "total_revenue": self.total_revenue,


        # ============================================================================
            # UTILITY METHODS
        # ============================================================================

    def name_get(self):
            """Custom name display"""
            result = []
            for record in self:
                if record.code:
                    display_name = _("%s [%s]", record.name, record.code)
                else:
                    display_name = record.name
                result.append((record.id, display_name))
            return result


    def _search_name_code(self, name, args=None, operator="ilike", limit=100, name_get_uid=None):
            """Enhanced search by name or code"""
            args = args or []
            domain = []
            if name:
                domain = []
                    "|",
                    "|",
                    ("name", operator, name),
                    ("code", operator, name),
                    ("description", operator, name),

            return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)


    def get_container_types_by_category(self, category):
            """Get container types by category"""
            return self.search()
                [("container_category", "=", category), ("state", "=", "active")]



    def copy(self, default=None):
            """Override copy to ensure unique codes"""
            default = dict(default or {})
            # Generate a unique code for the copy:
            base_code = self.code
            if base_code.endswith("_COPY"):
                # Code already has _COPY suffix, keep it as is
                new_code = base_code
            elif "_COPY" in base_code:
                base_code = base_code.split("_COPY")[0] + "_COPY"
                new_code = base_code
            else:
                new_code = f"{base_code}_COPY"

            # Find existing copies and increment a counter if needed:
            existing_codes = self.search()
                [("code", "like", f"{new_code}%"), ("company_id", "=", self.company_id.id)]
            ).mapped("code"
            counter = 1
            final_code = new_code
            while final_code in existing_codes:
                counter += 1
                final_code = f"{new_code}{counter}"

            default.update()
                {}
                    "name": _("%(name)s (Copy)", name=self.name),
                    "code": final_code,


            return super().copy(default)

        # ============================================================================
            # BUSINESS METHODS - INTEGRATE WITH EXISTING SYSTEMS
        # ============================================================================

    def _get_standard_type_rates(self):
            """Get standard rates based on container type from existing rate configuration"""
            self.ensure_one()

            # First priority: Direct billing configuration link
            if self.billing_config_id:
                return {}
                    "monthly_rate": self.billing_config_id.default_monthly_rate or 0.0,
                    "setup_fee": self.billing_config_id.setup_fee or 0.0,
                    "handling_fee": self.billing_config_id.handling_fee or 0.0,
                    "destruction_fee": self.billing_config_id.destruction_fee or 0.0,


            # Second priority: Direct base rate link
            if self.base_rate_id:
                return {}
                    "monthly_rate": self.base_rate_id.monthly_rate or 0.0,
                    "setup_fee": self.base_rate_id.setup_fee or 0.0,
                    "handling_fee": self.base_rate_id.handling_fee or 0.0,
                    "destruction_fee": self.base_rate_id.destruction_fee or 0.0,


            # Third priority: Search base rates by container type code
            base_rates = self.env["base.rate"].search()
                [("container_type_code", "=", self.code)], limit=1


            if base_rates:
                return {}
                    "monthly_rate": base_rates.monthly_rate or 0.0,
                    "setup_fee": base_rates.setup_fee or 0.0,
                    "handling_fee": base_rates.handling_fee or 0.0,
                    "destruction_fee": base_rates.destruction_fee or 0.0,


            # Fourth priority: Search base rates by standard type
            if self.standard_type and self.standard_type != "custom":
                base_rates = self.env["base.rate"].search()
                    [("container_type", "=", self.standard_type)], limit=1


                if base_rates:
                    return {}
                        "monthly_rate": base_rates.monthly_rate or 0.0,
                        "setup_fee": base_rates.setup_fee or 0.0,
                        "handling_fee": base_rates.handling_fee or 0.0,
                        "destruction_fee": base_rates.destruction_fee or 0.0,


            # Fifth priority: Hardcoded standard rates for actual business container types:
            rate_mapping = {}
                "type_01": {  # Standard Box - 1.2 CF, 35 lbs avg, 12x15x10}
                    "monthly_rate": 5.50,
                    "setup_fee": 15.0,
                    "handling_fee": 8.0,
                    "destruction_fee": 12.0,
                    "volume_cf": 1.2,
                    "avg_weight": 35,
                    "dimensions": "12x15x10",

                "type_02": {  # Legal/Banker Box - 2.4 CF, 65 lbs avg, 24x15x10}
                    "monthly_rate": 7.50,
                    "setup_fee": 20.0,
                    "handling_fee": 12.0,
                    "destruction_fee": 18.0,
                    "volume_cf": 2.4,  # Corrected volume
                    "avg_weight": 65,
                    "dimensions": "24x15x10",

                "type_03": {  # Map Box - 0.875 CF, 35 lbs avg, 42x6x6}
                    "monthly_rate": 8.0,
                    "setup_fee": 25.0,
                    "handling_fee": 15.0,
                    "destruction_fee": 20.0,
                    "volume_cf": 0.875,
                    "avg_weight": 35,
                    "dimensions": "42x6x6",

                "type_04": {  # Odd Size/Temp Box - 5.0 CF, 75 lbs avg, unknown dimensions}
                    "monthly_rate": 15.0,
                    "setup_fee": 40.0,
                    "handling_fee": 25.0,
                    "destruction_fee": 35.0,
                    "volume_cf": 5.0,
                    "avg_weight": 75,
                    "dimensions": "unknown",

                "type_06": {  # Pathology Box - 0.42 CF, 40 lbs avg, 12x6x10}
                    "monthly_rate": 4.50,
                    "setup_fee": 12.0,
                    "handling_fee": 6.0,
                    "destruction_fee": 10.0,
                    "volume_cf": 0.42,
                    "avg_weight": 40,
                    "dimensions": "12x6x10",



            # Return rates for the specific container type or zeros if not found:
            return rate_mapping.get()
                self.standard_type,
                {}
                    "monthly_rate": 0.0,
                    "setup_fee": 0.0,
                    "handling_fee": 0.0,
                    "destruction_fee": 0.0,
                    "volume_cf": 0.0,
                    "avg_weight": 0.0,
                    "dimensions": "unknown",




    def generate_container_barcode(self):
            """Generate barcode using existing barcode system"""
            self.ensure_one()
            if not self.barcode_product_id:
                raise UserError()
                    _("No barcode product template configured for this container type"):


            # Use existing barcode generation system
            barcode_service = self.env["barcode.product"]
            return barcode_service.generate_barcode_for_container_type(self)


    def get_billing_configuration(self):
            """Get billing configuration from existing billing system"""
            self.ensure_one()
            if self.billing_config_id:
                return self.billing_config_id
            elif self.standard_type != "custom":
                # Find or create billing config for standard type:
                billing_config = self.env["records.billing.config"].search()
                    [("container_type", "=", self.standard_type)], limit=1

                if billing_config:
                    self.billing_config_id = billing_config.id
                    return billing_config
            return False


    def create_containers_from_barcodes(self, barcode_list):
            """Create containers from barcode list using existing container management"""
            self.ensure_one()
            container_model = self.env["records.container"]
            created_containers = container_model.browse()

            base_container_vals = {}
                "container_type_id": self.id,
                "weight_capacity": self.weight_capacity,
                "volume_capacity": self.volume_capacity,
                "state": "draft",


            for barcode in barcode_list:
                container_vals = dict(base_container_vals)
                container_vals.update()
                    {}
                        "name": f"Container {barcode}",
                        "barcode": barcode,


                container = container_model.create(container_vals)
                created_containers |= container

            return created_containers

