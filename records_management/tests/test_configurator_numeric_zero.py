from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestConfiguratorNumericZero(TransactionCase):
    def test_numeric_zero_allowed(self):
        Config = self.env['rm.module.configurator']
        rec = Config.create({
            'name': 'Zero Retention Test',
            'config_key': 'test.zero.retention',
            'config_type': 'parameter',
            'value_number': 0.0,
            'category': 'compliance',
        })
        # Should not raise ValidationError after change; ensure current_value reflects zero
        self.assertEqual(rec.value_number, 0.0)
        self.assertEqual(rec.current_value, '0.0')
        # Update to another number and back to zero
        rec.write({'value_number': 5.0})
        self.assertEqual(rec.current_value, '5.0')
        rec.write({'value_number': 0.0})
        self.assertEqual(rec.current_value, '0.0')

    def test_switch_number_to_text_conflict(self):
        Config = self.env['rm.module.configurator']
        rec = Config.create({
            'name': 'Conflict Test',
            'config_key': 'test.conflict.param',
            'config_type': 'parameter',
            'value_number': 1.0,
            'category': 'system',
        })
        # Setting a text while numeric remains should raise conflict
        with self.assertRaises(ValidationError):
            rec.write({'value_text': 'abc'})
