"""The additive age column remains compatible with the previous web image."""
from django.db import connection
from django.test import TestCase

from catalog.models import Place
from catalog.testcases.utils import create_quality_place


class TestPlaceAgeReleaseCompatibility(TestCase):
    def test_old_writer_can_insert_without_the_new_age_column(self):
        source = create_quality_place(age_varies_by_program=True)
        quote = connection.ops.quote_name
        later_fields = {'age_varies_by_program', 'uses_slug_only_urls',
                        'public_slug_az', 'public_slug_ru', 'public_slug_en'}
        fields = [field for field in Place._meta.concrete_fields
                  if not field.primary_key and field.name not in later_fields]
        columns = ', '.join(quote(field.column) for field in fields)
        values = ', '.join('%s' if field.name == 'slug' else quote(field.column) for field in fields)
        table = quote(Place._meta.db_table)
        # An old image writes every old field, omitting the newly added column.
        with connection.cursor() as cursor:
            cursor.execute(f'INSERT INTO {table} ({columns}) SELECT {values} FROM {table} WHERE id = %s RETURNING age_varies_by_program',
                           ['legacy-writer-age-default', source.pk])
            self.assertIs(cursor.fetchone()[0], False)
