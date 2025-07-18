import os
import pandas as pd
import streamlit as st
from utils import load_config

# ========================================
# CONFIGURAÇÃO GLOBAL
# ========================================
paths, config = load_config()
st.set_page_config(layout="wide")

# ========================================
# CARREGAMENTO E TRATAMENTO
# ========================================
@st.cache_data
def load_consolidado_geral():
    """Agrupa por CNPJ_Fundo e escolhe o primeiro Nome_Fundo."""
    caminho = os.path.join(paths["data_consolidated"], "consolidado_geral.csv")
    df = pd.read_csv(caminho, dtype=str).fillna("")
    # chave e nome
    df = df.loc[df["CNPJ_Fundo"].ne("")]
    # agrupa por CNPJ, pega o primeiro nome
    df = (
        df.groupby("CNPJ_Fundo", as_index=False)
          .agg({"Nome_Fundo": "first"})
          .rename(columns={"CNPJ_Fundo": "CNPJ_Chave"})
    )
    return df

@st.cache_data
def load_consolidado_ativo():
    """Carrega e formata a base de ativos."""
    caminho = os.path.join(paths["data_consolidated"], "consolidado_ativo.csv")
    df = pd.read_csv(caminho, dtype=str).fillna("")
    df["Data_Referencia"] = pd.to_datetime(df["Data_Referencia"], format="%Y-%m-%d")
    df["Quantidade"] = pd.to_numeric(df["Quantidade"], errors="coerce").fillna(0)
    df["Valor"]     = pd.to_numeric(df["Valor"],     errors="coerce").fillna(0)
    return df

# ========================================
# UI: SIDEBAR
# ========================================
def sidebar_selecoes(df_fundos, df_ativos):
    st.sidebar.header("🔎 Selecione o Fundo")
    # Dropdown CNPJ – Nome (único por CNPJ)
    df_fundos["opcao"] = df_fundos["CNPJ_Chave"] + " – " + df_fundos["Nome_Fundo"]
    selecao = st.sidebar.selectbox(
        "Fundo:",
        sorted(df_fundos["opcao"]),
        placeholder="Digite ou selecione"
    )
    if not selecao:
        return None, []
    cnpj = selecao.split(" – ")[0]

    # Lista dinâmica de TIPOS de ativos desse fundo
    df_f = df_ativos[df_ativos["CNPJ_Fundo"] == cnpj]
    tipos = sorted(df_f["Tipo"].unique())
    tipos_sel = st.sidebar.multiselect(
        "📌 Tipos de ativos:",
        tipos,
        default=tipos
    )
    return cnpj, tipos_sel

# ========================================
# UI: REGIÕES PRINCIPAIS
# ========================================
def mostrar_dashboard_fundo(df_fundo):
    st.title(f"📊 Análise do Fundo: {df_fundo['Nome_Fundo'].iloc[0]}")
    st.markdown("**Seções disponíveis:**  \n"
                "- 📈 Portfólio de Ativos por Tipo  \n"
                "- 🔜 Outros indicadores em breve")

def mostrar_tabelas_por_tipo(df_ativos, cnpj, tipos_sel):
    st.subheader("📊 Portfólio de Ativos")
    for tipo in tipos_sel:
        st.markdown(f"### 🔖 Tipo: {tipo}")
        df_tipo = df_ativos[
            (df_ativos["CNPJ_Fundo"] == cnpj) &
            (df_ativos["Tipo"]       == tipo)
        ].loc[:, ["Data_Referencia", "Nome_Ativo", "Quantidade", "Valor"]]
        df_tipo = df_tipo.sort_values("Data_Referencia")
        if df_tipo.empty:
            st.info("Sem registros para este tipo de ativo.")
        else:
            st.dataframe(df_tipo, use_container_width=True)

# ========================================
# APP PRINCIPAL
# ========================================
def main():
    df_fundos = load_consolidado_geral()
    df_ativos = load_consolidado_ativo()

    cnpj, tipos_sel = sidebar_selecoes(df_fundos, df_ativos)
    if not cnpj:
        st.title("📈 Dashboard de Fundos Imobiliários")
        st.info("Selecione um fundo na barra lateral para iniciar.")
        return

    # Filtra o nome do fundo
    df_fundo = df_fundos[df_fundos["CNPJ_Chave"] == cnpj]
    mostrar_dashboard_fundo(df_fundo)
    mostrar_tabelas_por_tipo(df_ativos, cnpj, tipos_sel)

if __name__ == "__main__":
    main()
