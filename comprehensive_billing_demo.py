#!/usr/bin/env python3
"""
Comprehensive Records Management Billing System Demo

This demonstrates the full billing capabilities including:
- Multiple storage types with different rates
- Comprehensive service pricing
- Monthly minimum handling
- Automatic invoice generation
- All service types from your pricing structure
"""

def demo_comprehensive_billing():
    print("=" * 70)
    print("COMPREHENSIVE RECORDS MANAGEMENT BILLING SYSTEM")
    print("=" * 70)
    
    print("\n🏢 CUSTOMER: City of El Paso")
    print("📅 BILLING PERIOD: July 2025")
    print("-" * 50)
    
    # Storage fees
    print("\n📦 STORAGE FEES:")
    print("-" * 30)
    
    storage_items = [
        ("Standard boxes", 850, 0.32),
        ("Map boxes", 150, 0.45),
        ("Specialty boxes", 25, 0.50),
        ("Pallets", 5, 2.50)
    ]
    
    total_storage = 0
    for item, qty, rate in storage_items:
        cost = qty * rate
        total_storage += cost
        print(f"{item:20} {qty:4} × ${rate:5.2f} = ${cost:8.2f}")
    
    monthly_minimum = 45.00
    print(f"\nSubtotal storage: ${total_storage:.2f}")
    
    if total_storage >= monthly_minimum:
        print(f"✅ Above minimum (${monthly_minimum:.2f})")
        final_storage = total_storage
    else:
        adjustment = monthly_minimum - total_storage
        print(f"❌ Below minimum - adjustment: ${adjustment:.2f}")
        final_storage = monthly_minimum
        
    print(f"Final storage total: ${final_storage:.2f}")
    
    # Service fees for the month
    print("\n🔧 SERVICE FEES:")
    print("-" * 30)
    
    services = [
        ("New boxes (10 pack) with delivery", 3, 45.00),
        ("Pickup service", 8, 25.00),
        ("Delivery service", 12, 25.00),
        ("Trip charges", 5, 15.00),
        ("Shredding per box", 45, 3.50),
        ("Hard drive destruction", 12, 15.00),
        ("Regular retrieval - boxes", 28, 8.50),
        ("Regular retrieval - files", 67, 3.50),
        ("Rush retrieval - boxes", 3, 15.00),
        ("Emergency service 1HR", 1, 50.00),
        ("64 gallon bin service", 15, 35.00),
        ("96 gallon bin service", 8, 45.00),
        ("Shred box - standard", 22, 15.00),
        ("Shred box - double", 5, 25.00),
        ("Labor hours", 8.5, 35.00),
        ("Indexing per box", 125, 12.50),
        ("Transportation (120 miles)", 120, 0.75),
        ("Damaged property - bin", 1, 75.00),
    ]
    
    total_services = 0
    for service, qty, rate in services:
        cost = qty * rate
        total_services += cost
        print(f"{service:35} {qty:6.1f} × ${rate:6.2f} = ${cost:8.2f}")
    
    print(f"\nTotal services: ${total_services:.2f}")
    
    # Grand total
    grand_total = final_storage + total_services
    print("\n" + "=" * 50)
    print("💰 MONTHLY INVOICE SUMMARY")
    print("=" * 50)
    print(f"Storage fees:           ${final_storage:10.2f}")
    print(f"Service fees:           ${total_services:10.2f}")
    print("-" * 40)
    print(f"TOTAL AMOUNT:           ${grand_total:10.2f}")
    
    # Show detailed invoice breakdown
    print("\n📄 DETAILED INVOICE LINE ITEMS")
    print("=" * 70)
    print("CITY OF EL PASO - July 2025 Records Management Services")
    print("-" * 50)
    
    print("\nSTORAGE SERVICES:")
    for item, qty, rate in storage_items:
        cost = qty * rate
        print(f"  {item:30} {qty:4} × ${rate:5.2f} = ${cost:8.2f}")
    
    if total_storage < monthly_minimum:
        adjustment = monthly_minimum - total_storage
        print(f"  Monthly storage minimum fee              = ${adjustment:8.2f}")
    
    print(f"\nSTORAGE SUBTOTAL:                          ${final_storage:8.2f}")
    
    print("\nSERVICE CHARGES:")
    for service, qty, rate in services:
        cost = qty * rate
        print(f"  {service:40} {qty:6.1f} × ${rate:6.2f} = ${cost:8.2f}")
    
    print(f"\nSERVICES SUBTOTAL:                         ${total_services:8.2f}")
    print("-" * 60)
    print(f"TOTAL AMOUNT DUE:                          ${grand_total:8.2f}")
    
    print("\n" + "=" * 70)
    print("✅ BILLING SYSTEM CAPABILITIES")
    print("=" * 70)
    
    capabilities = [
        "✅ Multiple storage types (standard, map, specialty, pallet)",
        "✅ Monthly minimum fee calculation with adjustment",
        "✅ 50+ different service types and pricing",
        "✅ Automatic cost calculation for service requests",
        "✅ Quantity-based pricing for bulk services", 
        "✅ Emergency, rush, and regular service levels",
        "✅ Transportation cost calculation",
        "✅ Labor tracking and billing",
        "✅ Shred bin services (all sizes)",
        "✅ Hard drive and document destruction",
        "✅ Product sales integration",
        "✅ Monthly billing automation",
        "✅ Detailed invoice generation",
        "✅ Integration with Odoo accounting",
        "✅ Service request workflow",
        "✅ Portal access for customers",
        "✅ Department-level billing",
        "✅ Approval workflows for services"
    ]
    
    for capability in capabilities:
        print(f"  {capability}")
    
    print("\n🚀 HOW TO USE:")
    print("  1. Configure pricing: Records Management > Billing > Configuration")
    print("  2. Create service requests: Records Management > Services")
    print("  3. Monthly billing runs automatically via cron job")
    print("  4. Review billing periods: Records Management > Billing > Periods")
    print("  5. Generate invoices: Billing Period > Generate Invoices")
    print("  6. View invoices: Accounting > Customer Invoices")
    
    print("\n📊 YOUR SYSTEM MATCHES YOUR BUSINESS MODEL:")
    print("  - Handles all your current service types")
    print("  - Supports your pricing structure")
    print("  - Integrates with Odoo accounting")
    print("  - Provides customer portal access")
    print("  - Automates monthly billing")
    print("  - Generates professional invoices")

if __name__ == "__main__":
    demo_comprehensive_billing()
