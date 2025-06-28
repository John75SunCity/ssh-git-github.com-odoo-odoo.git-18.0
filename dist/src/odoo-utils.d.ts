/**
 * Sample TypeScript module for Odoo project utilities
 */
export declare class OdooUtils {
    /**
     * Get the project root directory
     */
    static getProjectRoot(): string;
    /**
     * Check if a file exists
     */
    static fileExists(filePath: string): boolean;
    /**
     * Read module manifest file
     */
    static readManifest(modulePath: string): Promise<any>;
}
export default OdooUtils;
