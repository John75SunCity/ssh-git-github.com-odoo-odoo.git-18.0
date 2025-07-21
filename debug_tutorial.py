#!/usr/bin/env python3
"""
Simple debugging tutorial for beginners
This file demonstrates basic debugging concepts you can practice with.
"""

def calculate_total_boxes(departments):
    """Calculate total boxes across departments"""
    total = 0
    
    print("🔍 Starting calculation...")
    
    for dept_name, box_count in departments.items():
        print(f"Processing {dept_name}: {box_count} boxes")
        
        # SET A BREAKPOINT HERE! (Click on line number)
        total += box_count
        
        print(f"Running total: {total}")
    
    return total

def simulate_records_workflow():
    """Simulate a basic records management workflow"""
    print("📦 Simulating Records Management Workflow")
    
    # Sample data (like what you might have in Odoo)
    departments = {
        "Finance": 50,
        "HR": 25,
        "Legal": 75,
        "Operations": 30
    }
    
    print("🏢 Department data:")
    for dept, boxes in departments.items():
        print(f"   • {dept}: {boxes} boxes")
    
    # SET A BREAKPOINT HERE to inspect the departments dictionary
    total_boxes = calculate_total_boxes(departments)
    
    print(f"\n📊 Total boxes in storage: {total_boxes}")
    
    # Simulate some business logic
    if total_boxes > 100:
        storage_status = "High capacity"
        action_needed = "Consider additional storage"
    else:
        storage_status = "Normal capacity"
        action_needed = "No action needed"
    
    # SET ANOTHER BREAKPOINT HERE to see the final results
    result = {
        "total_boxes": total_boxes,
        "status": storage_status,
        "recommendation": action_needed
    }
    
    return result

def main():
    """Main function to demonstrate debugging"""
    print("🐛 Welcome to Debugging Tutorial!")
    print("=" * 40)
    
    print("\n💡 Instructions:")
    print("1. Set breakpoints by clicking on line numbers (look for the comments)")
    print("2. Press F5 to start debugging")
    print("3. Select 'Test Python Module' from the dropdown")
    print("4. Use the debugging controls to step through the code")
    print("5. Watch the Variables panel to see how values change")
    
    print("\n🚀 Starting simulation...")
    
    # This will run the workflow
    result = simulate_records_workflow()
    
    print(f"\n✅ Final result: {result}")
    print("\n🎉 Debugging tutorial complete!")

if __name__ == "__main__":
    main()
