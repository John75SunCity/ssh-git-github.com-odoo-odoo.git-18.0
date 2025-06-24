import unittest
from openerp.tests.common import TransactionCase

class TestRecordsManagement(TransactionCase):
    def setUp(self):
        super(TestRecordsManagement, self).setUp()
        # Set up test data and environment
        self.record_model = self.env['records.management']
        self.test_record = self.record_model.create({
            'name': 'Test Record',
            'description': 'This is a test record.',
        })

    def test_record_creation(self):
        """Test that a record is created successfully."""
        self.assertEqual(self.test_record.name, 'Test Record')
        self.assertEqual(self.test_record.description, 'This is a test record.')

    def test_record_deletion(self):
        """Test that a record is deleted successfully."""
        record_id = self.test_record.id
        self.test_record.unlink()
        self.assertFalse(self.record_model.search([('id', '=', record_id)]))

if __name__ == '__main__':
    unittest.main()