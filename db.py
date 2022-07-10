from os import environ, getenv

from niki.settings import BASE_DIR
from niki.settings import RADIUS, WITHLDAP

DB_TYPE = getenv("DB_TYPE", "sqlite").lower()

if DB_TYPE == "postgres":
    DB_ENGINE = "django.db.backends.postgresql_psycopg2"
    DB_NAME = environ["DB_NAME"]
elif DB_TYPE == "mysql":
    DB_ENGINE = "django.db.backends.mysql"
    DB_NAME = environ["DB_NAME"]
else:
    DB_ENGINE = "django.db.backends.sqlite3"
    DB_NAME = str(BASE_DIR / "db.sqlite3")

DB_SETTINGS = {
    "NAME": DB_NAME,
    "ENGINE": DB_ENGINE,
    "USER": getenv("DB_USERNAME", ""),
    "PASSWORD": getenv("DB_PASSWORD", ""),
    "HOST": getenv("DB_ADDR", ""),
}

if WITHLDAP:
    import ldap
    LDAP_SETTINGS = {
        "NAME": "ldap://"+environ["LDAP_ADDR"],
        "ENGINE": "ldapdb.backends.ldap",
        "USER": "cn=admin,"+environ["LDAP_BASE_DN"],
        "PASSWORD": environ["LDAP_ADMIN_PASSWORD"],
        # 'TLS': True,
        'CONNECTION_OPTIONS': {
            ldap.OPT_X_TLS_DEMAND: True,
        }
    }

if RADIUS:
    RADIUS_SETTINGS = {
        'NAME': 'radius',
        'ENGINE': 'django.db.backends.mysql',
        'USER': environ["RADIUS_USERNAME"],
        'PASSWORD': environ["RADIUS_PASSWORD"],
        'HOST': environ["RADIUS_ADDR"],
    }
