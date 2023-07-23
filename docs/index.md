# Django Signal Webhooks

[![Coverage Status][coverage-badge]][coverage]
[![GitHub Workflow Status][status-badge]][status]
[![PyPI][pypi-badge]][pypi]
[![GitHub][licence-badge]][licence]
[![GitHub Last Commit][repo-badge]][repo]
[![GitHub Issues][issues-badge]][issues]
[![Downloads][downloads-badge]][pypi]

[![Python Version][version-badge]][pypi]
[![Django Version][django-badge]][pypi]

```shell
pip install django-signal-webhooks
```

---

**Documentation**: [https://mrthearman.github.io/django-signal-webhooks/](https://mrthearman.github.io/django-signal-webhooks/)

**Source Code**: [https://github.com/MrThearMan/django-signal-webhooks/](https://github.com/MrThearMan/django-signal-webhooks/)

**Contributing**: [https://github.com/MrThearMan/django-signal-webhooks/blob/main/CONTRIBUTING.md](https://github.com/MrThearMan/django-signal-webhooks/blob/main/CONTRIBUTING.md)

---

This library enables you to add webhooks to a Django project for any create/update/delete
events on your models with a simple configuration. New webhooks can be added in the
admin panel, with or without authentication, with plenty of hooks into the webhook sending
process to customize them for your needs.

```python
# project/settings.py

# Add to instaled apps
INSTALLED_APPS = [
    ...
    "signal_webhooks",
    ...
]

# Add default webhook configuration to the User model
SIGNAL_WEBHOOKS = {
    "HOOKS": {
        "django.contrib.auth.models.User": ...,
    },
}
```

[coverage-badge]: https://coveralls.io/repos/github/MrThearMan/django-signal-webhooks/badge.svg?branch=main
[status-badge]: https://img.shields.io/github/actions/workflow/status/MrThearMan/django-signal-webhooks/test.yml?branch=main
[pypi-badge]: https://img.shields.io/pypi/v/django-signal-webhooks
[licence-badge]: https://img.shields.io/github/license/MrThearMan/django-signal-webhooks
[repo-badge]: https://img.shields.io/github/last-commit/MrThearMan/django-signal-webhooks
[issues-badge]: https://img.shields.io/github/issues-raw/MrThearMan/django-signal-webhooks
[version-badge]: https://img.shields.io/pypi/pyversions/django-signal-webhooks
[downloads-badge]: https://img.shields.io/pypi/dm/django-signal-webhooks
[django-badge]: https://img.shields.io/pypi/djversions/django-signal-webhooks

[coverage]: https://coveralls.io/github/MrThearMan/django-signal-webhooks?branch=main
[status]: https://github.com/MrThearMan/django-signal-webhooks/actions/workflows/test.yml
[pypi]: https://pypi.org/project/django-signal-webhooks
[licence]: https://github.com/MrThearMan/django-signal-webhooks/blob/main/LICENSE
[repo]: https://github.com/MrThearMan/django-signal-webhooks/commits/main
[issues]: https://github.com/MrThearMan/django-signal-webhooks/issues
