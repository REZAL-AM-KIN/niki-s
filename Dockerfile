FROM python:3
WORKDIR /niki

COPY requirements-ldap.txt ./
COPY requirements.txt ./
RUN apt-get update && apt-get install -y gpg python3 python3-pip libsasl2-dev libldap2-dev libssl-dev ldap-utils libz-dev libjpeg-dev libfreetype6-dev python-dev
RUN pip install --no-cache-dir -r requirements-ldap.txt
COPY . .
CMD ["sh", "entrypoint.sh"]