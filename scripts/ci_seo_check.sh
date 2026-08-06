#!/usr/bin/env bash
set -euo pipefail

echo "===================================================="
echo "KIDSMAP CI/CD PRE-DEPLOYMENT SEO & INTEGRITY CHECK"
echo "===================================================="

PYTHON_BIN="./.venv/bin/python"
if [ ! -x "$PYTHON_BIN" ]; then
    PYTHON_BIN="python"
fi

echo "1. Running Django system check..."
$PYTHON_BIN manage.py check

echo "2. Checking for unapplied migrations..."
$PYTHON_BIN manage.py makemigrations --check --dry-run

echo "3. Running SEO and Sitemap test suites..."
DJANGO_TESTING=1 $PYTHON_BIN manage.py test src.catalog.testcases.test_seo_audit_system src.catalog.testcases.public.TestPublicPagesSmoke.test_sitemap_xml_is_valid_xml

echo "4. Auditing sitemap.xml..."
$PYTHON_BIN manage.py audit_sitemap

echo "5. Validating Schema.org microdata..."
$PYTHON_BIN manage.py audit_schema

echo "6. Running SEO Audit (Critical Error Check)..."
$PYTHON_BIN manage.py audit_seo --only-errors

echo "===================================================="
echo "✓ ALL CI/CD PRE-DEPLOYMENT SEO CHECKS PASSED!"
echo "===================================================="
