from playwright.sync_api import sync_playwright
from urllib.parse import urljoin

def varrer_portal_ri_playwright(url_portal: str) -> list:
    """
    Motor de Web Scraping Headless Generalizado.
    Lida com portais MZ Group e customizados, adaptando-se a dropdowns ou abas.
    """
    print(f"\nIniciando robô de varredura em: {url_portal}")
    links_encontrados = []
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url_portal, wait_until="networkidle", timeout=60000)
            
            anos_alvo = ["2026", "2025", "2024"]
            
            for ano in anos_alvo:
                try:
                    if page.locator("#fano").is_visible():
                        page.locator("#fano").select_option(ano)
                        page.wait_for_timeout(1500) # Pausa para o JS atualizar a tabela
                    else:
                        botao_ano = page.get_by_text(ano, exact=True).first
                        if botao_ano.is_visible():
                            botao_ano.click(timeout=3000)
                            page.wait_for_timeout(1500)
                except Exception:
                    pass

                # Estrategia A: Buscar em linhas de tabela
                linhas = page.locator("tr").all()
                for linha in linhas:
                    texto_linha = linha.inner_text().lower()
                    if "prévia" in texto_linha or "previa" in texto_linha or "preview" in texto_linha:
                        for tag in linha.locator("a[href]").all():
                            href = tag.get_attribute("href")
                            if href and href.startswith("http"):
                                links_encontrados.append(urljoin(url_portal, href))
                
                # Estrategia B: Buscar em links soltos
                links_soltos = page.locator("a[href]").all()
                for tag in links_soltos:
                    texto_link = tag.inner_text().lower()
                    if "prévia" in texto_link or "previa" in texto_link or "preview" in texto_link:
                        href = tag.get_attribute("href")
                        if href and href.startswith("http"):
                            links_encontrados.append(urljoin(url_portal, href))
            
            browser.close()
            
        links_unicos = list(set(links_encontrados))
        print(f"Sucesso! {len(links_unicos)} links de Prévias extraídos dinamicamente.")
        return links_unicos
        
    except Exception as e:
        print(f"Erro no web scraping com Playwright para {url_portal}: {e}")
        return []
