from __future__ import annotations

from urllib.parse import parse_qs, unquote, urlsplit

from django.core.exceptions import ImproperlyConfigured


SUPPORTED_SCHEMES = {
    "postgres": "django.db.backends.postgresql",
    "postgresql": "django.db.backends.postgresql",
    "mysql": "django.db.backends.mysql",
    "mariadb": "django.db.backends.mysql",
    "sqlite": "django.db.backends.sqlite3",
}


def parse_database_url(value: str, *, env_name: str, conn_max_age: int = 60) -> dict:
    raw_value = (value or "").strip()
    if not raw_value:
        raise ImproperlyConfigured(f"{env_name} must be configured.")

    parsed = urlsplit(raw_value)
    scheme = parsed.scheme.lower()
    engine = SUPPORTED_SCHEMES.get(scheme)
    if not engine:
        supported = ", ".join(sorted(SUPPORTED_SCHEMES))
        raise ImproperlyConfigured(
            f"Unsupported scheme in {env_name}: {scheme!r}. Supported schemes: {supported}."
        )

    if scheme == "sqlite":
        database_name = unquote(parsed.path or "")
        if not database_name:
            raise ImproperlyConfigured(f"{env_name} must include a SQLite database path.")
        return {
            "ENGINE": engine,
            "NAME": database_name,
        }

    database_name = unquote((parsed.path or "").lstrip("/"))
    if not database_name:
        raise ImproperlyConfigured(f"{env_name} must include a database name.")
    if not parsed.username:
        raise ImproperlyConfigured(f"{env_name} must include a database user.")
    if parsed.password is None:
        raise ImproperlyConfigured(f"{env_name} must include a database password.")
    if not parsed.hostname:
        raise ImproperlyConfigured(f"{env_name} must include a database host.")

    config = {
        "ENGINE": engine,
        "NAME": database_name,
        "USER": unquote(parsed.username),
        "PASSWORD": unquote(parsed.password),
        "HOST": parsed.hostname,
        "PORT": str(parsed.port or (5432 if scheme in {"postgres", "postgresql"} else 3306)),
        "CONN_MAX_AGE": conn_max_age,
        "CONN_HEALTH_CHECKS": True,
    }

    query = parse_qs(parsed.query, keep_blank_values=False)
    options: dict[str, str] = {}
    for option_name in ("sslmode", "connect_timeout", "application_name"):
        values = query.get(option_name)
        if values:
            options[option_name] = values[-1]

    if scheme in {"mysql", "mariadb"}:
        options.update(
            {
                "charset": "utf8mb4",
                "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
            }
        )

    if options:
        config["OPTIONS"] = options
    return config
