#!/bin/bash
set -e

cd "$(dirname "$0")"

SERVICE="$1"

if [ -z "$SERVICE" ]; then
    echo "Usage: $0 <service-name>"
    exit 1
fi

openssl genrsa -out "${SERVICE}-key.pem" 2048

openssl req -new \
  -key "${SERVICE}-key.pem" \
  -out "${SERVICE}.csr" \
  -subj "/CN=${SERVICE}"

if [ "$SERVICE" = "proxy" ]; then
    echo "subjectAltName=URI:spiffe://zetashield.local/ns/default/sa/${SERVICE},IP:127.0.0.1,DNS:localhost" > san.cnf
else
    echo "subjectAltName=URI:spiffe://zetashield.local/ns/default/sa/${SERVICE}" > san.cnf
fi

openssl x509 -req \
  -in "${SERVICE}.csr" \
  -CA ca.pem \
  -CAkey ca-key.pem \
  -CAcreateserial \
  -out "${SERVICE}.pem" \
  -days 30 \
  -sha256 \
  -extfile san.cnf

echo "Issued: ${SERVICE}.pem with SAN identity"