#!/usr/bin/env python3
"""
Manual fix for specific syntax errors caused by ensure_one() insertion
"""

def fix_specific_syntax_errors():
    """Fix specific syntax errors in affected files"""

    fixes = [
        # records_chain_of_custody.py - fix indentation after if statement
        {
            'file': 'records_management/models/records_chain_of_custody.py',
            'old': '''        if previous_records and previous_records.custody_to_id != self.custody_from_id:
        self.chain_integrity = "broken"
        self.message_post(
        body=_("Chain of custody integrity broken: Previous custodian mismatch"),
        message_type="comment",
        )''',
            'new': '''        if previous_records and previous_records.custody_to_id != self.custody_from_id:
            self.chain_integrity = "broken"
            self.message_post(
                body=_("Chain of custody integrity broken: Previous custodian mismatch"),
                message_type="comment",
            )'''
        },

        # paper_bale_source_document.py - fix unterminated string
        {
            'file': 'records_management/models/paper_bale_source_document.py',
            'old': '''        self.message_post(body=_("Document confirmed by %s", self.env.user.name))
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": "success",
                "message": _("Document confirmed successfully"),
            },
        }

    def action_done(self):
        "Mark document as done"
        self.ensure_one()
        if self.state != "confirmed":
            raise UserError(_("Only confirmed documents can be marked as done"))

        self.state = "done"
        self.processed_date = fields.Datetime.now()
        self.message_post(body=_("Document marked as done by %s", self.env.user.name))

    def action_cancel(self):
        """Cancel the document"
        self.ensure_one()''',
            'new': '''        self.message_post(body=_("Document confirmed by %s", self.env.user.name))
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": "success",
                "message": _("Document confirmed successfully"),
            },
        }

    def action_done(self):
        """Mark document as done"""
        self.ensure_one()
        if self.state != "confirmed":
            raise UserError(_("Only confirmed documents can be marked as done"))

        self.state = "done"
        self.processed_date = fields.Datetime.now()
        self.message_post(body=_("Document marked as done by %s", self.env.user.name))

    def action_cancel(self):
        """Cancel the document"""
        self.ensure_one()'''
        }
    ]

    for fix in fixes:
        filepath = fix['file']
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            if fix['old'] in content:
                new_content = content.replace(fix['old'], fix['new'])

                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)

                print(f"✅ Fixed {filepath}")
            else:
                print(f"⚠️ Pattern not found in {filepath}")

        except Exception as e:
            print(f"❌ Error fixing {filepath}: {e}")

if __name__ == "__main__":
    print("🔧 FIXING SPECIFIC SYNTAX ERRORS")
    print("=" * 40)
    fix_specific_syntax_errors()
    print("=" * 40)
    print("✅ Manual fix complete")
