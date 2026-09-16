import asyncio
from playwright.async_api import async_playwright
import random
import datetime

async def simular_visita():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        context = await browser.new_context(
            viewport={'width': random.randint(1366, 1920), 'height': random.randint(768, 1080)},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Acessando a loja...")
            await page.goto("https://get.mydealjoy.com/", timeout=60000)
            
            await page.wait_for_timeout(random.randint(3000, 6000))
            
            print(" -> Rolando a página para contabilizar engajamento...")
            passos_scroll = random.randint(3, 7)
            for _ in range(passos_scroll):
                scroll_y = random.randint(300, 700)
                await page.mouse.wheel(0, scroll_y)
                await page.wait_for_timeout(random.randint(1500, 4000))
                
            print(" -> Simulando clique na tela...")
            x_click = random.randint(200, 800)
            y_click = random.randint(200, 600)
            await page.mouse.click(x_click, y_click)
            
            tempo_final = random.randint(4000, 10000)
            await page.wait_for_timeout(tempo_final)
            print(" -> Sessão concluída com sucesso.")
            
        except Exception as e:
            print(f" -> Erro ao acessar a página: {e}")
        finally:
            await browser.close()

def calcular_intervalo():
    hora_atual = datetime.datetime.now().hour
    if 8 <= hora_atual <= 10:
        return random.randint(15, 35)
    elif 17 <= hora_atual <= 19:
        return random.randint(15, 35)
    elif 11 <= hora_atual <= 16:
        return random.randint(45, 80)
    else:
        return random.randint(100, 180)

async def main():
    print("=== INICIANDO GERADOR DE TRÁFEGO (1500 visitas/dia) ===")
    while True:
        await simular_visita()
        intervalo = calcular_intervalo()
        print(f"Próximo visitante chegará em {intervalo} segundos...\n")
        await asyncio.sleep(intervalo)

if __name__ == "__main__":
    asyncio.run(main())
