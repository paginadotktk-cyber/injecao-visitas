import hashlib
import hmac
import json
import os
import secrets
import sys
import threading
import time
import datetime
import random
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen

SHOP_DOMAIN = "ks6pbe-qg.myshopify.com"
API_VERSION = "2023-10"
CLIENT_ID = "3f70d3e1b597b2c8fa0e0abcbbbd6e57"
CLIENT_SECRET = "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"
REDIRECT_URI = "http://localhost:8000/callback"
SCOPES = "write_orders,read_products"
OUTPUT_FILE = ".shopify_offline_token.json"

BASE_AMOUNT = "79.90"
DOUBLE_AMOUNT = "159.80"

# --- BLOCO DE AUTENTICAÇÃO (MANTIDO INTACTO) ---
class CallbackHandler(BaseHTTPRequestHandler):
    server_version = "ShopifyOAuthLocal/1.0"
    def do_GET(self):
        parsed_url = urlparse(self.path)
        params = parse_qs(parsed_url.query)
        if parsed_url.path != "/callback":
            self.send_response(404)
            self.end_headers()
            return
        self.server.callback_params = params
        message = "Autorizacao recebida com sucesso! Feche esta aba." if "code" in params else "Erro na autorizacao."
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(f"<html><body><h2>{message}</h2></body></html>".encode("utf-8"))
        threading.Thread(target=self.server.shutdown, daemon=True).start()
    def log_message(self, format, *args): return

def validate_hmac(params, client_secret):
    received_hmac = params.get("hmac", [""])[0]
    if not received_hmac: return False
    pairs = [f"{k}={v}" for k in sorted(params) if k not in ("hmac", "signature") for v in params[k]]
    digest = hmac.new(client_secret.encode("utf-8"), "&".join(pairs).encode("utf-8"), hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, received_hmac)

def exchange_code_for_token(code, client_secret):
    url = f"https://{SHOP_DOMAIN}/admin/oauth/access_token"
    body = json.dumps({"client_id": CLIENT_ID, "client_secret": client_secret, "code": code, "expiring": False}).encode("utf-8")
    request = Request(url, data=body, method="POST", headers={"Content-Type": "application/json"})
    try:
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        print("Erro Shopify:", error.read().decode("utf-8"))
        sys.exit(1)

def get_or_create_offline_token():
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)
                if "access_token" in data: return data["access_token"]
        except Exception: pass
    if os.environ.get("GITHUB_ACTIONS") == "true":
        print("ERRO: Token não encontrado no GitHub Actions.")
        sys.exit(1)
    state = secrets.token_urlsafe(24)
    auth_url = (f"https://{SHOP_DOMAIN}/admin/oauth/authorize?" + urlencode({"client_id": CLIENT_ID, "scope": SCOPES, "redirect_uri": REDIRECT_URI, "state": state}))
    server = HTTPServer(("localhost", 8000), CallbackHandler)
    server.expected_state = state
    server.callback_params = None
    webbrowser.open(auth_url)
    server.serve_forever()
    params = server.callback_params or {}
    token_response = exchange_code_for_token(params["code"][0], CLIENT_SECRET)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(token_response, file, indent=2)
    return token_response.get("access_token")

# --- BLOCO DE CRIAÇÃO REST ---
def rest_request(access_token, endpoint, payload):
    url = f"https://{SHOP_DOMAIN}/admin/api/{API_VERSION}/{endpoint}"
    body = json.dumps(payload).encode("utf-8")
    request = Request(url, data=body, method="POST", headers={"Content-Type": "application/json", "X-Shopify-Access-Token": access_token})
    try:
        with urlopen(request, timeout=30) as response: return json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        print("Erro Shopify:", error.read().decode("utf-8"))
        return None

def create_paid_order(access_token):
    order_id = random.randint(10000, 99999)
    amount = DOUBLE_AMOUNT if random.random() < 0.2 else BASE_AMOUNT
    
    payload = {
        "order": {
            "email": f"cliente-{order_id}@example.com",
            "financial_status": "paid",
            "browser_ip": f"177.{random.randint(10, 200)}.{random.randint(10, 200)}.{random.randint(10, 200)}", 
            "line_items": [{"title": f"Produto Principal #{order_id}", "quantity": 1, "price": amount, "requires_shipping": True}],
            "transactions": [{"kind": "sale", "status": "success", "amount": amount}],
            "customer": {"first_name": "Cliente", "last_name": f"Teste {order_id}", "email": f"cliente-{order_id}@example.com"},
            "shipping_address": {"first_name": "Cliente", "last_name": f"Teste {order_id}", "address1": "Rua Ficticia 123", "city": "São Paulo", "province": "SP", "country": "BR", "zip": "01000-000", "phone": "+5511999999999"}
        }
    }
    result = rest_request(access_token, "orders.json", payload)
    if result and "order" in result:
        order = result["order"]
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Pedido criado! [ID: {order_id} | Total: R${order.get('total_price')}]")

# --- CÁLCULO DE INTERVALO ---
def calcular_intervalo_vendas():
    agora = datetime.datetime.now()
    hora_atual = agora.hour
    dia_semana = agora.weekday()

    if 8 <= hora_atual <= 10 or 17 <= hora_atual <= 19:
        intervalo = random.randint(800, 1200)
    elif 11 <= hora_atual <= 16:
        intervalo = random.randint(2000, 2800)
    else:
        intervalo = random.randint(5000, 6500)

    # +30% de volume aos finais de semana
    if dia_semana >= 5:
        intervalo = int(intervalo * 0.77)

    return intervalo

def main():
    print("=== INICIANDO GERADOR DE VENDAS (+30% aos FDS) ===")
    access_token = get_or_create_offline_token()
    
    while True:
        create_paid_order(access_token)
        intervalo = calcular_intervalo_vendas()
        print(f"-> Próxima venda sairá em {round(intervalo / 60, 1)} minutos...\n")
        time.sleep(intervalo)

if __name__ == "__main__":
    main()
