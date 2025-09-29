# Report models removed - QWeb templates work without custom Python models
# since they don't require complex data processing.
# 
# Standard QWeb reports automatically receive:
# - docs: Records from the report's model
# - doc_ids: List of record IDs
# - doc_model: Model name
# - data: Additional data passed to the report
#
# Custom Python report models are only needed for:
# - Complex data aggregation
# - Multiple model data combination  
# - Custom formatting/calculations
# - Special rendering logic
