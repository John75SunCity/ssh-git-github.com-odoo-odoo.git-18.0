# Test file to verify VS Code ruler visibility

# This line should be right at the 88-character ruler mark (PEP8) ✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓
# This line should extend well past the 120-character ruler and show you where the hard limit is set for Odoo development ✓✓✓✓✓✓✓

def test_function():
    """
    This function tests the ruler visibility in VS Code.
    You should see vertical lines at:
    - 88 characters (soft guideline)
    - 120 characters (hard limit)
    """
    very_long_variable_name_that_approaches_the_ruler = "test value"
    return very_long_variable_name_that_approaches_the_ruler

# If you can see the rulers, you should see them as thin vertical lines
# The 88-char ruler helps with PEP8 compliance
# The 120-char ruler is the absolute maximum for Odoo development
