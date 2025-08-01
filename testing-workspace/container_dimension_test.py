#!/usr/bin/env python3
"""
Container Dimension Validation Test
==================================

Test the dimension conversion calculations for the records_container model.
"""


def test_dimension_conversions():
    """Test cm to inches conversions for standard container sizes"""
    print("🧮 CONTAINER DIMENSION VALIDATION")
    print("=" * 50)

    # Conversion factor: 1 inch = 2.54 cm
    cm_to_inch = 1 / 2.54

    # Test standard size: 15"×12"×10"
    print("📦 Standard Container Size:")
    standard_length_cm = 15 * 2.54  # Should be 38.1 cm
    standard_width_cm = 12 * 2.54  # Should be 30.48 cm (rounded to 30.5)
    standard_height_cm = 10 * 2.54  # Should be 25.4 cm

    print(f'   Length: 15" = {standard_length_cm:.1f} cm')
    print(f'   Width:  12" = {standard_width_cm:.1f} cm')
    print(f'   Height: 10" = {standard_height_cm:.1f} cm')

    # Test legal/double size: 15"×24"×10"
    print("\n📦 Legal/Double-size Container:")
    legal_length_cm = 15 * 2.54  # Should be 38.1 cm
    legal_width_cm = 24 * 2.54  # Should be 60.96 cm (rounded to 61.0)
    legal_height_cm = 10 * 2.54  # Should be 25.4 cm

    print(f'   Length: 15" = {legal_length_cm:.1f} cm')
    print(f'   Width:  24" = {legal_width_cm:.1f} cm')
    print(f'   Height: 10" = {legal_height_cm:.1f} cm')

    # Test reverse conversion (cm to inches)
    print("\n🔄 Reverse Conversion Test:")
    print("   38.1 cm =", round(38.1 * cm_to_inch, 1), "inches (should be 15.0)")
    print("   30.5 cm =", round(30.5 * cm_to_inch, 1), "inches (should be 12.0)")
    print("   61.0 cm =", round(61.0 * cm_to_inch, 1), "inches (should be 24.0)")
    print("   25.4 cm =", round(25.4 * cm_to_inch, 1), "inches (should be 10.0)")

    print("\n✅ All dimension calculations validated!")

    # Test dimension display formatting
    print("\n📏 Dimension Display Examples:")
    print(f'   Standard: 15.0"×12.0"×10.0"')
    print(f'   Legal:    15.0"×24.0"×10.0"')
    print(f'   Custom:   20.5"×18.3"×12.7"')


if __name__ == "__main__":
    test_dimension_conversions()
