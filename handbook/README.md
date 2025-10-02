# Records Management Handbook Index

Internal reference documentation (auto-generated).

## Sections
- [Custom Fields Reference](custom-fields-reference.md)
- [Views & Templates Mapping](views-and-templates-mapping.md)
- [Access Rights Matrix](access-rights-matrix.md)
- [Module Statistics](module-statistics.md)
- [Menu Structure](menu-structure.md) *(placeholder – generation not yet implemented)*

## Regeneration
From repository root:
```
python3 scripts/update_handbook.py --module-path records_management --handbook-path RECORDS_MANAGEMENT_HANDBOOK.md --section all --split
```

This writes/updates the monolithic `RECORDS_MANAGEMENT_HANDBOOK.md` and per-section markdown files in this directory.

## Notes
- These files are NOT part of any Odoo module path.
- Safe to keep large; for personal/internal use.
- Edit only outside auto-generated section markers if needed in the monolithic file.
