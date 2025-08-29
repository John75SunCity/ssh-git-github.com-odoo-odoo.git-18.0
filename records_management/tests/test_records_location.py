from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError

class TestRecordsLocation(TransactionCase):

    def setUp(self):
        super(TestRecordsLocation, self).setUp()
        self.location_model = self.env['records.location']
        self.parent_location = self.location_model.create({
            'name': 'Parent Location',
            'code': 'PARENT',
            'max_capacity': 10,
        })
        self.child_location = self.location_model.create({
            'name': 'Child Location',
            'code': 'CHILD',
            'parent_location_id': self.parent_location.id,
            'max_capacity': 5,
        })

    def test_hierarchy_constraint(self):
        """Test that recursive location hierarchies are not allowed."""
        with self.assertRaises(ValidationError):
            self.parent_location.write({'parent_location_id': self.child_location.id})

    def test_max_capacity_constraint(self):
        """Test that max_capacity cannot be negative."""
        with self.assertRaises(ValidationError):
            self.parent_location.write({'max_capacity': -1})

    def test_utilization_percentage(self):
        """Test utilization percentage calculation."""
        container_model = self.env['records.container']
        container_model.create({'name': 'Container 1', 'location_id': self.parent_location.id})
        container_model.create({'name': 'Container 2', 'location_id': self.parent_location.id})
        self.parent_location._compute_utilization_percentage()
        self.assertEqual(self.parent_location.utilization_percentage, 20.0)

    def test_available_spaces(self):
        """Test available spaces calculation."""
        container_model = self.env['records.container']
        container_model.create({'name': 'Container 1', 'location_id': self.parent_location.id})
        self.parent_location._compute_available_spaces()
        self.assertEqual(self.parent_location.available_spaces, 9)

    def test_is_at_capacity(self):
        """Test is_at_capacity computation."""
        self.parent_location.write({'max_capacity': 1})
        container_model = self.env['records.container']
        container_model.create({'name': 'Container 1', 'location_id': self.parent_location.id})
        self.parent_location._compute_is_at_capacity()
        self.assertTrue(self.parent_location.is_at_capacity)

    def test_action_view_containers(self):
        """Test action_view_containers method."""
        action = self.parent_location.action_view_containers()
        self.assertEqual(action['res_model'], 'records.container')
        self.assertEqual(action['domain'], [('location_id', '=', self.parent_location.id)])

    def test_action_view_child_locations(self):
        """Test action_view_child_locations method."""
        action = self.parent_location.action_view_child_locations()
        self.assertEqual(action['res_model'], 'records.location')
        self.assertEqual(action['domain'], [('parent_location_id', '=', self.parent_location.id)])

    def test_action_activate(self):
        """Test action_activate method."""
        self.parent_location.action_activate()
        self.assertTrue(self.parent_location.active)
        self.assertEqual(self.parent_location.state, 'active')

    def test_action_deactivate(self):
        """Test action_deactivate method."""
        self.parent_location.action_deactivate()
        self.assertFalse(self.parent_location.active)
        self.assertEqual(self.parent_location.state, 'inactive')
