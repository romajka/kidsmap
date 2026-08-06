#!/usr/bin/env bash
set -euo pipefail

SCHEDULE_TYPE="${1:-daily}"

echo "===================================================="
echo "KIDSMAP AUTOMATED SEO SCHEDULED AUDIT ($SCHEDULE_TYPE)"
echo "===================================================="

PYTHON_BIN="./.venv/bin/python"
if [ ! -x "$PYTHON_BIN" ]; then
    PYTHON_BIN="python"
fi

case "$SCHEDULE_TYPE" in
    post_deploy)
        echo "Running post-deploy technical & sitemap audit..."
        $PYTHON_BIN manage.py audit_sitemap
        $PYTHON_BIN manage.py audit_schema
        $PYTHON_BIN manage.py audit_seo --only-errors
        ;;

    daily)
        echo "Running daily SEO audit & applying safe Level A auto-fixes..."
        $PYTHON_BIN manage.py audit_sitemap
        $PYTHON_BIN manage.py audit_seo
        $PYTHON_BIN manage.py apply_seo_fixes --safe-only --apply
        $PYTHON_BIN manage.py seo_report
        ;;

    weekly)
        echo "Running weekly full SEO crawl & audit report..."
        $PYTHON_BIN manage.py audit_sitemap
        $PYTHON_BIN manage.py audit_schema
        $PYTHON_BIN manage.py audit_internal_links
        $PYTHON_BIN manage.py audit_seo
        $PYTHON_BIN manage.py apply_seo_fixes --safe-only --apply
        $PYTHON_BIN manage.py seo_report --format=markdown
        ;;

    *)
        echo "Unknown schedule type: $SCHEDULE_TYPE (use post_deploy, daily, or weekly)"
        exit 1
        ;;
esac

echo "===================================================="
echo "✓ SCHEDULED SEO AUDIT ($SCHEDULE_TYPE) FINISHED"
echo "===================================================="
