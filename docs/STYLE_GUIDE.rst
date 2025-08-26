Records Management – RST Style Guide
===================================

Purpose
-------
This document defines the reStructuredText conventions for the Records Management module.
Use it for all documentation-like content (README, docs/, report templates notes).
It must not trigger changes to Python logic; keep doc-only edits isolated.

Line width
----------
- Target 100 characters per line.
- Wrap paragraphs manually.
- Prefer leaving URLs unbroken where practical.

Headings hierarchy
------------------
Use underline-only adornments. Do not skip levels.

- H1: =
- H2: -
- H3: ~
- H4: ^

Links
-----
- Inline: ``Link text <https://example.com>``_.
- Repeated links: define a named target once and reuse, for example::

   .. _odoo-guides: https://www.odoo.com/documentation

  Then reference as: ``odoo-guides_``.
- Prefer relative links within this repo. Keep anchors stable.

Inline markup
-------------
- Use ````inline literals```` for code/field names.
- Use ``*emphasis*`` and ``**strong**`` sparingly.

Code blocks
-----------
- Use ``::`` or ``.. code-block:: <lang>`` with language hints (python, xml, csv, bash).
- Indent code blocks by 3+ spaces and avoid tabs.

Admonitions
-----------
Use short, actionable messages:

- ``.. note::``
- ``.. warning::``
- ``.. tip::``

Lists and tables
----------------
- Prefer bullet and enumerated lists.
- Use grid tables only when necessary; keep them simple.

Images
------
- Place assets under ``static/`` or ``docs/_static``.
- Reference with ``.. image::`` and include ``:alt:`` text.

Cross-references
----------------
- When referencing models/fields, prefer ``:code:`` literals.
- Avoid Sphinx domain roles unless the docs build is configured.

Changelog style
---------------
- Use conventional commits in Git.
- Mirror relevant summaries in docs when appropriate.
- Avoid duplicating internal implementation details.

i18n notes
----------
- Keep documentation strings in English.
- UI strings in code must follow the project i18n policy: only static templates inside ``_()`` and percent-style interpolation after translation, e.g., ``_("Text %s") % value``.

Minimal feature doc skeleton
----------------------------
- Overview (what/why)
- Configuration (RM Module Configurator toggles if any)
- Security/Access notes
- Usage steps and key actions
- Edge cases/limitations
- API and model hooks (method names only)

Validation
----------
Run the "Validate Records Management Module" task. Documentation changes must not introduce syntax/build errors.
