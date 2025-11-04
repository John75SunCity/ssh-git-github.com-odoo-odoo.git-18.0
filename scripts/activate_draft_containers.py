#!/usr/bin/env python3
"""
Activate Draft Containers - Create Missing Stock.Quant Records

ISSUE:
- Containers in 'draft' state never got stock.quant records created
- My Inventory portal page shows empty because it queries stock.quant

SOLUTION:
- Activate all draft containers (change state to 'active')
- This triggers automatic stock.quant creation via write() method

USAGE:
    Odoo shell:
    $ odoo-bin shell -d your_database -c your_config.conf
    
    >>> exec(open('scripts/activate_draft_containers.py').read())

RESULT:
- ✅ Creates stock.quant for each container
- ✅ Sets owner_id to customer (partner_id)
- ✅ Integrates with native Odoo inventory
- ✅ My Inventory portal page works correctly
"""

from odoo import api, SUPERUSER_ID

def activate_draft_containers(env):
    """
    Activate all draft containers to create stock.quant records.
    
    This fixes the issue where portal My Inventory shows empty
    because containers were created in draft state without quants.
    """
    
    # Find all draft containers
    Container = env['records.container']
    draft_containers = Container.search([
        ('state', '=', 'draft'),
        ('quant_id', '=', False),  # No stock.quant yet
    ])
    
    print(f"\n{'='*60}")
    print(f"ACTIVATING DRAFT CONTAINERS")
    print(f"{'='*60}")
    print(f"Found {len(draft_containers)} draft containers without stock.quant")
    
    if not draft_containers:
        print("✅ No action needed - all containers have stock.quant records")
        return
    
    # Group by customer for reporting
    by_customer = {}
    for container in draft_containers:
        customer_name = container.partner_id.name or 'Unknown'
        if customer_name not in by_customer:
            by_customer[customer_name] = []
        by_customer[customer_name].append(container)
    
    print(f"\nContainers by customer:")
    for customer, containers in by_customer.items():
        print(f"  - {customer}: {len(containers)} containers")
    
    print(f"\n{'='*60}")
    print("ACTIVATING CONTAINERS...")
    print(f"{'='*60}\n")
    
    # Activate containers (this will trigger stock.quant creation)
    success_count = 0
    error_count = 0
    
    for container in draft_containers:
        try:
            # Change state to active (triggers stock.quant creation)
            container.write({'state': 'active'})
            
            # Verify quant was created
            if container.quant_id:
                print(f"✅ {container.name} ({container.partner_id.name})")
                print(f"   Stock.quant ID: {container.quant_id.id}")
                print(f"   Owner: {container.quant_id.owner_id.name}")
                print(f"   Location: {container.quant_id.location_id.complete_name}\n")
                success_count += 1
            else:
                print(f"⚠️  {container.name} - Stock.quant not created (check logs)\n")
                error_count += 1
                
        except Exception as e:
            print(f"❌ {container.name} - Error: {str(e)}\n")
            error_count += 1
    
    print(f"{'='*60}")
    print("ACTIVATION COMPLETE")
    print(f"{'='*60}")
    print(f"✅ Successfully activated: {success_count}")
    if error_count > 0:
        print(f"❌ Errors: {error_count}")
    print(f"\nTotal stock.quant records created: {success_count}")
    print("\n💡 Portal users can now see their inventory in 'My Inventory' page!\n")


if __name__ == '__main__':
    # This runs when executed in Odoo shell
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        activate_draft_containers(env)
        env.cr.commit()
