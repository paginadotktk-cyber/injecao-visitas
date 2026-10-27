import asyncio
from playwright.async_api import async_playwright
import random
import datetime
import argparse
import os
import re

# Configure estas credenciais nos Secrets do GitHub Actions.
EMAIL = os.environ.get("UTMIFY_EMAIL", "")
SENHA = os.environ.get("UTMIFY_PASSWORD", "")

URL_RESUMO = "https://app.utmify.com.br/dashboards/6aa0740478b7a717497138f6/resumo/"
URL_GASTOS = "https://app.utmify.com.br/dashboards/6aa0740478b7a717497138f6/gastos"

def limpar_valor_monetario(texto):
    if not texto: return 0.0
    texto_limpo = texto.replace('R$', '').replace('&nbsp;', '').replace('.', '').replace(',', '.').strip()
    try:
        return float(texto_limpo)
    except ValueError:
        return 0.0

async def aguardar_painel(page):
    """Aceita o lembrete opcional de ativacao; nao contorna desafios de 2FA."""
    await page.wait_for_url(
        re.compile(r"https://app\.utmify\.com\.br/(?:ativar-2fa|dashboards)(?:/|\?|$)"),
        timeout=60000,
    )
    if "/ativar-2fa" in page.url:
        print(" -> Lembrete de ativação de 2FA encontrado.")
        pular = page.get_by_role("button", name="Pular", exact=True)
        await pular.wait_for(state="visible", timeout=30000)
        # click aguarda automaticamente o fim da contagem regressiva e
        # o botão ficar habilitado. Não usar force=True.
        await pular.click(timeout=60000)
    await page.wait_for_url(
        re.compile(r"https://app\.utmify\.com\.br/dashboards/"),
        timeout=60000,
    )
    print(" -> Acesso ao painel confirmado.")


async def gerenciar_gastos(diagnostico=False):
    async with async_playwright() as p:
        # HEADLESS=TRUE para rodar nos servidores invisíveis do GitHub
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1366, 'height': 768},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            print(f"\n[{datetime.datetime.now().strftime('%H:%M:%S')}] Iniciando injeção na UTMify...")
            
            # 1. LOGIN
            await page.goto("https://app.utmify.com.br/login/", wait_until="domcontentloaded")
            await page.locator('input[name="email"]').fill(EMAIL)
            await page.locator('input[name="password"]').fill(SENHA)
            await page.get_by_role("button", name="Entrar", exact=True).click()
            print(" -> Login enviado. Aguardando painel ou lembrete de 2FA...")
            await aguardar_painel(page)

            if diagnostico:
                print(" -> DIAGNÓSTICO OK: login e acesso ao painel confirmados. Nenhuma despesa adicionada.")
                return

            # 2. LER DADOS NA ABA RESUMO
            print(" -> Lendo faturamento na aba Resumo...")
            await page.goto(URL_RESUMO)
            await page.wait_for_timeout(10000) 
            
            elementos_h2 = await page.locator('h2.fw-bolder.mb-1').all_inner_texts()
            
            texto_fat = elementos_h2[0] if len(elementos_h2) > 0 else "R$ 0,00"
            texto_gasto = elementos_h2[1] if len(elementos_h2) > 1 else "R$ 0,00"
            
            faturamento_atual = limpar_valor_monetario(texto_fat)
            gasto_atual = limpar_valor_monetario(texto_gasto)
            
            print(f" -> Faturamento Lido: R$ {faturamento_atual:.2f}")
            print(f" -> Gasto Atual Lido: R$ {gasto_atual:.2f}")
            
            if faturamento_atual <= 0:
                print(" -> AVISO: Faturamento zerado.")

            # 3. INTELIGÊNCIA DO ROI (Cálculo Dinâmico)
            roi_alvo = random.uniform(2.7, 3.9)
            gasto_ideal = faturamento_atual / roi_alvo
            gasto_pendente = gasto_ideal - gasto_atual
            
            print(f" -> ROI Alvo Sorteado: {roi_alvo:.2f}")
            
            # Se o faturamento NÃO subiu o suficiente, injeta entre 30 e 50 reais
            if gasto_pendente <= 30.00:
                gasto_pendente = random.uniform(30.00, 50.00)
                print(f" -> Faturamento estável. Injetando Tráfego de Manutenção: R$ {gasto_pendente:.2f}")
            else:
                print(f" -> Faturamento subiu! Injetando Custo Ideal para ROI: R$ {gasto_pendente:.2f}")

            # 4. INJEÇÃO NA ABA GASTOS
            await page.goto(URL_GASTOS)
            await page.wait_for_timeout(8000) 
            
            print(" -> Preenchendo formulário...")
            await page.locator('button', has_text="Adicionar").first.click()
            await page.wait_for_timeout(1500)
            
            await page.fill('#new-custom-spending-description', 'Custo Meta Ads')
            
            await page.click('#select2-new-custom-spending-category-container')
            await page.wait_for_timeout(500)
            await page.click('li:has-text("Tráfego")')

            await page.click('#new-custom-spending-date') 
            await page.wait_for_timeout(500) 
            await page.locator('.flatpickr-day.today').first.click() 
            await page.wait_for_timeout(500)
            
            valor_formatado = f"{gasto_pendente:.2f}".replace('.', ',')
            await page.fill('#custom-spending-value-input', valor_formatado)
            
            print(" -> Clicando em Salvar...")
            await page.locator('button', has_text="Adicionar Despesa").first.click()
            
            await page.wait_for_timeout(4000)
            print(" -> Comando de salvar enviado!")

            # 5. VALIDAÇÃO FINAL
            print(" -> Checando se a despesa foi registrada no Resumo...")
            await page.goto(URL_RESUMO)
            await page.wait_for_timeout(10000) 
            
            elementos_ver = await page.locator('h2.fw-bolder.mb-1').all_inner_texts()
            novo_gasto = limpar_valor_monetario(elementos_ver[1] if len(elementos_ver) > 1 else "R$ 0,00")
            
            if novo_gasto > gasto_atual:
                print(f" -> ✅ SUCESSO! O gasto subiu para: R$ {novo_gasto:.2f}")
            else:
                print(" -> ⚠️ AVISO: O gasto não atualizou na tela de imediato.")

        except Exception as e:
            print(f" -> ❌ Erro: {type(e).__name__}: {e}")
            print(f" -> Página no momento da falha: {page.url}")
            raise  # O GitHub Actions precisa receber uma saída de erro.
        finally:
            await browser.close()

async def main_loop(diagnostico=False):
    if not EMAIL or not SENHA:
        raise RuntimeError("Configure UTMIFY_EMAIL e UTMIFY_PASSWORD no ambiente/Secrets do GitHub.")
    if diagnostico:
        await gerenciar_gastos(diagnostico=True)
        return
    # 15 ciclos de 20 minutos = 300 minutos (exatas 5 horas)
    ciclos = 15
    for i in range(ciclos):
        print(f"\n==========================================")
        print(f"=== INICIANDO CICLO {i+1} DE {ciclos} ===")
        print(f"==========================================")
        
        # Roda a injeção
        await gerenciar_gastos()
        
        # Se não for o último ciclo, ele entra em modo soneca por 20 minutos (1200 segundos)
        if i < ciclos - 1:
            print("\n -> Entrando em modo espera. Próxima leitura em exatos 20 minutos...")
            await asyncio.sleep(1200) 
            
    print("\n✅ Lote de 5 horas finalizado com segurança para evitar ban do GitHub.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--diagnostico", action="store_true", help="Testa apenas o login, sem lançar despesas ou repetir ciclos.")
    args = parser.parse_args()
    asyncio.run(main_loop(diagnostico=args.diagnostico))
