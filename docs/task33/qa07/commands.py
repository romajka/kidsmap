"""Migration generation only; no project env or existing database permitted."""
def main(mode, labels):
    import django
    from django.conf import settings
    from django.core.management import call_command
    from guard import validate_settings, install_network_guard, install_libpq_guard
    validate_settings(settings)
    install_network_guard()
    install_libpq_guard()
    django.setup()
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT current_database(), inet_server_addr() IS NULL")
        database, unix = cursor.fetchone()
        assert database == 'qa_stage04' and unix
    call_command('makemigrations', 'catalog', name='task33_business_permissions', interactive=False)
    return 0
