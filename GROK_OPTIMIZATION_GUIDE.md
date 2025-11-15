# Grok-4 Optimization Guide

## 🚀 Available Grok Commands

### 1. **grok** - Simple, direct questions
```bash
grok "your question here"
```
- Fast, no context loading
- Good for general questions
- No codebase context

### 2. **grok-full** - Full codebase context (legacy)
```bash
grok-full "analyze records.container model"
```
- Loads entire codebase every time (slow)
- ~148KB context
- Use for comprehensive analysis
- **Deprecated** - use `grok-indexed` instead

### 3. **grok-indexed** - Smart cached index (RECOMMENDED) ⭐
```bash
grok-indexed "does records.container have a weight field?"
```
- **10x+ faster** than grok-full
- Persistent index (626 files, 4.7M chars)
- Auto-rebuilds when files change
- Smart file selection (stays within token limits)
- Best for frequent queries

## 📚 Advanced Usage

### Focus on Specific Files
```bash
grok-indexed --focus "records_container.py,customer_inventory_demo.xml" "validate demo data"
```

### Force Rebuild Index
```bash
grok-indexed --rebuild
```
- Run after major codebase changes
- Index auto-rebuilds if files modified
- Stored at `~/.github/agents/grok-index.json`

## 🎯 How It Works

### Index Structure
```json
{
  "built_at": "2025-11-14T...",
  "files": {
    "records_management/models/records_container.py": {
      "content": "...",
      "size": 12345,
      "mtime": 1234567890
    }
  },
  "summary": {
    "total_files": 1092,
    "total_chars": 8316144,
    "models": [...],
    "demos": [...],
    "views": [...],
    "controllers": [...],
    "wizards": [...],
    "security": [...]
  }
}
```

### Smart File Selection
The indexed version prioritizes:
1. **All Models**: Complete records_management + records_management_fsm models (313 files)
2. **All Views**: Every XML view definition (310 files)
3. **All Demos**: Complete demo data (10 files)
4. **All Controllers**: Web controllers and routes (11 files)
5. **All Wizards**: Wizard implementations (28 files)
6. **All Security**: Access rules and permissions (16 files)
7. **Everything else**: JS, SCSS, docs, etc. (404 files)
8. **Token limit**: Max 450K chars (~112K tokens) to stay within Grok's 131K limit
9. **Scope**: ONLY records_management and records_management_fsm (no other workspace files)

### Auto-Rebuild Triggers
Index rebuilds automatically when:
- Any `.py` file in workspace is modified
- Any `.xml` file in workspace is modified
- Index file doesn't exist

## 📊 Performance Comparison

| Command | Load Time | Files | Context Size | Use Case |
|---------|-----------|-------|--------------|----------|
| `grok` | Instant | 0 | None | Simple questions |
| `grok-full` | 5-10s | 148KB | ~148KB | Comprehensive (deprecated) |
| `grok-indexed` | 1-2s | 1092 | Smart 450KB | **Best for everything** ⭐ |

## 💡 Best Practices

### ✅ DO:
- Use `grok-indexed` for field validation
- Use `--focus` when you know specific files
- Let index auto-rebuild (it's smart)
- Ask specific questions for better answers

### ❌ DON'T:
- Use `grok-full` for simple questions (overkill)
- Manually rebuild index unless needed
- Ask vague questions (be specific)

## 🔧 Setup

### Initial Setup (Done)
```bash
# 1. Script already at ~/.github/agents/grok-indexed.py
# 2. Alias already in ~/.zshrc
# 3. Index built at ~/.github/agents/grok-index.json
```

### New Terminal Setup
```bash
source ~/.zshrc  # Load aliases
grok-indexed --rebuild  # Build initial index
```

## 📝 Examples

### Validate Demo Data
```bash
grok-indexed "List all fields in customer_inventory_demo.xml that don't exist in records.container"
```

### Check Model Fields
```bash
grok-indexed "Does records.container have weight, storage_start_date, and last_access_date fields?"
```

### Focus on Specific Model
```bash
grok-indexed --focus "records_container.py" "What are all the Date fields?"
```

### Analyze Relationships
```bash
grok-indexed "How are records.container and records.location related?"
```

## 🐛 Troubleshooting

### Error: "This model's maximum prompt length is 131072"
- **Cause**: Too much context loaded
- **Fix**: Use `--focus` to limit files or reduce smart selection
- Already handled in smart selection logic

### Index Not Updating
```bash
grok-indexed --rebuild  # Force rebuild
```

### Wrong Answers
- **Cause**: Index might be stale
- **Fix**: 
  ```bash
  grok-indexed --rebuild
  ```
- Index auto-rebuilds, but manual rebuild ensures latest code

## 🎓 Learning Resources

### Understanding the Code
```python
# Location: ~/.github/agents/grok-indexed.py

# Key functions:
# - build_index(): Creates persistent cache
# - should_rebuild_index(): Checks if rebuild needed
# - load_index(): Loads cached or rebuilds
# - build_context(): Smart file selection
# - ask_grok(): Sends to API with context
```

## 📈 Stats

- **Total Files Indexed**: 1092 (ONLY records_management + records_management_fsm)
- **Total Characters**: 8,316,144 (~2MB of Python/XML/JS code)
- **Python Models**: 313
- **XML Views**: 310
- **XML Demo Files**: 10
- **Controllers**: 11
- **Wizards**: 28
- **Security Files**: 16
- **Other Files**: 404 (JS, SCSS, docs, etc.)
- **Index File Size**: ~8.5MB (JSON with full source code)
- **Response Time**: 1-2 seconds (vs 5-10s for grok-full)
- **Coverage**: 100% of records_management modules, 0% of other workspace files

---

**Last Updated**: November 14, 2025  
**Version**: 1.0  
**Maintained By**: GitHub Copilot + John Cope
