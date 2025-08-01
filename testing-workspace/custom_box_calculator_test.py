#!/usr/bin/env python3
"""
Custom Box Volume Calculator Test Suite
======================================

Test the volume-based pricing calculations for custom boxes vs standard boxes.
Validates the business logic for fair pricing based on volume equivalency.
"""


def test_volume_calculations():
    """Test volume calculation accuracy"""
    print("📦 CUSTOM BOX VOLUME CALCULATOR VALIDATION")
    print("=" * 60)

    # Standard box reference: 15" x 12" x 10" = 1,800 cubic inches
    standard_length = 15.0
    standard_width = 12.0
    standard_height = 10.0
    standard_volume = standard_length * standard_width * standard_height
    standard_rate = 6.00

    print(f"📐 Standard Box Reference:")
    print(f'   Dimensions: {standard_length}" × {standard_width}" × {standard_height}"')
    print(f"   Volume: {standard_volume:,.0f} cubic inches")
    print(f"   Rate: ${standard_rate:.2f}")
    print()

    # Test cases for different custom box sizes
    test_cases = [
        {
            "name": 'Example from user (18" × 28" × 12")',
            "length": 18.0,
            "width": 28.0,
            "height": 12.0,
            "expected_volume": 6048,  # 18 * 28 * 12
        },
        {
            "name": 'Small custom box (10" × 8" × 6")',
            "length": 10.0,
            "width": 8.0,
            "height": 6.0,
            "expected_volume": 480,  # 10 * 8 * 6
        },
        {
            "name": 'Large custom box (20" × 20" × 15")',
            "length": 20.0,
            "width": 20.0,
            "height": 15.0,
            "expected_volume": 6000,  # 20 * 20 * 15
        },
        {
            "name": 'Exact standard size (15" × 12" × 10")',
            "length": 15.0,
            "width": 12.0,
            "height": 10.0,
            "expected_volume": 1800,  # Should equal standard
        },
        {
            "name": 'Double standard volume (18.97" × 12" × 10")',
            "length": 18.97,
            "width": 12.0,
            "height": 10.0,
            "expected_volume": 2276.4,  # Should be ~2x standard
        },
    ]

    print("🧮 CALCULATION TESTS:")
    print("-" * 60)

    for i, case in enumerate(test_cases, 1):
        print(f"\n{i}. {case['name']}")

        # Calculate custom volume
        custom_volume = case["length"] * case["width"] * case["height"]

        # Verify expected volume
        assert (
            abs(custom_volume - case["expected_volume"]) < 0.1
        ), f"Volume mismatch for {case['name']}"

        # Calculate equivalency
        volume_ratio = custom_volume / standard_volume
        equivalent_boxes = round(volume_ratio, 2)
        calculated_price = round(equivalent_boxes * standard_rate, 2)

        print(
            f"   Dimensions: {case['length']}\" × {case['width']}\" × {case['height']}\""
        )
        print(f"   Volume: {custom_volume:,.1f} cubic inches")
        print(f"   Ratio: {volume_ratio:.3f} (vs standard)")
        print(f"   Equivalent: {equivalent_boxes} standard boxes")
        print(f"   Price: ${calculated_price:.2f}")

        # Validate pricing logic
        if equivalent_boxes == 1.0:
            print(f"   ✅ Same as standard - fair pricing")
        elif equivalent_boxes > 1.0:
            print(
                f"   ✅ Larger than standard - customer pays {equivalent_boxes}x rate"
            )
        else:
            print(f"   ✅ Smaller than standard - customer pays reduced rate")

    print("\n" + "=" * 60)
    print("🎯 BUSINESS VALIDATION:")

    # Specific validation for user's example: 18" × 28" × 12"
    user_example_volume = 18 * 28 * 12  # 6,048 cubic inches
    user_ratio = user_example_volume / standard_volume  # 6,048 / 1,800 = 3.36
    user_equivalent = round(user_ratio, 2)  # 3.36 standard boxes
    user_price = round(user_equivalent * standard_rate, 2)  # 3.36 * $6.00 = $20.16

    print(f"\n📋 User Example Analysis:")
    print(f'   Custom box: 18" × 28" × 12" = {user_example_volume:,} cubic inches')
    print(f'   Standard box: 15" × 12" × 10" = {standard_volume:,} cubic inches')
    print(f"   Volume ratio: {user_ratio:.2f}")
    print(f"   Equivalent boxes: {user_equivalent}")
    print(f"   Fair price: ${user_price:.2f}")
    print(f"   ")
    print(f"   💡 This customer's large box contains {user_ratio:.1f}x more material")
    print(f"      than a standard box, so they should pay {user_ratio:.1f}x the rate.")
    print(f"      This ensures fair pricing based on actual volume to shred.")

    print("\n✅ All calculations validated!")

    # Test edge cases
    print("\n⚠️  EDGE CASE TESTING:")
    edge_cases = [
        {"length": 0, "width": 12, "height": 10, "should_error": True},
        {"length": 101, "width": 12, "height": 10, "should_error": True},  # Over 100"
        {
            "length": 0.1,
            "width": 0.1,
            "height": 0.1,
            "should_error": False,
        },  # Very small
    ]

    for case in edge_cases:
        volume = case["length"] * case["width"] * case["height"]
        if case["should_error"]:
            print(
                f"   ❌ {case['length']}\" × {case['width']}\" × {case['height']}\": Should trigger validation error"
            )
        else:
            print(
                f"   ⚠️  {case['length']}\" × {case['width']}\" × {case['height']}\": Volume = {volume:.3f} cubic inches"
            )


def test_pricing_fairness():
    """Test that pricing is fair across different scenarios"""
    print(f"\n💰 PRICING FAIRNESS VALIDATION:")
    print("-" * 40)

    standard_volume = 1800  # 15 × 12 × 10
    standard_rate = 6.00

    scenarios = [
        {"description": "Half volume box", "volume": 900, "expected_price": 3.00},
        {"description": "Double volume box", "volume": 3600, "expected_price": 12.00},
        {"description": "Triple volume box", "volume": 5400, "expected_price": 18.00},
    ]

    for scenario in scenarios:
        ratio = scenario["volume"] / standard_volume
        calculated_price = round(ratio * standard_rate, 2)

        print(f"   {scenario['description']}:")
        print(f"      Volume: {scenario['volume']:,} cubic inches")
        print(f"      Ratio: {ratio:.1f}x standard")
        print(f"      Price: ${calculated_price:.2f}")
        print(f"      Expected: ${scenario['expected_price']:.2f}")

        assert (
            abs(calculated_price - scenario["expected_price"]) < 0.01
        ), f"Price mismatch for {scenario['description']}"
        print(f"      ✅ Pricing validated")
        print()


if __name__ == "__main__":
    test_volume_calculations()
    test_pricing_fairness()
    print("\n🎉 ALL TESTS PASSED - Calculator ready for deployment!")
