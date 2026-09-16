import asyncio
from playwright.async_api import async_playwright
import random
import datetime

# --- CONFIGURAÇÕES DO PRODUTO E BOTÕES ---
URL_PRODUTO = "COLOQUE_A_URL_AQUI"
SELETOR_BOTAO_CARRINHO = "COLOQUE_O_SELETOR_AQUI" 
SELETOR_BOTAO_CHECKOUT = "COLOQUE_O_SELETOR_AQUI" 

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
            
            # 1. Leitura inicial (Simula que está vendo o produto)
            await page.wait_for_timeout(random.randint(3000, 6000))
            for _ in range(random.randint(2, 4)):
                await page.mouse.wheel(0, random.randint(300, 600))
                await page.wait_for_timeout(random.randint(1500, 3000))
            
            # 2. Clica em Adicionar ao Carrinho (100% de taxa)
            print(" -> Clicando em Adicionar ao Carrinho...")
            # IMPORTANTE: Descomente a linha abaixo quando tivermos o seletor
            # await page.locator(SELETOR_BOTAO_CARRINHO).first.click()
            await page.wait_for_timeout(random.randint(3000, 5000))
            
            # 3. Clica para ir ao Checkout (100% de taxa)
            print(" -> Avançando para o Checkout...")
            # IMPORTANTE: Descomente a linha abaixo quando tivermos o seletor
            # await page.locator(SELETOR_BOTAO_CHECKOUT).first.click()
            
            # Tempo lendo o checkout antes de abandonar a página
            await page.wait_for_timeout(random.randint(4000, 7000))
            print(" -> Checkout iniciado. Fechando sessão.")

        except Exception as e:
            print(f" -> Erro durante a visita: {e}")
        finally:
            await browser.close()

def calcular_intervalo():
    hora_atual = datetime.datetime.now().hour
    
    # As janelas de tempo são bem largas para garantir que o total de visitas 
    # varie aleatoriamente entre ~120 e ~180 por dia, tirando o padrão robótico.
    if 8 <= hora_atual <= 10 or 17 <= hora_atual <= 19:
        return random.randint(150, 450) # Picos: entre 2.5 min e 7.5 min
    elif 11 <= hora_atual <= 16:
        return random.randint(400, 900) # Tarde: entre 6.5 min e 15 min
    else:
        return random.randint(700, 1400) # Madrugada: entre 11 min e 23 min

async def main():
    print("=== INICIANDO GERADOR DE TRÁFEGO (100% Funil | Média 150/dia) ===")
    while True:
        await simular_visita()
        intervalo = calcular_intervalo()
        print(f"Próximo visitante chegará em {round(intervalo/60, 1)} minutos...\n")
        await asyncio.sleep(intervalo)

if __name__ == "__main__":
    asyncio.run(main())
