-- SIMPLE SQL PATCH for res_partner columns
-- Copy and paste this entire block into Odoo.sh SQL console
-- Safe to run multiple times (uses IF NOT EXISTS)

-- Add transitory_field_config_id
ALTER TABLE res_partner ADD COLUMN IF NOT EXISTS transitory_field_config_id INTEGER;

-- Add field_label_config_id  
ALTER TABLE res_partner ADD COLUMN IF NOT EXISTS field_label_config_id INTEGER;

-- Add allow_transitory_items with default
ALTER TABLE res_partner ADD COLUMN IF NOT EXISTS allow_transitory_items BOOLEAN DEFAULT TRUE;

-- Add max_transitory_items with default
ALTER TABLE res_partner ADD COLUMN IF NOT EXISTS max_transitory_items INTEGER DEFAULT 100;

-- Set defaults for any existing NULL values
UPDATE res_partner SET allow_transitory_items = TRUE WHERE allow_transitory_items IS NULL;
UPDATE res_partner SET max_transitory_items = 100 WHERE max_transitory_items IS NULL;

-- Verification query - should show 4 columns
SELECT column_name, data_type, column_default
FROM information_schema.columns 
WHERE table_name = 'res_partner' 
AND column_name IN (
    'transitory_field_config_id',
    'field_label_config_id',
    'allow_transitory_items',
    'max_transitory_items'
)
ORDER BY column_name;
