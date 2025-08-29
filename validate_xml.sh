#!/bin/bash
# Odoo XML Validation Script using jing-trang
# Provides better error messages than Odoo's default validator

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if jing is installed
if ! command -v jing &> /dev/null; then
    print_error "jing-trang is not installed. Please install it first:"
    echo "  brew install jing-trang"
    exit 1
fi

# Check if XML file is provided
if [ $# -eq 0 ]; then
    print_error "Usage: $0 <xml_file> [xml_file2 ...]"
    echo "Example: $0 records_management/data/*.xml"
    exit 1
fi

# Odoo XML Schema (simplified for basic validation)
ODOO_SCHEMA="/tmp/odoo_xml_schema.rng"

# Create a basic Odoo XML schema for validation
cat > "$ODOO_SCHEMA" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<grammar xmlns="http://relaxng.org/ns/structure/1.0"
         datatypeLibrary="http://www.w3.org/2001/XMLSchema-datatypes">

  <start>
    <element name="odoo">
      <optional>
        <attribute name="noupdate">
          <data type="boolean"/>
        </attribute>
      </optional>
      <zeroOrMore>
        <element name="data">
          <optional>
            <attribute name="noupdate">
              <data type="boolean"/>
            </attribute>
          </optional>
          <zeroOrMore>
            <choice>
              <element name="record">
                <attribute name="model"/>
                <attribute name="id"/>
                <zeroOrMore>
                  <element name="field">
                    <attribute name="name"/>
                    <optional>
                      <attribute name="eval"/>
                      <attribute name="ref"/>
                      <attribute name="type"/>
                    </optional>
                    <text/>
                  </element>
                </zeroOrMore>
              </element>
              <element name="template">
                <attribute name="id"/>
                <zeroOrMore>
                  <element name="field">
                    <attribute name="name"/>
                    <text/>
                  </element>
                </zeroOrMore>
              </element>
              <element name="menuitem">
                <attribute name="id"/>
                <optional>
                  <attribute name="name"/>
                  <attribute name="parent"/>
                  <attribute name="action"/>
                  <attribute name="sequence"/>
                </optional>
              </element>
              <element name="act_window">
                <attribute name="id"/>
                <optional>
                  <attribute name="name"/>
                  <attribute name="res_model"/>
                  <attribute name="view_mode"/>
                </optional>
              </element>
            </choice>
          </zeroOrMore>
        </element>
      </zeroOrMore>
    </element>
  </start>
</grammar>
EOF

print_status "Starting XML validation with jing-trang..."
print_status "Using schema: $ODOO_SCHEMA"

# Validate each XML file
for xml_file in "$@"; do
    if [ ! -f "$xml_file" ]; then
        print_warning "File not found: $xml_file"
        continue
    fi

    print_status "Validating: $xml_file"

    # Run jing validation
    if jing "$ODOO_SCHEMA" "$xml_file" 2>&1; then
        print_success "✓ $xml_file is valid"
    else
        print_error "✗ $xml_file has validation errors:"
        # Re-run to show the actual errors
        jing "$ODOO_SCHEMA" "$xml_file"
    fi
done

# Clean up
rm -f "$ODOO_SCHEMA"

print_success "XML validation completed!"
print_status "For more detailed Odoo-specific validation, use:"
echo "  python3 development-tools/syntax-tools/find_syntax_errors.py"
