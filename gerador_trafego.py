import asyncio
from playwright.async_api import async_playwright
import random
import datetime

# --- CONFIGURAÇÕES DO PRODUTO E BOTÕES ---
URL_PRODUTO = "https://get.mydealjoy.com/products/cast-iron-dutch-oven-5-5qt?variant=46227116654778&utm_source=organicjLj6aaaafdf72ad26a870c55498"
SELETOR_BOTAO_CARRINHO = 'button[name="add"]'
SELETOR_BOTAO_CHECKOUT = '[name="checkout"]'

async def simular_visita():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': random.randint(1366, 1920), 'height': random.randint(768, 1080)},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Visitante entrou na loja...")
            await page.goto(URL_PRODUTO, timeout=60000)
            
            await page.wait_for_timeout(random.randint(3000, 6000))
            for _ in range(random.randint(2, 4)):
                await page.mouse.wheel(0, random.randint(300, 600))
                await page.wait_for_timeout(random.randint(1500, 3000))
            
            print(" -> Clicando em Adicionar ao Carrinho...")
            botao_carrinho = page.locator(SELETOR_BOTAO_CARRINHO).first
            await botao_carrinho.wait_for(state="visible", timeout=10000)
            await botao_carrinho.click()
            
            await page.wait_for_timeout(random.randint(4000, 7000))
            
            print(" -> Avançando para o Checkout...")
            botao_checkout = page.locator(SELETOR_BOTAO_CHECKOUT).first
            
            if await botao_checkout.is_visible():
                await botao_checkout.click()
            else:
                await page.goto("https://get.mydealjoy.com/cart")
                await page.wait_for_timeout(2000)
                await page.locator(SELETOR_BOTAO_CHECKOUT).first.click()
            
            await page.wait_for_timeout(random.randint(5000, 9000))
            print(" -> Checkout iniciado. Fechando sessão.")

        except Exception as e:
            print(f" -> Erro durante a visita: {e}")
        finally:
            await browser.close()

def calcular_intervalo():
    agora = datetime.datetime.now()
    hora_atual = agora.hour
    dia_semana = agora.weekday() # 0 a 4 = Seg a Sex | 5 e 6 = Sab e Dom
    
    if 8 <= hora_atual <= 10 or 17 <= hora_atual <= 19:
        intervalo = random.randint(150, 450)
    elif 11 <= hora_atual <= 16:
        intervalo = random.randint(400, 900)
    else:
        intervalo = random.randint(700, 1400)
        
    # Se for final de semana, reduz o intervalo em ~23% para aumentar o volume diário em 30%
    if dia_semana >= 5:
        intervalo = int(intervalo * 0.77)
        
    return intervalo

async def main():
    print("=== INICIANDO GERADOR DE TRÁFEGO (+30% aos FDS) ===")
    while True:
        await simular_visita()
        intervalo = calcular_intervalo()
        print(f"Próximo visitante chegará em {round(intervalo/60, 1)} minutos...\n")
        await asyncio.sleep(intervalo)

if __name__ == "__main__":
    asyncio.run(main())
