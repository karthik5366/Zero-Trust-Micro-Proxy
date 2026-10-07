#!/bin/bash
set -e

SERVICE=$1

if [ -z "$SERVICE" ]; then
  echo "Usage: ./issue_cert.sh <service-name>"
  exit 1
fi

# Windows Git Bash path conversion fix
export MSYS_NO_PATHCONV=1

echo "Generating key for $SERVICE..."
openssl genrsa -out ${SERVICE}-key.pem 2048

echo "Creating CSR for $SERVICE..."
# Create temporary config for SAN
if [ "$SERVICE" = "proxy" ]; then
    # Proxy needs IP and DNS for local testing compatibility
    echo "subjectAltName=URI:spiffe://zetashield.local/ns/default/sa/${SERVICE},IP:127.0.0.1,DNS:localhost" > san.cnf
else
    # Standard services only need the SPIFFE URI
    echo "subjectAltName=URI:spiffe://zetashield.local/ns/default/sa/${SERVICE}" > san.cnf
fi

# CSR generation does NOT use -config here, only -subj
openssl req -new -key ${SERVICE}-key.pem -out ${SERVICE}.csr -subj "/CN=${SERVICE}"

echo "Signing certificate with ZetaShield CA..."
# The -extfile flag correctly applies the SAN to the signed certificate
openssl x509 -req -in ${SERVICE}.csr -CA ca.pem -CAkey ca-key.pem -CAcreateserial \
  -out ${SERVICE}.pem -days 30 -extfile san.cnf

echo "Cleaning up..."
rm ${SERVICE}.csr san.cnf

echo "✅ Certificate issued: ${SERVICE}.pem"