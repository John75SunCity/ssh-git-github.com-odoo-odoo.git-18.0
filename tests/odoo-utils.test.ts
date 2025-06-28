import { OdooUtils } from '../src/odoo-utils';
import * as path from 'path';

describe('OdooUtils', () => {
    test('should get project root directory', () => {
        const projectRoot = OdooUtils.getProjectRoot();
        expect(typeof projectRoot).toBe('string');
        expect(projectRoot).toBeDefined();
    });

    test('should check if file exists', () => {
        const packageJsonPath = path.join(process.cwd(), 'package.json');
        expect(OdooUtils.fileExists(packageJsonPath)).toBe(true);
        expect(OdooUtils.fileExists('non-existent-file.txt')).toBe(false);
    });

    test('should read manifest for records_management module', async () => {
        const modulePath = path.join(process.cwd(), 'records_management');
        const manifest = await OdooUtils.readManifest(modulePath);
        
        expect(manifest).toBeDefined();
        expect(manifest.exists).toBe(true);
        expect(manifest.path).toContain('__manifest__.py');
    });
});
