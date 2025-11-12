# Grok-4 Integration for Odoo Development

This directory contains tools for integrating xAI's Grok-4 model with your Odoo development workflow.

## 🎯 **What's Available:**

### **1. VS Code Custom Agent** (`odoo-expert.agent.md`)
- Uses GitHub Copilot infrastructure
- No API key needed
- Works in VS Code chat with `@odoo-expert`
- **Not actual Grok** - enhanced Copilot with Odoo expertise

### **2. Direct Grok-4 API** (`grok-helper.py`)
- Uses real Grok-4-0709 model from xAI
- Requires xAI API key
- Command-line interface or VS Code task
- **True Grok** - actual xAI model with expert prompting

---

## 🚀 **Setup: Direct Grok-4 API**

### **Step 1: Install xAI SDK**
```bash
pip install xai-sdk
```

### **Step 2: Get Your API Key**
1. Go to https://console.x.ai/
2. Navigate to "API Keys" section
3. Create a new API key
4. Copy your key (starts with `xai-...`)

### **Step 3: Set Your API Key**

**Option A: Environment Variable (Recommended)**
```bash
# Add to your ~/.zshrc or ~/.bash_profile
export XAI_API_KEY="xai-your-key-here"

# Reload shell
source ~/.zshrc
```

**Option B: Direct in Command**
```bash
# Pass key directly (not recommended for security)
XAI_API_KEY="xai-your-key-here" python .github/agents/grok-helper.py "your question"
```

---

## 💬 **Usage:**

### **Method 1: VS Code Task (Easiest)**
1. Press `Cmd+Shift+P` (macOS) or `Ctrl+Shift+P` (Windows/Linux)
2. Type "Tasks: Run Task"
3. Select "🤖 Ask Grok-4 (Odoo Expert)"
4. Enter your question
5. See Grok's response in the terminal

### **Method 2: Command Line**
```bash
# From repository root
python .github/agents/grok-helper.py "Why are my course slides empty?"
python .github/agents/grok-helper.py "Analyze the records.container model"
python .github/agents/grok-helper.py "Should I create a new model or extend existing?"
```

---

## 📊 **Pricing (from your screenshot):**

**grok-4-0709**: 
- Input: $3.00 per million tokens
- Output: $15.00 per million tokens
- Context: 256K tokens (2M input, 480 output)

**Cost Examples:**
- Simple question (500 tokens in + 1000 out): ~$0.017
- Complex analysis (5000 tokens in + 3000 out): ~$0.06
- Very reasonable for development assistance!

---

## 🔍 **How to Verify It's Using Grok-4:**

### **Check 1: Model Name in Response**
The script uses `model="grok-4-0709"` - this is the actual Grok-4 model.

### **Check 2: API Console**
- Log in to https://console.x.ai/
- Check "Usage" section
- You'll see API calls with `grok-4-0709` listed

### **Check 3: Response Style**
Grok-4 has a distinctive analytical style and deep reasoning capabilities that differ from Copilot.

---

## 🆚 **VS Code Agent vs Direct API:**

| Feature | @odoo-expert (Copilot) | grok-helper.py (True Grok) |
|---------|------------------------|----------------------------|
| **Model** | GitHub Copilot | xAI Grok-4-0709 |
| **API Key** | Not needed | Required |
| **Cost** | Included in Copilot | Pay per use (~$0.02-0.06/query) |
| **Integration** | VS Code chat | Terminal/Task |
| **Context** | VS Code workspace | Odoo expert prompt |
| **Best For** | Quick questions, code completion | Deep analysis, architecture decisions |

---

## 💡 **Best Practices:**

### **Use VS Code Agent (@odoo-expert) For:**
- Quick code questions
- Simple model lookups
- File navigation help
- Syntax checking

### **Use Direct Grok-4 API For:**
- Complex architectural decisions
- Deep code analysis
- Multi-step reasoning
- Advanced troubleshooting

---

## 🔒 **Security:**

⚠️ **Never commit your API key!**

Your API key is stored in:
- Environment variable (safe ✅)
- NOT in this repository (safe ✅)

The `.gitignore` already excludes sensitive files.

---

## 🛠️ **Troubleshooting:**

### **"XAI_API_KEY not set" Error:**
```bash
# Check if key is set
echo $XAI_API_KEY

# If empty, set it
export XAI_API_KEY="xai-your-key-here"
```

### **"Module not found: xai_sdk":**
```bash
pip install xai-sdk
# or
pip3 install xai-sdk
```

### **Want to use different model:**
Edit `grok-helper.py` and change:
```python
model="grok-4-0709"  # Current
model="grok-3-mini"  # Cheaper alternative
```

---

## 📚 **Example Questions:**

```bash
# Architecture
python .github/agents/grok-helper.py "Should I create records.billing.contact or extend res.partner?"

# Debugging  
python .github/agents/grok-helper.py "Why does security_level='1' fail for records.location?"

# Best Practices
python .github/agents/grok-helper.py "What's the correct way to implement barcode-driven container activation?"

# Analysis
python .github/agents/grok-helper.py "Analyze the portal inventory workflow and suggest optimizations"
```

---

**Happy coding with Grok-4! 🚀**
