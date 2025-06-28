import * as path from 'path';
import * as fs from 'fs';

/**
 * Sample TypeScript module for Odoo project utilities
 */
export class OdooUtils {
    /**
     * Get the project root directory
     */
    static getProjectRoot(): string {
        return path.resolve(__dirname, '..');
    }

    /**
     * Check if a file exists
     */
    static fileExists(filePath: string): boolean {
        return fs.existsSync(filePath);
    }

    /**
     * Read module manifest file
     */
    static async readManifest(modulePath: string): Promise<any> {
        const manifestPath = path.join(modulePath, '__manifest__.py');
        
        if (!this.fileExists(manifestPath)) {
            throw new Error(`Manifest file not found: ${manifestPath}`);
        }

        // This is a simple example - in reality you'd need to parse Python
        return {
            path: manifestPath,
            exists: true
        };
    }
}

export default OdooUtils;
