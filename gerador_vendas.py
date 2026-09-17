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

# ==========================================
# BLOCO DE AUTENTICAÇÃO
# ==========================================
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

# ==========================================
# GERAÇÃO DE PERFIL AMERICANO COM ZIP VALIDADO
# ==========================================
def gerar_perfil_americano():
    # Lista de combinações Cidade/Estado/CEP reais para evitar bloqueio de fraude na Shopify
    locais_validos = [
        {"city": "New York", "province": "New York", "zip": "10001"},
        {"city": "Los Angeles", "province": "California", "zip": "90001"},
        {"city": "Chicago", "province": "Illinois", "zip": "60601"},
        {"city": "Houston", "province": "Texas", "zip": "77001"},
        {"city": "Miami", "province": "Florida", "zip": "33101"},
        {"city": "Atlanta", "province": "Georgia", "zip": "30301"},
        {"city": "Seattle", "province": "Washington", "zip": "98101"},
        {"city": "Denver", "province": "Colorado", "zip": "80201"},
        {"city": "Boston", "province": "Massachusetts", "zip": "02108"},
        {"city": "Las Vegas", "province": "Nevada", "zip": "89101"},
        {"city": "Orlando", "province": "Florida", "zip": "32801"},
        {"city": "Dallas", "province": "Texas", "zip": "75201"},
        {"city": "Phoenix", "province": "Arizona", "zip": "85001"},
        {"city": "San Francisco", "province": "California", "zip": "94101"},
        {"city": "Philadelphia", "province": "Pennsylvania", "zip": "19102"}
    ]

    try:
        # Puxa APENAS o nome e sobrenome da API para manter o realismo humano
        req = Request("https://randomuser.me/api/?nat=us", headers={'User-Agent': 'Mozilla/5.0'})
        with urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            user = data['results'][0]
            
            primeiro_nome = user['name']['first']
            sobrenome = user['name']['last']
            
            dominios = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "icloud.com"]
            email = f"{primeiro_nome.lower()}.{sobrenome.lower()}{random.randint(10,999)}@{random.choice(dominios)}"
            
            # Sorteia um local 100% validado
            local = random.choice(locais_validos)
            
            # Gera um nome de rua aleatório
            ruas = ["Main St", "Oak St", "Pine St", "Maple Ave", "Cedar Ln", "Washington St", "Park Ave", "Lakeview Dr"]
            endereco = f"{random.randint(100, 9999)} {random.choice(ruas)}"
            
            telefone = f"+1{random.randint(200,999)}{random.randint(200,999)}{random.randint(1000,9999)}"
            
            # IP realista de provedores americanos
            blocos_ip_eua = ['104', '107', '198', '64', '69', '50', '72', '73', '172']
            ip_eua = f"{random.choice(blocos_ip_eua)}.{random.randint(10,250)}.{random.randint(10,250)}.{random.randint(10,250)}"
            
            return {
                "first_name": primeiro_nome,
                "last_name": sobrenome,
                "email": email,
                "address1": endereco,
                "city": local["city"],
                "province": local["province"],
                "zip": local["zip"],
                "phone": telefone,
                "ip": ip_eua
            }
    except Exception as e:
        print(f"Aviso: Usando fallback de dados ({e})")
        local = random.choice(locais_validos)
        n = random.randint(10000, 99999)
        return {
            "first_name": "James", "last_name": "Walker", "email": f"james.walker{n}@gmail.com",
            "address1": f"{random.randint(100, 999)} Main Street", "city": local["city"], 
            "province": local["province"], "zip": local["zip"], "phone": "+12125550199", "ip": "104.12.5.5"
        }

# ==========================================
# CRIAÇÃO REST DA VENDA
# ==========================================
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
    amount = DOUBLE_AMOUNT if random.random() < 0.2 else BASE_AMOUNT
    perfil = gerar_perfil_americano()
    
    payload = {
        "order": {
            "email": perfil["email"],
            "financial_status": "paid",
            "browser_ip": perfil["ip"], 
            "line_items": [{"title": "Cast Iron Dutch Oven 5.5Qt", "quantity": 1, "price": amount, "requires_shipping": True}],
            "transactions": [{"kind": "sale", "status": "success", "amount": amount}],
            "customer": {
                "first_name": perfil["first_name"], 
                "last_name": perfil["last_name"], 
                "email": perfil["email"],
                "phone": perfil["phone"]
            },
            "shipping_address": {
                "first_name": perfil["first_name"], 
                "last_name": perfil["last_name"], 
                "address1": perfil["address1"], 
                "city": perfil["city"], 
                "province": perfil["province"], 
                "country": "US", 
                "zip": perfil["zip"], 
                "phone": perfil["phone"]
            }
        }
    }
    result = rest_request(access_token, "orders.json", payload)
    if result and "order" in result:
        order = result["order"]
        nome_completo = f"{perfil['first_name']} {perfil['last_name']}"
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Venda US gerada! | Cliente: {nome_completo} ({perfil['province']} - {perfil['zip']}) | Total: ${order.get('total_price')}")

# ==========================================
# CÁLCULO DE INTERVALO
# ==========================================
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

    if dia_semana >= 5:
        intervalo = int(intervalo * 0.77)

    return intervalo

def main():
    print("=== INICIANDO GERADOR DE VENDAS US (CEP VALIDADO) ===")
    access_token = get_or_create_offline_token()
    
    while True:
        create_paid_order(access_token)
        intervalo = calcular_intervalo_vendas()
        print(f"-> Próxima venda sairá em {round(intervalo / 60, 1)} minutos...\n")
        time.sleep(intervalo)

if __name__ == "__main__":
    main()
