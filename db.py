from os import environ, getenv

from niki.settings import BASE_DIR
from niki.settings import RADIUS

DB_TYPE = getenv("DB_TYPE", "sqlite").lower()
LDAP = getenv("LDAP", "False") == "True"

WITHLDAP = False
if LDAP:
    try:
        import ldap

        WITHLDAP = True
    except:
        pass

if DB_TYPE == "postgres":
    DB_SETTINGS = {
        "NAME": environ["DB_NAME"],
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "USER": environ["DB_USERNAME"],
        "PASSWORD": environ["DB_PASSWORD"],
        "HOST": environ["DB_ADDR"],
    }
elif DB_TYPE == "mysql":
    DB_SETTINGS = {
        "NAME": environ["DB_NAME"],
        "ENGINE": "django.db.backends.mysql",
        "USER": environ["DB_USERNAME"],
        "PASSWORD": environ["DB_PASSWORD"],
        "HOST": environ["DB_ADDR"],
    }
else:
    DB_SETTINGS = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": str(BASE_DIR / "db.sqlite3"),
    }

if WITHLDAP:
    LDAP_SETTINGS = {
        "NAME": environ["LDAP_ADDR"],
        "ENGINE": "ldapdb.backends.ldap",
        "USER": environ["LDAP_USER"],
        "PASSWORD": environ["LDAP_PASSWORD"],
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
