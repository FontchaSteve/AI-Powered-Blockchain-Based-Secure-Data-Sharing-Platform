---
name: debug-django-templates
description: Debug and fix common errors in Django HTML templates, including syntax issues, missing assets, and CSS class problems.
---

# Debug Django Templates

## Workflow

1. **Read the template file** to identify syntax errors or issues.
2. **Check context variables** in the corresponding view to ensure all required data is passed.
3. **Verify base template** includes necessary CSS/JS libraries (e.g., Bootstrap if used).
4. **Fix CSS class names** to match the loaded frameworks (e.g., Bootstrap classes).
5. **Test rendering** by running the Django server and checking for errors.

## Common Issues

- Missing Bootstrap CSS when using Bootstrap classes.
- Incorrect class names (e.g., `justify-between` instead of `justify-content-between`).
- Template syntax errors like unclosed tags.
- Missing context variables in views.
- Conflicting CSS between custom styles and frameworks.

## Usage

Use this skill when Django templates fail to render properly or display incorrectly.