import os
import yaml
import os
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import csv
import zipfile
import pandas as pd

def load_config():
    """Carrega o config.yaml e cria os diretórios especificados se não existirem."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "..", "config.yaml")

    with open(config_path, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    # Construção de paths absolutos
    paths = {
        "script_dir": script_dir,
        "data_raw": os.path.join(script_dir, config["paths"]["data_raw"]),
        "data_processed": os.path.join(script_dir, config["paths"]["data_processed"]),
        "data_consolidated": os.path.join(script_dir, config["paths"]["data_consolidated"]),
        "src": os.path.join(script_dir, config["paths"]["src"]),
        "log": os.path.join(script_dir, config["paths"]["log"]),
        "log_downloads": os.path.join(script_dir, config["paths"]["log"], config["files"]["log_downloads"]),
        "log_processamento": os.path.join(script_dir, config["paths"]["log"], "processamento.log"),
    }

    # Criação das pastas principais se não existirem
    for key in ["data_raw", "data_processed", "data_consolidated", "src", "log"]:
        os.makedirs(paths[key], exist_ok=True)

    return paths, config


def get_links_from_cvm(base_url):
    """Coleta todos os links .zip disponíveis na página da CVM."""
    resp = requests.get(base_url)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    # Os <a> dentro do <pre> têm hrefs relativos como "inf_trimestral_fii_2016.zip"
    links = []
    for a in soup.find_all('a'):
        href = a.get('href', '')
        if href.endswith('.zip'):
            links.append(base_url + href)
    return links

def load_download_log(log_path):
    """Retorna um set de filenames já baixados (do log)."""
    if not os.path.exists(log_path):
        return set()
    with open(log_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return {row['filename'] for row in reader}

def append_to_log(log_path, filename, url):
    """Anexa uma linha ao CSV de log (filename, url)."""
    file_exists = os.path.exists(log_path)
    with open(log_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['filename', 'url'])
        if not file_exists:
            writer.writeheader()
        writer.writerow({'filename': filename, 'url': url})

def download_files(links, save_path, log_path=None):
    """Baixa arquivos .zip e registra no log para não repetir. Usa tqdm somente se houver arquivos a baixar."""
    os.makedirs(save_path, exist_ok=True)
    downloaded = set()
    if log_path:
        downloaded = load_download_log(log_path)

    # Filtra os links que ainda precisam ser baixados
    to_download = []
    for url in links:
        filename = url.rsplit("/", 1)[-1]
        dest = os.path.join(save_path, filename)
        if filename not in downloaded and not os.path.exists(dest):
            to_download.append((url, filename, dest))

    # Se não há o que baixar, retorna silenciosamente
    if not to_download:
        print("nothing to download - clear the folders data and log")
        return

    for url, filename, dest in tqdm(to_download, desc="Baixando arquivos"):
        try:
            r = requests.get(url)
            r.raise_for_status()
            with open(dest, "wb") as f:
                f.write(r.content)
            if log_path:
                append_to_log(log_path, filename, url)
        except Exception as e:
            print(f"[ERRO] ao baixar {url}: {e}")


def extract_zip_files(data_raw, data_processed, logger=print):
    """
    Extrai todos os arquivos .zip de data_raw para subpastas em data_processed.
    Cada subpasta é nomeada conforme o arquivo zip (sem .zip).
    Não re-extrai se a pasta de destino já existe e contém arquivos.
    Lida com arquivos corrompidos ou vazios de forma robusta.
    Loga o nome de cada zip extraído com sucesso.
    """
    for fname in os.listdir(data_raw):
        if not fname.lower().endswith('.zip'):
            continue
        zip_path = os.path.join(data_raw, fname)
        extract_dir = os.path.join(data_processed, os.path.splitext(fname)[0])
        # Se já extraído e não está vazio, pula
        if os.path.isdir(extract_dir) and os.listdir(extract_dir):
            continue
        os.makedirs(extract_dir, exist_ok=True)
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Testa se está vazio ou corrompido
                bad_file = zip_ref.testzip()
                if bad_file is not None:
                    logger(f"[ERRO] Arquivo corrompido em {fname}: {bad_file}")
                    continue
                if not zip_ref.namelist():
                    logger(f"[AVISO] ZIP vazio: {fname}")
                    continue
                zip_ref.extractall(extract_dir)
                logger(f"[OK] Extraído: {fname}")
        except zipfile.BadZipFile:
            logger(f"[ERRO] ZIP corrompido: {fname}")
        except Exception as e:
            logger(f"[ERRO] ao extrair {fname}: {e}")

def consolidate_csvs(data_processed, data_consolidated, log_path):
    """
    Consolida arquivos CSV de todos os anos em data/processed em arquivos únicos por tipo em data/consolidated.
    Loga todas as operações em log_path.
    """
    os.makedirs(data_consolidated, exist_ok=True)
    csv_map = {}

    # Mapeamento tipo -> lista de arquivos
    for year_folder in os.listdir(data_processed):
        year_path = os.path.join(data_processed, year_folder)
        if not os.path.isdir(year_path):
            continue
        for fname in os.listdir(year_path):
            if not fname.lower().endswith('.csv'):
                continue
            try:
                parts = fname.replace('.csv', '').split('_')
                tipo = '_'.join(parts[3:-1])  # remove prefixo e ano
                csv_map.setdefault(tipo, []).append(os.path.join(year_path, fname))
            except Exception as e:
                with open(log_path, 'a', encoding='utf-8') as log:
                    log.write(f"[ERRO] Nome inválido ignorado: {fname} ({e})\n")

    # Consolidação
    for tipo, files in csv_map.items():
        dfs = []
        for f in files:
            try:
                df = pd.read_csv(
                    f,
                    encoding='latin-1',
                    sep=';',
                    quoting=csv.QUOTE_NONE,
                    engine='python'
                )
                dfs.append(df)
            except Exception as e:
                with open(log_path, 'a', encoding='utf-8') as log:
                    log.write(f"[ERRO] ao ler {f}: {e}\n")
                continue

        if dfs:
            df_concat = pd.concat(dfs, ignore_index=True)
            outname = f"consolidado_{tipo}.csv"
            outpath = os.path.join(data_consolidated, outname)
            try:
                df_concat.to_csv(outpath, index=False, encoding='utf-8')
                with open(log_path, 'a', encoding='utf-8') as log:
                    log.write(f"[OK] Consolidado salvo: {outname}\n")
            except Exception as e:
                with open(log_path, 'a', encoding='utf-8') as log:
                    log.write(f"[ERRO] ao salvar {outname}: {e}\n")