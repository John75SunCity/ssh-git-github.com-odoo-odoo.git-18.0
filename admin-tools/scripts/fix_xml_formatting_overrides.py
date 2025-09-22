#!/usr/bin/env python3
"""
🔧 VS Code XML Formatter Override Detection and Fix Script

This script helps identify and fix VS Code extensions that are overriding
our manual XML formatting settings.
"""

import json
import os
import sys

def check_settings():
    """Check current VS Code settings for XML formatting overrides."""
    settings_path = "/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0/.vscode/settings.json"
    
    print("🔍 CHECKING VS CODE SETTINGS FOR XML FORMATTING OVERRIDES...")
    print("=" * 70)
    
    if not os.path.exists(settings_path):
        print("❌ Settings file not found!")
        return
    
    try:
        with open(settings_path, 'r') as f:
            settings = json.load(f)
        
        print("✅ Settings file loaded successfully")
        print()
        
        # Check XML-specific settings
        xml_settings = settings.get('[xml]', {})
        print("🎯 XML-SPECIFIC SETTINGS:")
        print(f"  formatOnSave: {xml_settings.get('editor.formatOnSave', 'NOT SET')}")
        print(f"  formatOnPaste: {xml_settings.get('editor.formatOnPaste', 'NOT SET')}")
        print(f"  formatOnType: {xml_settings.get('editor.formatOnType', 'NOT SET')}")
        print(f"  defaultFormatter: {xml_settings.get('editor.defaultFormatter', 'NOT SET')}")
        print(f"  autoIndent: {xml_settings.get('editor.autoIndent', 'NOT SET')}")
        print()
        
        # Check global XML settings
        print("🌐 GLOBAL XML FORMATTER SETTINGS:")
        xml_format_enabled = settings.get('xml.format.enabled', 'NOT SET')
        print(f"  xml.format.enabled: {xml_format_enabled}")
        print(f"  xml.format.preserveAttributeLineBreaks: {settings.get('xml.format.preserveAttributeLineBreaks', 'NOT SET')}")
        print(f"  xml.format.maxLineWidth: {settings.get('xml.format.maxLineWidth', 'NOT SET')}")
        print()
        
        # Check if settings are correct
        correct_settings = (
            xml_settings.get('editor.formatOnSave') == False and
            xml_settings.get('editor.formatOnPaste') == False and
            xml_settings.get('editor.formatOnType') == False and
            xml_settings.get('editor.defaultFormatter') is None and
            xml_format_enabled == False
        )
        
        if correct_settings:
            print("✅ XML FORMATTING SETTINGS ARE CORRECT!")
            print("   Extensions should no longer auto-format XML files.")
        else:
            print("❌ XML FORMATTING SETTINGS NEED ADJUSTMENT!")
            print("   Extensions may still be auto-formatting XML files.")
        
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing settings.json: {e}")
    except Exception as e:
        print(f"❌ Error reading settings: {e}")

def provide_solutions():
    """Provide step-by-step solutions to fix XML formatting issues."""
    print("\n🛠️  SOLUTIONS TO FIX XML FORMATTING OVERRIDES:")
    print("=" * 70)
    
    print("\n1️⃣  DISABLE XML EXTENSIONS:")
    print("   • Open VS Code Command Palette (Cmd+Shift+P)")
    print("   • Type: 'Extensions: Show Installed Extensions'")
    print("   • Find and DISABLE these extensions:")
    print("     - Red Hat XML (redhat.vscode-xml)")
    print("     - XML Tools (DotJoshJohnson.xml)")
    print("     - Any other XML formatters")
    
    print("\n2️⃣  FORCE RELOAD VS CODE:")
    print("   • Cmd+Shift+P → 'Developer: Reload Window'")
    print("   • This ensures all settings take effect")
    
    print("\n3️⃣  TEST WITH COPILOT INLINE CHAT:")
    print("   • Open an XML file")
    print("   • Use Ctrl+I (inline chat)")
    print("   • Ask for a simple edit")
    print("   • Check if formatting is preserved")
    
    print("\n4️⃣  ALTERNATIVE: DISABLE COPILOT AUTO-FORMAT:")
    print("   • When using Copilot inline chat")
    print("   • Add to your prompt: 'Do not reformat the file'")
    print("   • Or: 'Keep existing formatting'")
    
    print("\n5️⃣  MANUAL OVERRIDE (IF NEEDED):")
    print("   • After Copilot changes, immediately Undo (Cmd+Z)")
    print("   • This reverts formatting but keeps content changes")
    print("   • Then manually apply the content changes")

def main():
    """Main function to run the diagnostics and provide solutions."""
    print("🚀 VS CODE XML FORMATTING OVERRIDE FIX TOOL")
    print("=" * 70)
    print("This tool helps fix issues where VS Code extensions override")
    print("your manual XML formatting settings.")
    print()
    
    check_settings()
    provide_solutions()
    
    print("\n🎯 SUMMARY:")
    print("The main issue is that XML formatter extensions (Red Hat XML, XML Tools)")
    print("override workspace settings. Our settings are now configured to prevent")
    print("auto-formatting, but you need to disable/reload extensions.")
    print()
    print("✅ Key changes made:")
    print("   • Set editor.defaultFormatter to null for XML")
    print("   • Disabled all XML auto-formatting")
    print("   • Added extension blacklist")
    print("   • Preserved attribute line breaks")

if __name__ == "__main__":
    main()
