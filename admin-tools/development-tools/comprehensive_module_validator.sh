#!/bin/bash
# Comprehensive Odoo Module Validation Script
# Validates models, demo data, and module structure

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MODULE_DIR="/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0/records_management"
TEMP_SCHEMA="/tmp/odoo_demo_schema.rng"

echo -e "${BLUE}🔍 Comprehensive Odoo Module Validation${NC}"
echo "=========================================="
echo "Module: records_management"
echo "Date: $(date)"
echo

# Function to print status
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 1. Validate Python Models
echo -e "${BLUE}📝 Phase 1: Python Model Validation${NC}"
echo "-------------------------------------"

MODEL_COUNT=$(find "$MODULE_DIR/models" -name "*.py" -not -name "__init__.py" -not -name "__pycache__" | wc -l)
echo "Found $MODEL_COUNT Python model files"

# Syntax validation
echo "Checking Python syntax..."
SYNTAX_ERRORS=0
VALID_MODELS=0

for model_file in "$MODULE_DIR"/models/*.py; do
    if [[ "$model_file" == *"__init__.py" ]] || [[ "$model_file" == *"__pycache__"* ]]; then
        continue
    fi

    filename=$(basename "$model_file")
    if python3 -m py_compile "$model_file" 2>/dev/null; then
        ((VALID_MODELS++))
    else
        ((SYNTAX_ERRORS++))
        print_error "Syntax error in $filename"
    fi
done

if [ $SYNTAX_ERRORS -eq 0 ]; then
    print_status "All $VALID_MODELS Python models have valid syntax"
else
    print_warning "$SYNTAX_ERRORS models have syntax errors"
fi

# 2. Validate Demo Data Files
echo
echo -e "${BLUE}📊 Phase 2: Demo Data Validation${NC}"
echo "-----------------------------------"

# Create Odoo XML schema for demo data (more flexible for HTML content)
cat > "$TEMP_SCHEMA" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<grammar ns="" xmlns="http://relaxng.org/ns/structure/1.0"
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
          <zeroOrMore>
            <element name="record">
              <attribute name="id"/>
              <attribute name="model"/>
              <zeroOrMore>
                <element name="field">
                  <attribute name="name"/>
                  <optional>
                    <attribute name="eval"/>
                  </optional>
                  <optional>
                    <attribute name="ref"/>
                  </optional>
                  <optional>
                    <attribute name="type"/>
                  </optional>
                  <zeroOrMore>
                    <choice>
                      <text/>
                      <element name="div">
                        <zeroOrMore>
                          <choice>
                            <text/>
                            <element name="p">
                              <zeroOrMore>
                                <choice>
                                  <text/>
                                  <element name="strong">
                                    <zeroOrMore>
                                      <choice>
                                        <text/>
                                        <element name="br">
                                          <empty/>
                                        </element>
                                      </choice>
                                    </zeroOrMore>
                                  </element>
                                  <element name="br">
                                    <empty/>
                                  </element>
                                </choice>
                              </zeroOrMore>
                            </element>
                            <element name="br">
                              <empty/>
                            </element>
                          </choice>
                        </zeroOrMore>
                      </element>
                    </choice>
                  </zeroOrMore>
                </element>
              </zeroOrMore>
            </element>
          </zeroOrMore>
        </element>
      </zeroOrMore>
    </element>
  </start>
</grammar>
EOF

DEMO_XML_COUNT=$(find "$MODULE_DIR/demo" -name "*.xml" | wc -l)
echo "Found $DEMO_XML_COUNT demo XML files"

# Check if jing-trang is available
if command -v jing &> /dev/null; then
    echo "Using jing-trang for XML validation..."

    DEMO_VALID=0
    DEMO_INVALID=0

    for xml_file in "$MODULE_DIR"/demo/*.xml; do
        filename=$(basename "$xml_file")

        # First check if XML is well-formed
        if xmllint --noout "$xml_file" 2>/dev/null; then
            # For HTML content files, just check basic structure
            if [[ "$filename" == *"mail_templates"* ]] || [[ "$filename" == *"template"* ]]; then
                # Check if it has proper Odoo structure
                if grep -q "<odoo" "$xml_file" && grep -q "<data>" "$xml_file" && grep -q "<record" "$xml_file"; then
                    ((DEMO_VALID++))
                    print_status "$filename: Valid (HTML content)"
                else
                    ((DEMO_INVALID++))
                    print_error "$filename: Missing Odoo structure"
                fi
            else
                # Use jing-trang for regular data files
                if jing "$TEMP_SCHEMA" "$xml_file" 2>/dev/null; then
                    ((DEMO_VALID++))
                    print_status "$filename: Valid"
                else
                    ((DEMO_INVALID++))
                    print_error "$filename: Schema validation failed"
                    jing "$TEMP_SCHEMA" "$xml_file" 2>&1 | head -3
                fi
            fi
        else
            ((DEMO_INVALID++))
            print_error "$filename: Not well-formed XML"
        fi
    done

    if [ $DEMO_INVALID -eq 0 ]; then
        print_status "All $DEMO_VALID demo XML files are valid"
    else
        print_warning "$DEMO_INVALID demo files have issues"
    fi

else
    echo "jing-trang not found, using basic XML validation..."

    DEMO_VALID=0
    DEMO_INVALID=0

    for xml_file in "$MODULE_DIR"/demo/*.xml; do
        filename=$(basename "$xml_file")

        if xmllint --noout "$xml_file" 2>/dev/null; then
            ((DEMO_VALID++))
            print_status "$filename: Well-formed"
        else
            ((DEMO_INVALID++))
            print_error "$filename: Invalid XML"
        fi
    done
fi

# 3. Model Relationship Analysis
echo
echo -e "${BLUE}🔗 Phase 3: Model Relationship Analysis${NC}"
echo "------------------------------------------"

# Analyze model imports and dependencies
echo "Analyzing model dependencies..."

# Check models/__init__.py
if [ -f "$MODULE_DIR/models/__init__.py" ]; then
    MODEL_IMPORTS=$(grep -c "from . import" "$MODULE_DIR/models/__init__.py" || echo "0")
    print_status "Found $MODEL_IMPORTS model imports in __init__.py"
else
    print_error "models/__init__.py not found"
fi

# Check for common model patterns
echo "Checking model patterns..."

# Count models by category
CORE_MODELS=$(find "$MODULE_DIR/models" -name "*records*.py" | wc -l)
BILLING_MODELS=$(find "$MODULE_DIR/models" -name "*billing*.py" | wc -l)
NAID_MODELS=$(find "$MODULE_DIR/models" -name "*naid*.py" | wc -l)
FSM_MODELS=$(find "$MODULE_DIR/models" -name "*fsm*.py" | wc -l)

echo "Model categories:"
echo "  Core Records: $CORE_MODELS models"
echo "  Billing: $BILLING_MODELS models"
echo "  NAID Compliance: $NAID_MODELS models"
echo "  FSM Integration: $FSM_MODELS models"

# 4. Security and Access Analysis
echo
echo -e "${BLUE}🔐 Phase 4: Security Analysis${NC}"
echo "-------------------------------"

if [ -f "$MODULE_DIR/security/ir.model.access.csv" ]; then
    ACCESS_RULES=$(wc -l < "$MODULE_DIR/security/ir.model.access.csv")
    print_status "Found $ACCESS_RULES access rules in security CSV"
else
    print_warning "Security access CSV not found"
fi

# 5. View and Template Analysis
echo
echo -e "${BLUE}👀 Phase 5: Views and Templates${NC}"
echo "----------------------------------"

VIEW_COUNT=$(find "$MODULE_DIR/views" -name "*.xml" 2>/dev/null | wc -l || echo "0")
TEMPLATE_COUNT=$(find "$MODULE_DIR" -name "*template*.xml" 2>/dev/null | wc -l || echo "0")

print_status "Found $VIEW_COUNT view files"
print_status "Found $TEMPLATE_COUNT template files"

# 6. Final Summary
echo
echo -e "${BLUE}📊 Final Validation Summary${NC}"
echo "================================"

echo "Python Models:"
echo "  Total: $MODEL_COUNT files"
echo "  Valid: $VALID_MODELS files"
echo "  Errors: $SYNTAX_ERRORS files"

echo
echo "Demo Data:"
echo "  Total: $DEMO_XML_COUNT files"
echo "  Valid: $DEMO_VALID files"
echo "  Issues: $DEMO_INVALID files"

echo
echo "Module Structure:"
echo "  Views: $VIEW_COUNT files"
echo "  Templates: $TEMPLATE_COUNT files"
echo "  Access Rules: $ACCESS_RULES rules"

# Overall status
TOTAL_ISSUES=$((SYNTAX_ERRORS + DEMO_INVALID))

if [ $TOTAL_ISSUES -eq 0 ]; then
    echo
    print_status "🎉 Module validation PASSED - All components are valid!"
    echo "The Records Management module is ready for deployment."
else
    echo
    print_warning "⚠️  Module validation found $TOTAL_ISSUES issues"
    echo "Please review and fix the reported problems before deployment."
fi

# Cleanup
rm -f "$TEMP_SCHEMA"

echo
echo -e "${BLUE}Validation completed at $(date)${NC}"
