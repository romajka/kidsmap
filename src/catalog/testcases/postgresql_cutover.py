from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.test import RequestFactory, SimpleTestCase, TestCase

from catalog.domain_admin.category import CategoryAdmin, SubcategoryAdmin
from catalog.models import Category, Subcategory
from config.database_url import parse_database_url


class DatabaseUrlTests(SimpleTestCase):
    def test_postgres_url_is_decoded_and_has_health_checks(self):
        config = parse_database_url(
            "postgresql://kids%20user:p%40ss@postgres:5432/kidsmap?sslmode=require",
            env_name="DATABASE_URL",
        )

        self.assertEqual(config["ENGINE"], "django.db.backends.postgresql")
        self.assertEqual(config["USER"], "kids user")
        self.assertEqual(config["PASSWORD"], "p@ss")
        self.assertEqual(config["NAME"], "kidsmap")
        self.assertTrue(config["CONN_HEALTH_CHECKS"])
        self.assertEqual(config["OPTIONS"]["sslmode"], "require")

    def test_incomplete_url_fails_with_clear_error(self):
        with self.assertRaisesMessage(ImproperlyConfigured, "database password"):
            parse_database_url(
                "postgresql://kids@postgres:5432/kidsmap",
                env_name="DATABASE_URL",
            )


class TaxonomyAdminSoftDeleteTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username="taxonomy-admin",
            email="taxonomy-admin@example.com",
            password="StrongPass123!!",
        )
        self.request = RequestFactory().post("/admin/catalog/category/")
        self.request.user = self.user
        self.category_admin = CategoryAdmin(Category, admin.site)
        self.subcategory_admin = SubcategoryAdmin(Subcategory, admin.site)

    def test_category_admin_delete_archives_instead_of_removing(self):
        category = Category.objects.create(code="ARCHIVE", name="Archive")

        self.category_admin.delete_model(self.request, category)

        category.refresh_from_db()
        self.assertFalse(category.is_active)
        self.assertIsNotNone(category.deleted_at)
        self.assertEqual(category.deleted_by, self.user)

    def test_bulk_category_delete_archives_every_row(self):
        Category.objects.create(code="ARCHIVE-1", name="Archive 1")
        Category.objects.create(code="ARCHIVE-2", name="Archive 2")

        self.category_admin.delete_queryset(
            self.request,
            Category.objects.filter(code__startswith="ARCHIVE-"),
        )

        self.assertEqual(Category.objects.filter(code__startswith="ARCHIVE-").count(), 2)
        self.assertEqual(
            Category.objects.filter(
                code__startswith="ARCHIVE-", is_active=False, deleted_by=self.user
            ).count(),
            2,
        )

    def test_subcategory_admin_delete_archives_instead_of_removing(self):
        category = Category.objects.create(code="PARENT", name="Parent")
        subcategory = Subcategory.objects.create(category=category, code="archive-child", name="Child")

        self.subcategory_admin.delete_model(self.request, subcategory)

        subcategory.refresh_from_db()
        self.assertFalse(subcategory.is_active)
        self.assertIsNotNone(subcategory.deleted_at)
        self.assertEqual(subcategory.deleted_by, self.user)
