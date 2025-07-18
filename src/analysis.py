import pandas as pd
from utils import *
import os

paths, config = load_config()

# Define o caminho do consolidado_geral.csv dentro da pasta data_consolidated
caminho_csv = os.path.join(paths["data_consolidated"], "consolidado_geral.csv")

# Carrega o CSV
df = pd.read_csv(caminho_csv, dtype=str)

# Garante que campos vazios fiquem como None
df = df.where(pd.notnull(df), None)

# Total de linhas
total_linhas = len(df)

# Linhas com ambos preenchidos
ambos_preenchidos = df[df['CNPJ_Fundo'].notna() & df['CNPJ_Fundo_Classe'].notna()]

# Linhas com apenas CNPJ_Fundo
so_cnpj_fundo = df[df['CNPJ_Fundo'].notna() & df['CNPJ_Fundo_Classe'].isna()]

# Linhas com apenas CNPJ_Fundo_Classe
so_cnpj_classe = df[df['CNPJ_Fundo'].isna() & df['CNPJ_Fundo_Classe'].notna()]

# CNPJs únicos em cada
cnpjs_fundo = set(so_cnpj_fundo['CNPJ_Fundo'].dropna().unique())
cnpjs_classe = set(so_cnpj_classe['CNPJ_Fundo_Classe'].dropna().unique())

# Diferenças entre os conjuntos
so_no_fundo = cnpjs_fundo - cnpjs_classe
so_na_classe = cnpjs_classe - cnpjs_fundo
intersecao = cnpjs_fundo & cnpjs_classe

# Resultado
print("Total de linhas:", total_linhas)
print("Linhas com CNPJ_Fundo apenas:", len(so_cnpj_fundo))
print("Linhas com CNPJ_Fundo_Classe apenas:", len(so_cnpj_classe))
print("Linhas com ambos preenchidos:", len(ambos_preenchidos))
print("CNPJs só no CNPJ_Fundo:", len(so_no_fundo))
print("CNPJs só no CNPJ_Fundo_Classe:", len(so_na_classe))
print("CNPJs presentes em ambos:", len(intersecao))
