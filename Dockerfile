FROM python:3.10-alpine
WORKDIR /niki

#RUN apk add --no-cache libressl-dev musl-dev libffi-dev
RUN apk add --no-cache gcc git curl openldap-dev build-base mariadb-dev supervisor
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s CMD curl -v -X GET -H "Accept: application/json" --fail http://localhost:8000/status/ || exit 1
COPY requirements.txt .
COPY requirements-ldap.txt .
COPY requirements-mysql.txt .
COPY requirements-postgres.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements-ldap.txt
RUN pip install --no-cache-dir -r requirements-postgres.txt
RUN pip install --no-cache-dir -r requirements-mysql.txt
COPY . .
CMD ["sh", "entrypoint.sh"]