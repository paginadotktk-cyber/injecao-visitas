import os
import asyncio
from playwright.async_api import async_playwright, expect
import random
import datetime
import re
from zoneinfo import ZoneInfo

# --- CREDENCIAIS (Usa Secrets do GitHub se existirem, senão usa o padrão abaixo) ---
EMAIL = os.getenv("UTMIFY_EMAIL", "shamim413@uorak.com")
SENHA = os.getenv("UTMIFY_SENHA", "Thalyta@100")

# --- PROXY OPCIONAL (Formato: "http://usuario:senha@ip:porta" ou deixe vazio) ---
PROXY_URL = os.getenv("PROXY_URL", "")

URL_RESUMO = "https://app.utmify.com.br/dashboards/6aa0740478b7a717497138f6/resumo/"
URL_GASTOS = "https://app.utmify.com.br/dashboards/6aa0740478b7a717497138f6/gastos"


def limpar_valor_monetario(texto):
    if not texto:
        return 0.0
    texto_limpo = (
        texto.replace('R$', '')
        .replace('&nbsp;', '')
        .replace('\xa0', '')
        .replace('.', '')
        .replace(',', '.')
        .strip()
    )
    try:
        return float(texto_limpo)
    except ValueError:
        return 0.0


async def gerenciar_gastos():
    async with async_playwright() as p:
        launch_options = {
            "headless": True,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        }

        if PROXY_URL:
            launch_options["proxy"] = {"server": PROXY_URL}

        browser = await p.chromium.launch(**launch_options)

        context = await browser.new_context(
            viewport={'width': 1366, 'height': 768},
            locale="pt-BR",
            timezone_id="America/Sao_Paulo",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        )

        # Remove a flag navigator.webdriver para evitar bloqueio básico de bot
        await context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        page = await context.new_page()

        try:
            print(f"\n[{datetime.datetime.now(ZoneInfo('America/Sao_Paulo')).strftime('%H:%M:%S')}] Iniciando injeção na UTMify...")

            # 1. LOGIN
            await page.goto(
                "https://app.utmify.com.br/login/",
                wait_until="domcontentloaded",
                timeout=60000,
            )

            campo_email = page.locator('input[name="email"]')
            await campo_email.wait_for(state="visible", timeout=30000)

            await campo_email.fill(EMAIL)
            await page.fill('input[name="password"]', SENHA)
            await page.keyboard.press('Enter')

            print(" -> Login digitado. Aguardando carregamento...")

            # FECHAR O LEMBRETE OPCIONAL DE ATIVAÇÃO DE 2FA
            await page.wait_for_url(
                re.compile(r"https://app\.utmify\.com\.br/(?:ativar-2fa|dashboards)(?:/|\?|$)"),
                timeout=60000,
            )
            if "/ativar-2fa" in page.url:
                botao_2fa = page.get_by_role("button", name="Pular", exact=True)
                await botao_2fa.wait_for(state="visible", timeout=30000)
                await botao_2fa.click(timeout=60000)
                await page.wait_for_url(
                    re.compile(r"https://app\.utmify\.com\.br/dashboards/"),
                    timeout=60000,
                )
                print(" -> Aviso de ativação de 2FA fechado. Painel acessado.")

            # 2. LER DADOS NA ABA RESUMO
            print(" -> Lendo faturamento na aba Resumo...")
            await page.goto(
                URL_RESUMO,
                wait_until="domcontentloaded",
                timeout=60000,
            )
            await page.locator('h2.fw-bolder.mb-1').first.wait_for(state="visible", timeout=30000)
            await page.wait_for_timeout(3000)

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
            await page.goto(
                URL_GASTOS,
                wait_until="domcontentloaded",
                timeout=60000,
            )
            await page.locator('#select2-select-data-container').wait_for(state="visible", timeout=30000)
            await page.wait_for_timeout(2000)

            # Conferir e validar os lançamentos no período correto.
            await page.locator('#select2-select-data-container').click()
            await page.get_by_role('option', name='Hoje', exact=True).click()
            await page.wait_for_url(re.compile(r'dateOption=today(?:&|$)'), timeout=30000)
            await page.wait_for_timeout(1500)

            print(" -> Preenchendo formulário...")
            await page.get_by_role('button', name='Adicionar gasto', exact=True).click()
            await page.wait_for_timeout(1500)

            await page.fill('#new-custom-spending-description', 'Custo Meta Ads')

            await page.click('#select2-new-custom-spending-category-container')
            await page.wait_for_timeout(500)
            await page.click('li:has-text("Tráfego")')

            # Seleção exata da data de hoje no Flatpickr
            data_hoje = datetime.datetime.now(ZoneInfo("America/Sao_Paulo")).date()
            meses = [
                "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
            ]
            await page.locator('#new-custom-spending-date').click()
            calendario = page.locator('.flatpickr-calendar.open')
            await expect(calendario.get_by_role('spinbutton', name='Year', exact=True)).to_have_value(str(data_hoje.year))
            await calendario.get_by_role('combobox', name='Month', exact=True).select_option(str(data_hoje.month - 1))
            dia_exato = f"{meses[data_hoje.month - 1]} {data_hoje.day}, {data_hoje.year}"
            await calendario.locator(f'.flatpickr-day[aria-label="{dia_exato}"]').click()

            data_esperada = data_hoje.strftime('%d/%m/%Y')
            await expect(page.locator('#new-custom-spending-date')).to_have_value(data_esperada)
            print(f" -> Data conferida no formulário: {data_esperada}")

            valor_formatado = f"{gasto_pendente:.2f}".replace('.', ',')
            await page.fill('#custom-spending-value-input', valor_formatado)

            valor_exibido = f"{gasto_pendente:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            await expect(page.locator('#custom-spending-value-input')).to_have_value(
                re.compile(rf"R\$\s*{re.escape(valor_exibido)}")
            )

            registros = (
                page.get_by_role('row')
                .filter(has_text=data_esperada)
                .filter(has_text='Custo Meta Ads')
                .filter(has_text=re.compile(rf"R\$\s*{re.escape(valor_exibido)}(?:\s|$)"))
            )
            quantidade_antes = await registros.count()

            print(" -> Clicando em Salvar...")
            await page.get_by_role('dialog', name='Adicionar Despesa', exact=True).get_by_role(
                'button', name='Adicionar Despesa', exact=True
            ).click()

            await expect(page.get_by_role('dialog', name='Adicionar Despesa', exact=True)).not_to_be_visible(timeout=30000)
            await expect(registros).to_have_count(quantidade_antes + 1, timeout=30000)

            print(" -> Registro apareceu na lista. Confirmando persistência...")
            await page.reload(wait_until='domcontentloaded', timeout=60000)
            await expect(registros).to_have_count(quantidade_antes + 1, timeout=30000)

            print(f" -> OK SUCESSO! Despesa de R$ {valor_exibido} registrada em {data_esperada} e confirmada após recarregar.")

        except Exception as e:
            print(f" -> ERRO: {e}")
            try:
                await page.screenshot(path="erro_utmify.png", full_page=True)
                print(" -> Screenshot salvo em erro_utmify.png")
            except Exception:
                pass
            raise
        finally:
            await browser.close()


async def main_loop():
    # 15 ciclos de 20 minutos = 300 minutos (exatas 5 horas)
    ciclos = 15
    for i in range(ciclos):
        print("\n==========================================")
        print(f"=== INICIANDO CICLO {i+1} DE {ciclos} ===")
        print("==========================================")

        await gerenciar_gastos()

        if i < ciclos - 1:
            print("\n -> Entrando em modo espera. Próxima leitura em exatos 20 minutos...")
            await asyncio.sleep(1200)

    print("\nOK Lote de 5 horas finalizado com segurança.")


if __name__ == "__main__":
    asyncio.run(main_loop())
