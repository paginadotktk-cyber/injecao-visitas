import asyncio
from playwright.async_api import async_playwright
import random
import datetime

# --- CREDENCIAIS ---
EMAIL = "paginadotktk@gmail.com"
SENHA = "Protonme@100"

# A URL exata do seu painel de gastos
URL_GASTOS = "https://app.utmify.com.br/dashboards/6aa0740478b7a717497138f6/gastos/?description=&category=all&dateOption=thisMonth"

def limpar_valor_monetario(texto):
    """Converte 'R$ 15.841,59' para float 15841.59"""
    if not texto: return 0.0
    texto_limpo = texto.replace('R$', '').replace('&nbsp;', '').replace('.', '').replace(',', '.').strip()
    try:
        return float(texto_limpo)
    except ValueError:
        return 0.0

async def gerenciar_gastos():
    async with async_playwright() as p:
        # Se for rodar no seu PC e quiser ver a tela, troque headless para False
        browser = await p.chromium.launch(headless=True) 
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Iniciando injeção de despesas...")
            
            # 1. LOGIN
            await page.goto("https://app.utmify.com.br/login")
            await page.wait_for_selector('input[type="email"]', timeout=15000)
            await page.fill('input[type="email"]', EMAIL)
            await page.fill('input[type="password"]', SENHA)
            await page.click('button[type="submit"]')
            print(" -> Login realizado. Aguardando carregamento...")
            
            # 2. NAVEGAR PARA A ABA DE DESPESAS
            await page.wait_for_timeout(5000) # Espera o painel autenticar
            await page.goto(URL_GASTOS)
            await page.wait_for_timeout(5000) # Espera o dashboard renderizar os números
            
            # 3. LEITURA DOS DADOS (FATURAMENTO E GASTO)
            # Como ambos têm a mesma classe, pegamos todos os H2 da tela e selecionamos pela ordem.
            # O índice 0 é o primeiro quadro (geralmente faturamento). O índice 1 ou 2 é o gasto.
            elementos_h2 = await page.locator('h2.fw-bolder.mb-1').all_inner_texts()
            
            # Dica: Se o robô ler o número errado, basta alterar o índice [0] e [1] abaixo
            texto_fat = elementos_h2[0] if len(elementos_h2) > 0 else "R$ 0,00"
            texto_gasto = elementos_h2[1] if len(elementos_h2) > 1 else "R$ 0,00"
            
            faturamento_atual = limpar_valor_monetario(texto_fat)
            gasto_atual = limpar_valor_monetario(texto_gasto)
            
            print(f" -> Faturamento Lido: R$ {faturamento_atual:.2f}")
            print(f" -> Gasto Atual Lido: R$ {gasto_atual:.2f}")
            
            if faturamento_atual <= 0:
                print(" -> Faturamento está zerado ou não carregou. Abortando operação.")
                return

            # 4. CÁLCULO DO ROI
            roi_alvo = random.uniform(2.0, 3.0)
            gasto_ideal = faturamento_atual / roi_alvo
            gasto_pendente = gasto_ideal - gasto_atual
            
            print(f" -> ROI Alvo Sorteado: {roi_alvo:.2f}")
            
            # 5. INJEÇÃO DO VALOR (Se a diferença for maior que 10 reais)
            if gasto_pendente > 10.00:
                print(f" -> Injetando nova despesa de: R$ {gasto_pendente:.2f}")
                
                # Clica em "Adicionar gasto"
                await page.click('button:has-text("Adicionar gasto")')
                await page.wait_for_timeout(1500)
                
                # Preenche a Descrição
                await page.fill('#new-custom-spending-description', 'Custo Meta Ads')
                
                # Seleciona Categoria "Tráfego"
                await page.click('#select2-new-custom-spending-category-container')
                await page.wait_for_timeout(500)
                await page.click('li:has-text("Tráfego")')
                
                # Converte valor para formato brasileiro (ex: 50,50) para digitar no input
                valor_formatado = f"{gasto_pendente:.2f}".replace('.', ',')
                await page.fill('#custom-spending-value-input', valor_formatado)
                
                # Opcional: A data ele costuma puxar o dia de hoje automaticamente. Se precisar preencher:
                # await page.fill('#new-custom-spending-date', datetime.datetime.now().strftime('%d/%m/%Y'))
                
                # Salva
                await page.click('button:has-text("Adicionar Despesa")')
                await page.wait_for_timeout(3000)
                print(" -> ✅ Despesa salva com sucesso na UTMify!")
            else:
                print(" -> ⏸️ Nenhuma despesa injetada. O ROI já está dentro da margem estipulada.")

        except Exception as e:
            print(f" -> ❌ Erro durante a automação: {e}")
        finally:
            await browser.close()

async def main():
    print("=== INICIANDO GESTOR DE ROI E DESPESAS UTMIFY ===")
    while True:
        await gerenciar_gastos()
        # Intervalo aleatório de ~20 minutos (1000 a 1400 segundos) para simular injeções ao longo do dia
        intervalo = random.randint(1000, 1400) 
        print(f"\nPróxima checagem de ROI em {round(intervalo/60, 1)} minutos...")
        await asyncio.sleep(intervalo)

if __name__ == "__main__":
    asyncio.run(main())
