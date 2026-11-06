#!/bin/bash
set -e

SERVICE=$1
DAYS=${2:-30}

if [ -z "$SERVICE" ]; then
  echo "Usage: ./issue_cert.sh <service-name> [validity-days]"
  exit 1
fi

# Windows Git Bash path conversion fix
export MSYS_NO_PATHCONV=1

cd "$(dirname "$0")"

echo "Generating key for $SERVICE..."
openssl genrsa -out ${SERVICE}-key.pem 2048

echo "Creating CSR for $SERVICE..."
# Create temporary config for SAN
if [ "$SERVICE" = "proxy" ]; then
    # Proxy needs IP and DNS for local and container/cloud testing compatibility
    SANS="URI:spiffe://zetashield.local/ns/default/sa/${SERVICE},DNS:localhost,DNS:zeta-gateway,DNS:gateway,IP:127.0.0.1"
    if [ -n "$ZS_EXTRA_SANS" ]; then
        SANS="${SANS},${ZS_EXTRA_SANS}"
    fi
    echo "subjectAltName=${SANS}" > san.cnf
else
    # Standard services only need the SPIFFE URI
    SANS="URI:spiffe://zetashield.local/ns/default/sa/${SERVICE}"
    if [ -n "$ZS_EXTRA_SANS" ]; then
        SANS="${SANS},${ZS_EXTRA_SANS}"
    fi
    echo "subjectAltName=${SANS}" > san.cnf
fi

# CSR generation does NOT use -config here, only -subj
openssl req -new -key ${SERVICE}-key.pem -out ${SERVICE}.csr -subj "/CN=${SERVICE}"

echo "Signing certificate with ZetaShield CA..."
# The -extfile flag correctly applies the SAN to the signed certificate
openssl x509 -req -in ${SERVICE}.csr -CA ca.pem -CAkey ca-key.pem -CAcreateserial \
  -out ${SERVICE}.pem -days ${DAYS} -extfile san.cnf

echo "Cleaning up..."
rm -f ${SERVICE}.csr san.cnf

echo "✅ Certificate issued: ${SERVICE}.pem"
