import os
import yaml

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
        "output": os.path.join(script_dir, config["paths"]["output"]),
        "img": os.path.join(script_dir, config["paths"]["img"]),
        "src": os.path.join(script_dir, config["paths"]["src"]),
        "log_downloads": os.path.join(script_dir, config["paths"]["data_raw"], config["files"]["log_downloads"]),
    }

    # Criação das pastas principais se não existirem
    for key in ["data_raw", "data_processed", "output", "img", "src"]:
        os.makedirs(paths[key], exist_ok=True)

    return paths, config
