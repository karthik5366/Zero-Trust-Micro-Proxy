import urllib.request
import urllib.error
import ssl
import sys
import os

# Ensure we are running from mock-apps/ so relative paths work
if not os.path.basename(os.getcwd()) == 'mock-apps':
    print("ERROR: Please run this script from the 'mock-apps' directory.")
    sys.exit(1)

GATEWAY_URL = "https://127.0.0.1:8443"
CERTS_DIR = "../certs"

def make_request(test_name, method, path, cert_file, key_file):
    print(f"\n[{test_name}]")
    print(f"  Request: {method} {path}")
    
    url = f"{GATEWAY_URL}{path}"
    
    try:
        # Create SSL context requiring client cert
        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=f"{CERTS_DIR}/ca.pem")
        ctx.load_cert_chain(certfile=cert_file, keyfile=key_file)
        
        # Strict hostname checking for the proxy cert
        ctx.check_hostname = True 
        ctx.verify_mode = ssl.CERT_REQUIRED

        req = urllib.request.Request(url, method=method)
        
        with urllib.request.urlopen(req, context=ctx) as response:
            status = response.status
            print(f"  Result: {status} OK")
            return status
            
    except ssl.SSLError as e:
        print(f"  Result: TLS_REJECT (Handshake Failed)")
        print(f"  Detail: {str(e).split(':')[-1].strip()}")
        return "TLS_REJECT"
        
    except urllib.error.HTTPError as e:
        if e.code == 503:
            print(f"  Result: 503 (Fail-Closed / Backend Down)")
        else:
            print(f"  Result: {e.code} {e.reason}")
        return e.code
        
    except urllib.error.URLError as e:
        # Catches connection refused (backend down) or handshake failures not caught by SSLError
        if "Connection refused" in str(e):
             print(f"  Result: 503 (Fail-Closed / Backend Down)")
             return 503
        print(f"  Result: ERROR ({e})")
        return "ERROR"

def main():
    print("=" * 60)
    print("ZetaShield V1.0 — 7-Test Adversarial Demo Suite")
    print("=" * 60)

    # 1. Authorized Access
    make_request("TEST 1: AUTHORIZED (frontend -> orders)", 
                 "GET", "/orders/list", 
                 f"{CERTS_DIR}/frontend-service.pem", f"{CERTS_DIR}/frontend-service-key.pem")

    # 2. No Certificate (Anonymous)
    print("\n[TEST 2: NO CERTIFICATE (Anonymous)]")
    print("  Request: GET /orders/list")
    try:
        # Context with NO client cert
        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=f"{CERTS_DIR}/ca.pem")
        req = urllib.request.Request(f"{GATEWAY_URL}/orders/list")
        urllib.request.urlopen(req, context=ctx)
        print("  Result: 200 OK (FAIL - Should have been rejected)")
    except ssl.SSLError:
        print("  Result: TLS_REJECT (Handshake Failed - No Identity)")
    except urllib.error.URLError:
        print("  Result: TLS_REJECT (Connection Reset)")

    # 3. Authorized Identity, Unauthorized Path (Deny-by-Default)
    make_request("TEST 3: DENY-BY-DEFAULT (frontend -> admin)", 
                 "GET", "/admin/delete", 
                 f"{CERTS_DIR}/frontend-service.pem", f"{CERTS_DIR}/frontend-service-key.pem")

    # 4. Lateral Movement Blocked (Micro-segmentation)
    make_request("TEST 4: LATERAL MOVEMENT BLOCKED (orders -> payments)", 
                 "GET", "/payments/balance", 
                 f"{CERTS_DIR}/orders-service.pem", f"{CERTS_DIR}/orders-service-key.pem")

    # 5. Authorized Access (Own Domain)
    make_request("TEST 5: AUTHORIZED (payments -> payments)", 
                 "GET", "/payments/balance", 
                 f"{CERTS_DIR}/payments-service.pem", f"{CERTS_DIR}/payments-service-key.pem")

    # 6. FORGED CERTIFICATE (Valid SPIFFE ID, Untrusted CA)
    make_request("TEST 6: FORGED CERT (Attacker -> orders)", 
                 "GET", "/orders/list", 
                 f"{CERTS_DIR}/attacker.pem", f"{CERTS_DIR}/attacker-key.pem")

    # 7. FAIL-CLOSED (Valid Request, Dead Backend)
    make_request("TEST 7: FAIL-CLOSED (frontend -> inventory [DOWN])", 
                 "GET", "/inventory/status", 
                 f"{CERTS_DIR}/frontend-service.pem", f"{CERTS_DIR}/frontend-service-key.pem")

    print("\n" + "=" * 60)
    print("SUMMARY: Expected Sequence -> 200, TLS_REJECT, 403, 403, 200, TLS_REJECT, 503")
    print("=" * 60)

if __name__ == "__main__":
    main()