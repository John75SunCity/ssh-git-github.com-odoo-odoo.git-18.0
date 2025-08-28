from odoo.tests.common import TransactionCase


class TestHardDriveScanning(TransactionCase):

    def setUp(self):
        super(TestHardDriveScanning, self).setUp()
        self.HardDriveScan = self.env['hard.drive.scan']
        self.scan = self.HardDriveScan.create({
            'name': 'Test Scan',
            'status': 'pending',
        })

    def test_scan_creation(self):
        """Test creation of a new hard drive scan."""
        self.assertEqual(self.scan.name, 'Test Scan')
        self.assertEqual(self.scan.status, 'pending')

    def test_scan_completion(self):
        """Test marking a scan as completed."""
        self.scan.action_complete()
        self.assertEqual(self.scan.status, 'completed')
