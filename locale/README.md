# Localization (Translation) Guide

This project uses the standard Django internationalization (I18N) system.
Field names in the admin panel and static text in templates support Russian (`ru`) and English (`en`) languages.

## How to Add or Change a Translation

### 1. Preparing Strings in Code
For text to be translatable, it must be wrapped:
- In Python code (`models.py`, `views.py`): use `gettext_lazy` or `_`.
  ```python
  from django.utils.translation import gettext_lazy as _
  name = _("Text to translate")
  ```
- In HTML templates: use the `{% trans %}` tag.
  ```html
  {% load i18n %}
  <p>{% trans "Text to translate" %}</p>
  ```

### 2. Collecting Strings for Translation
After making changes to the code or templates, run the command to update `.po` files:
```bash
python manage.py makemessages -l en
python manage.py makemessages -l ru
```
This command will find all new strings and add them to:
- `locale/en/LC_MESSAGES/django.po`
- `locale/ru/LC_MESSAGES/django.po`

### 3. Editing Translations
Open the required `.po` file and find strings with an empty `msgstr`. Enter the translation there.
Example:
```po
msgid "Home"
msgstr "Главная"
```

### 4. Compiling Translations
For Django to "see" the changes, they must be compiled into the binary `.mo` format:
```bash
python manage.py compilemessages
```
**Important:** Always run this command after editing `.po` files, otherwise the changes will not be reflected on the site.

## Main Settings
Language configuration is located in `settings/base.py`:
- `LANGUAGE_CODE = "ru-ru"` (default language)
- `LANGUAGES` (list of available languages)
- `LOCALE_PATHS` (path to this `locale/` folder)
