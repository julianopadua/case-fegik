import streamlit as st
import pandas as pd
import os
from utils import load_config

# ========================================
# CONFIGURAÇÃO GLOBAL
# ========================================

paths, config = load_config()

st.set_page_config(layout="wide")  # layout mais amplo para sidebar larga

# ========================================
# FUNÇÕES
# ========================================

@st.cache_data
def load_consolidado_geral():
    caminho_csv = os.path.join(paths["data_consolidated"], "consolidado_geral.csv")
    df = pd.read_csv(caminho_csv, dtype=str)
    df = df.where(pd.notnull(df), None)
    df["CNPJ_Chave"] = df["CNPJ_Fundo"]
    df["Nome_Fundo"] = df["Nome_Fundo"]

    # Remove duplicatas para garantir unicidade
    df = df.drop_duplicates(subset=["CNPJ_Chave", "Nome_Fundo"])

    return df[df["CNPJ_Chave"].notna() & df["Nome_Fundo"].notna()]

def montar_sidebar(df_fundos):
    st.sidebar.header("🔎 Selecionar Fundo")

    # Remover duplicações nas opções
    df_opcoes = df_fundos[["CNPJ_Chave", "Nome_Fundo"]].drop_duplicates()

    # Criar opções bem formatadas
    df_opcoes["opcao"] = df_opcoes["CNPJ_Chave"] + " – " + df_opcoes["Nome_Fundo"]

    # Campo dinâmico com busca integrada
    selecao = st.sidebar.selectbox(
        "Buscar por CNPJ ou Nome:",
        sorted(df_opcoes["opcao"]),
        index=None,
        placeholder="Digite ou selecione um fundo"
    )

    # Extrair CNPJ
    cnpj = selecao.split(" – ")[0] if selecao else None
    return cnpj

def mostrar_analise_fundo(fundo_df):
    nome_fundo = fundo_df["Nome_Fundo"].iloc[0]
    st.title(f"📊 Análise do Fundo: {nome_fundo}")

    # TODO: adicionar análises solicitadas pelo case
    st.write("🔧 Aqui vão as análises financeiras, portfólio, vacância, etc.")

# ========================================
# APP PRINCIPAL
# ========================================

def main():
    df_fundos = load_consolidado_geral()
    cnpj_selecionado = montar_sidebar(df_fundos)

    if cnpj_selecionado:
        fundo_df = df_fundos[df_fundos["CNPJ_Chave"] == cnpj_selecionado]
        mostrar_analise_fundo(fundo_df)
    else:
        st.title("📈 Dashboard de Fundos Imobiliários")
        st.info("Selecione um fundo na barra lateral para iniciar a análise.")

if __name__ == "__main__":
    main()
