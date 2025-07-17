import os
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from utils import load_config

def get_links_from_cvm(base_url):
    """Coleta todos os links .zip disponíveis na página da CVM."""
    response = requests.get(base_url)
    if response.status_code != 200:
        raise Exception(f"Erro ao acessar {base_url}: Status {response.status_code}")

    soup = BeautifulSoup(response.text, "html.parser")
    links = [base_url + a['href'] for a in soup.find_all('a') if a['href'].endswith('.zip')]
    return links

def download_files(links, save_path, log_path=None):
    """Baixa arquivos .zip da lista de links e salva em `save_path`."""
    os.makedirs(save_path, exist_ok=True)
    for url in tqdm(links, desc="Baixando arquivos"):
        filename = url.split("/")[-1]
        filepath = os.path.join(save_path, filename)

        if os.path.exists(filepath):
            continue  # Pula se já foi baixado

        try:
            response = requests.get(url)
            with open(filepath, "wb") as f:
                f.write(response.content)
        except Exception as e:
            print(f"Erro ao baixar {url}: {e}")

def main():
    # Carregar configurações e paths
    paths, config = load_config()

    # URL base da CVM para scraping
    base_url = "https://dados.cvm.gov.br/dados/FII/DOC/INF_TRIMESTRAL/DADOS/"

    # Etapa 1: Coleta dos links disponíveis
    links = get_links_from_cvm(base_url)

    # Etapa 2: Download dos arquivos
    download_files(links, paths["data_raw"], log_path=paths["log_downloads"])

    # Etapa 3: [TODO] Extrair dados dos .zip para CSV
    # ...

    # Etapa 4: [TODO] Consolidar CSVs em um DataFrame final
    # ...

if __name__ == "__main__":
    main()
