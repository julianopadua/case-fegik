import os
import re
import time
import requests
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

def download_documents_for_cnpj(cnpj_raw: str, download_dir: str):
    """
    Acessa o Gerenciador de Documentos CVM para o CNPJ informado,
    faz scrape da lista de documentos e baixa cada PDF, nomeando
    por <Tipo>_<YYYY-MM>.pdf, além de imprimir a tabela extraída.
    """
    # prepara CNPJ sem formatação
    cnpj_digits = re.sub(r"\D", "", cnpj_raw)
    url = (
        "https://fnet.bmfbovespa.com.br/fnet/publico/"
        f"abrirGerenciadorDocumentosCVM?cnpjFundo={cnpj_digits}"
    )

    # configura Chrome headless com download automático
    download_path = Path(download_dir) / cnpj_digits
    download_path.mkdir(parents=True, exist_ok=True)

    chrome_opts = Options()
    chrome_opts.add_argument("--headless")
    chrome_opts.add_experimental_option("prefs", {
        "download.default_directory": str(download_path),
        "download.prompt_for_download": False,
        "plugins.always_open_pdf_externally": True
    })
    driver = webdriver.Chrome(options=chrome_opts)

    try:
        driver.get(url)
        # espera a tabela aparecer
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#tblDocumentosEnviados tbody tr"))
        )
        time.sleep(1)  # garante que o JS preencheu tudo

        # parseia HTML
        soup = BeautifulSoup(driver.page_source, "html.parser")
        rows = soup.select("#tblDocumentosEnviados tbody tr")

        print(f"\n=== Documentos para {cnpj_raw} ===")
        downloaded = []

        # extrai cookies para usar em requests
        session = requests.Session()
        for ck in driver.get_cookies():
            session.cookies.set(ck['name'], ck['value'])

        for idx, row in enumerate(rows, 1):
            cols = [td.get_text(strip=True) for td in row.select("td")[:-1]]
            # colunas: Nome Fundo, Categoria, Tipo, Espécie, DataRef, DataEntrega, Status, Versão, Modalidade
            nome_fundo, categoria, tipo, especie, data_ref, data_entrega, status, versao, modalidade = cols

            # converte Data de Referência para AAAA-MM
            # supõe formato DD/MM/AAAA
            m = re.match(r"(\d{2})/(\d{2})/(\d{4})", data_ref)
            yyyy_mm = f"{m.group(3)}-{m.group(2)}" if m else data_ref.replace("/", "-")

            # encontra link(s) de download no último <td>
            action_cell = row.find_all("td")[-1]
            links = action_cell.find_all("a", href=True)

            for link in links:
                href = link["href"]
                # link pode ser relativo; torna absoluto
                download_url = requests.compat.urljoin(url, href)
                # monta nome de arquivo
                # usa <Tipo>_<YYYY-MM>_<idx>.pdf
                safe_tipo = re.sub(r"[^\w\-]", "_", tipo)
                filename = f"{safe_tipo}_{yyyy_mm}_{idx}.pdf"
                filepath = download_path / filename

                # baixa via requests usando os cookies do Selenium
                resp = session.get(download_url)
                resp.raise_for_status()
                with open(filepath, "wb") as f:
                    f.write(resp.content)
                downloaded.append(filename)

            # imprime a linha em tabela simples
            print(f"{idx:02d} | {data_ref} | {categoria} / {tipo} / {especie} -> baixou {len(links)} arquivo(s)")

        print(f"Arquivos salvos em: {download_path}")
        print("Lista de downloads:\n ", "\n  ".join(downloaded))

    finally:
        driver.quit()


if __name__ == "__main__":
    # teste para os dois CNPJs
    for c in ["01.235.622/0001-61", "00.332.266/0001-31"]:
        download_documents_for_cnpj(c, download_dir="downloads")
