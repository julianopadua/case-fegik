from utils import load_config, get_links_from_cvm, download_files, extract_zip_files, consolidate_csvs

def main():
    # Carrega paths e config
    paths, config = load_config()

    base_url = "https://dados.cvm.gov.br/dados/FII/DOC/INF_TRIMESTRAL/DADOS/"

    # 1) coleta todos os .zip disponíveis
    links = get_links_from_cvm(base_url)

    # 2) baixa para data/raw e atualiza log de downloads
    download_files(
        links,
        save_path=paths["data_raw"],
        log_path=paths.get("log_downloads")
    )

    # 3) descompactar .zip em data/processed
    extract_zip_files(paths["data_raw"], paths["data_processed"])

    # 4) consolidar os CSVs
    consolidate_csvs(paths["data_processed"], paths["data_consolidated"], paths["log_processamento"])

if __name__ == "__main__":
    main()
