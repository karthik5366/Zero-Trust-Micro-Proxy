#!/bin/bash
set -e

cd "$(dirname "$0")"

openssl genrsa -out ca-key.pem 4096

openssl req -x509 -new -nodes \
  -key ca-key.pem \
  -sha256 \
  -days 3650 \
  -out ca.pem \
  -subj "/CN=ZetaShield Root CA"

echo "Root CA created: ca.pem"