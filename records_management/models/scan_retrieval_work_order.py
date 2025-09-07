"""Scan Retrieval Work Order model.

Coordinates scanning work for retrieved physical files into digital assets for electronic transmission.
Key capabilities:
- Lifecycle/state machine: draft → confirmed → scanning → processing → quality_review → ready_for_delivery → delivered → completed/cancelled
- Scheduling and timing: scheduled start, estimated completion (heuristic per resolution/OCR/enhancement), actual timestamps
- Metrics and progress: item/page counts, progress %, produced file count and total MB
- Relations:
  * scan_item_ids (scan.retrieval.item) – items to scan, provides page counts
  * digital_asset_ids (scan.digital.asset) – files produced by this order
  * partner_id (res.partner), portal_request_id (portal.request), scanner_id (maintenance.equipment)
- Electronic transmission methods: portal, email, secure link, FTP with fees and confirmation tracking
- Chatter integration via mail.thread + mail.activity.mixin
- Sequence: scan.retrieval.work.order (assigned at create)
"""

"""Legacy scan retrieval work order model removed.

Tombstone only; unified retrieval model covers scanning workflow.
"""

# No model defined.
