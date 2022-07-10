FROM python:3.10-alpine
WORKDIR /niki

COPY requirements.txt .
COPY requirements-ldap.txt .
COPY requirements-mysql.txt .
COPY requirements-postgres.txt .
RUN apk add --no-cache gcc libressl-dev musl-dev libffi-dev build-base openldap-dev mariadb-dev git curl
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s CMD curl -v -X GET -H "Accept: application/json" --fail http://localhost:8000/status/ || exit 1
RUN pip install --no-cache-dir -r requirements-ldap.txt && pip install --no-cache-dir -r requirements-postgres.txt && pip install --no-cache-dir -r requirements-mysql.txt
COPY . .
CMD ["sh", "entrypoint.sh"]