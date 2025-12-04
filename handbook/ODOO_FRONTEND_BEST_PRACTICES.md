# Odoo Frontend Framework Best Practices (18.0/19.0)

> **Reference Guide for JavaScript/OWL Development**  
> Indexed from: https://www.odoo.com/documentation/19.0/developer/reference/frontend/framework_overview.html

---

## 🎯 Quick Reference

### Key Principles
1. **All new development should be done in OWL**, not legacy widgets
2. Use `setup()` method instead of constructors (constructors aren't overridable)
3. Templates should be in XML files (not inline `xml` helper) for translations
4. Use `useService()` hook to access services, not direct `env.services` access
5. Template names must follow: `addon_name.ComponentName`

---

## 📁 Code Structure

```
web/static/src/
├── core/          # Low-level features (utils, registries, browser)
├── fields/        # All field components
├── views/         # View components (form, list, kanban, etc.)
├── search/        # Control panel, search bar, search panel
└── webclient/     # Navbar, user menu, action service
```

### Import Convention
```javascript
// Use @web prefix for web module imports
import { memoize } from "@web/core/utils/functions";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
```

---

## 🧱 Building Blocks

### 1. Components (OWL)

**Basic Component Structure:**
```javascript
import { Component, useState } from "@odoo/owl";

class MyComponent extends Component {
    // ✅ CORRECT: Use string template reference
    static template = 'records_management.MyComponent';
    
    // ✅ CORRECT: Use setup(), not constructor
    setup() {
        this.state = useState({ value: 1 });
        // Access services via hook
        this.notification = useService("notification");
        this.orm = useService("orm");
    }
    
    // ❌ WRONG: Never use constructor
    // constructor(parent, props) { ... }
}
```

**Template File (my_component.xml):**
```xml
<?xml version="1.0" encoding="UTF-8" ?>
<templates xml:space="preserve">

<t t-name="records_management.MyComponent">
    <div t-on-click="increment">
        <t t-esc="state.value"/>
    </div>
</t>

</templates>
```

**File Organization (per component):**
- `my_component.js` - Component logic
- `my_component.xml` - QWeb template
- `my_component.scss` - Styles (optional)

### 2. Registries

Registries are key/value stores for extensibility:

```javascript
import { registry } from "@web/core/registry";

// Register a field component
registry.category("fields").add("my_field_char", MyFieldChar);

// Register a service
registry.category("services").add("myService", myService);

// Register a main component (extends web client)
registry.category("main_components").add("MyComponent", { Component: MyComponent });
```

**Common Registries:**
- `fields` - Field widgets
- `services` - Application services
- `main_components` - Components in MainComponentsContainer
- `actions` - Client actions
- `views` - View types

### 3. Services

Services are long-lived features with dependency injection:

```javascript
import { registry } from "@web/core/registry";

const myService = {
    dependencies: ["notification", "orm"],
    
    start(env, { notification, orm }) {
        // Service initialization
        return {
            doSomething() {
                notification.add("Hello!");
            }
        };
    }
};

registry.category("services").add("myService", myService);
```

**Using Services in Components:**
```javascript
setup() {
    // ✅ CORRECT: Use useService hook
    this.rpc = useService("rpc");
    this.notification = useService("notification");
    this.orm = useService("orm");
    this.action = useService("action");
    this.user = useService("user");
}
```

### 4. Hooks

**Essential Odoo Hooks:**

| Hook | Purpose | Import |
|------|---------|--------|
| `useService` | Access services | `@web/core/utils/hooks` |
| `useAutofocus` | Auto-focus element | `@web/core/utils/hooks` |
| `useBus` | Subscribe to event bus | `@web/core/utils/hooks` |
| `usePosition` | Position element relative to target | `@web/core/position_hook` |
| `usePager` | Display control panel pager | `@web/search/pager_hook` |

**Example: useBus**
```javascript
import { useBus } from "@web/core/utils/hooks";

setup() {
    useBus(this.env.bus, "some-event", (event) => {
        console.log(event);
    });
    // Automatically clears listener on unmount
}
```

---

## 🌐 Environment (this.env)

Components access the environment via `this.env`:

| Property | Description |
|----------|-------------|
| `env.bus` | Main event bus |
| `env.services` | All deployed services |
| `env.debug` | Debug mode string |
| `env._t` | Translation function |
| `env.isSmall` | Mobile mode (width <= 767px) |

```javascript
// Translation in component code
const message = this.env._t('some text');

// Check debug mode
if (this.env.debug) {
    console.log('Debug mode active');
}
```

---

## 📊 Domains

Use the Domain class for domain manipulation:

```javascript
import { Domain } from "@web/core/domain";

// Create domain
const domain = new Domain([["a", "=", 3]]);

// Check if record matches
domain.contains({ a: 3 }); // true

// Combine domains
const combined = Domain.and([
    [["a", "=", 1]], 
    "[('uid', '<=', uid)]"
]);

// Convert to string
combined.toString(); // ["&", ("a", "=", 1), ("uid", "<=", uid)]

// Evaluate with context
new Domain(`[('a', '>', b)]`).toList({ b: 3 }); // [['a', '>', 3]]
```

---

## 📡 Event Bus

Global events via `env.bus`:

```javascript
// Subscribe
env.bus.on("WEB_CLIENT_READY", null, doSomething);

// Common events:
// - ACTION_MANAGER:UI-UPDATED
// - ROUTE_CHANGE
// - RPC:REQUEST / RPC:RESPONSE
// - WEB_CLIENT_READY
// - CLEAR-CACHES
```

---

## 🔧 Context

### User Context
```javascript
setup() {
    const user = useService("user");
    console.log(user.context);
    // { allowed_company_ids: [1], lang: "en_US", tz: "America/Phoenix" }
}
```

### Action Context
```javascript
// Extend action context when calling actions
const actionService = useService("action");

actionService.doAction("addon_name.action_id", {
    additional_context: {
        default_period_id: periodId,
        search_default_customer: 1,
    }
});
```

---

## 🧩 Built-in Components

### Dropdown
```javascript
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
```

```xml
<Dropdown>
    <button>Click me</button>
    <t t-set-slot="content">
        <DropdownItem onSelected="selectItem">Item 1</DropdownItem>
    </t>
</Dropdown>
```

### CheckBox
```xml
<CheckBox value="boolean" t-on-change="onValueChange">
    Label Text
</CheckBox>
```

### Notebook (Tabs)
```xml
<Notebook orientation="'vertical'">
    <t t-set-slot="page_1" title="'Page 1'" isVisible="true">
        <h1>Content</h1>
    </t>
</Notebook>
```

### Pager
```xml
<Pager offset="0" limit="80" total="50" onUpdate="doSomething"/>
```

### SelectMenu
```xml
<SelectMenu choices="choices" value="selectedValue" onSelect="onSelect"/>
```

### TagsList
```xml
<TagsList tags="tags"/>
```

---

## 🐍 Python Expression Evaluator

Odoo includes a JS Python interpreter for view modifiers:

```javascript
import { evaluateExpr } from "@web/core/py_js/py";

evaluateExpr("1 + 2*{'a': 1}.get('b', 54) + v", { v: 33 }); // 142
```

---

## 🔍 Debug Mode

```javascript
// Check in component
if (this.env.debug) {
    // Debug-only code
}

// In XML views - use group
<field name="technical_field" groups="base.group_no_one"/>
```

**Debug Modes:**
- `debug` - General debug info
- `debug=assets` - Non-minified JS, source maps
- `debug=tests` - Include test tours

---

## 🚫 Anti-Patterns to Avoid

```javascript
// ❌ WRONG: Using constructor
class BadComponent extends Component {
    constructor(parent, props) {
        super(parent, props);
    }
}

// ❌ WRONG: Inline template in production code
class BadComponent extends Component {
    static template = xml`<div>inline</div>`;
}

// ❌ WRONG: Direct service access
someMethod() {
    this.env.services.notification.add("msg");
}

// ❌ WRONG: jQuery in new code
$('.selector').click();

// ✅ CORRECT: Use setup()
class GoodComponent extends Component {
    static template = 'addon.GoodComponent';
    
    setup() {
        this.notification = useService("notification");
    }
}
```

---

## 📦 Asset Bundles

Register JS/CSS in `__manifest__.py`:

```python
'assets': {
    'web.assets_backend': [
        'records_management/static/src/components/**/*',
    ],
    'web.assets_frontend': [
        'records_management/static/src/portal/**/*',
    ],
}
```

---

## 🔄 Patching Existing Components

```javascript
import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";

patch(FormController.prototype, {
    setup() {
        super.setup();
        // Add custom logic
    }
});
```

---

## 📝 Portal JavaScript Notes

For **portal** (public website) code:
- Use vanilla JavaScript (no OWL required)
- Avoid jQuery in Odoo 18+
- Use `web.assets_frontend` bundle
- Templates use QWeb but without OWL reactivity

---

## 🎓 Summary Checklist

- [ ] Use OWL for all new components
- [ ] Use `setup()` instead of constructor
- [ ] Templates in separate XML files
- [ ] Template names: `addon_name.ComponentName`
- [ ] Access services via `useService()` hook
- [ ] Use `Domain` class for domain manipulation
- [ ] Register components/services in registries
- [ ] Use `env.bus` for global events
- [ ] No jQuery in new code
- [ ] Use proper asset bundles

---

**Last Updated:** December 2024  
**Applies To:** Odoo 18.0, 19.0
