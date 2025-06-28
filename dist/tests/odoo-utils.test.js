"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
const odoo_utils_1 = require("../src/odoo-utils");
const path = __importStar(require("path"));
describe('OdooUtils', () => {
    test('should get project root directory', () => {
        const projectRoot = odoo_utils_1.OdooUtils.getProjectRoot();
        expect(typeof projectRoot).toBe('string');
        expect(projectRoot).toBeDefined();
    });
    test('should check if file exists', () => {
        const packageJsonPath = path.join(process.cwd(), 'package.json');
        expect(odoo_utils_1.OdooUtils.fileExists(packageJsonPath)).toBe(true);
        expect(odoo_utils_1.OdooUtils.fileExists('non-existent-file.txt')).toBe(false);
    });
    test('should read manifest for records_management module', async () => {
        const modulePath = path.join(process.cwd(), 'records_management');
        const manifest = await odoo_utils_1.OdooUtils.readManifest(modulePath);
        expect(manifest).toBeDefined();
        expect(manifest.exists).toBe(true);
        expect(manifest.path).toContain('__manifest__.py');
    });
});
