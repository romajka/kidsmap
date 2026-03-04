"""Test discovery bridge for src/ layout.

Django's default `manage.py test` discovery starts from the repository root.
This module imports app tests so they are discovered without explicit labels.
"""

from catalog.tests import *  # noqa: F401,F403
