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
exports.OdooUtils = void 0;
const path = __importStar(require("path"));
const fs = __importStar(require("fs"));
/**
 * Sample TypeScript module for Odoo project utilities
 */
class OdooUtils {
    /**
     * Get the project root directory
     */
    static getProjectRoot() {
        return path.resolve(__dirname, '..');
    }
    /**
     * Check if a file exists
     */
    static fileExists(filePath) {
        return fs.existsSync(filePath);
    }
    /**
     * Read module manifest file
     */
    static async readManifest(modulePath) {
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
exports.OdooUtils = OdooUtils;
exports.default = OdooUtils;
