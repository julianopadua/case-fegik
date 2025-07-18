import os
import pandas as pd
import streamlit as st
from utils import load_config

# ========================================
# CONFIGURAÇÃO GLOBAL
# ========================================
paths, config = load_config()
st.set_page_config(layout="wide", page_title="Case FEGIK Dashboard")

# ========================================
# CARREGAMENTO E TRATAMENTO
# ========================================
@st.cache_data
def load_consolidado_geral():
    """Agrupa por CNPJ_Fundo e escolhe o primeiro Nome_Fundo."""
    path = os.path.join(paths["data_consolidated"], "consolidado_geral.csv")
    df = pd.read_csv(path, dtype=str).fillna("")
    df = df[df["CNPJ_Fundo"].ne("")]
    df = (
        df.groupby("CNPJ_Fundo", as_index=False)
          .agg({"Nome_Fundo": "first"})
          .rename(columns={"CNPJ_Fundo": "CNPJ_Chave"})
    )
    return df

@st.cache_data
def load_consolidado_ativo():
    """Carrega e formata a base de ativos."""
    path = os.path.join(paths["data_consolidated"], "consolidado_ativo.csv")
    df = pd.read_csv(path, dtype=str).fillna("")
    df["Data_Referencia"] = pd.to_datetime(df["Data_Referencia"], format="%Y-%m-%d")
    df["Quantidade"]     = pd.to_numeric(df["Quantidade"], errors="coerce").fillna(0)
    df["Valor"]          = pd.to_numeric(df["Valor"],     errors="coerce").fillna(0)
    return df

# ========================================
# FUNÇÕES DE UI
# ========================================
def sidebar_selections(df_fundos, df_ativos):
    """Sidebar common: página + seleção de fundo + (condicional) tipos."""
    st.sidebar.header("🔎 Navegação e Seleção")
    page = st.sidebar.selectbox(
        "📑 Página",
        ["Visão Geral", "Portfólio de Ativos", "Portfólio de Ações", "Portfólio de Imóveis"]
    )

    # Seleção do fundo
    df_op = df_fundos.copy()
    df_op["opcao"] = df_op["CNPJ_Chave"] + " – " + df_op["Nome_Fundo"]
    selec = st.sidebar.selectbox("Fundo:", sorted(df_op["opcao"]))
    cnpj = selec.split(" – ")[0]

    tipos_sel = []
    # Só mostrando multiselect de TIPOS em Portfólio de Ativos
    if page == "Portfólio de Ativos":
        df_f = df_ativos[df_ativos["CNPJ_Fundo"] == cnpj]
        tipos = sorted(df_f["Tipo"].unique())
        tipos_sel = st.sidebar.multiselect(
            "📌 Tipos de ativos:",
            tipos,
            default=tipos
        )

    return page, cnpj, tipos_sel

def show_overview():
    st.title("📈 Dashboard Case FEGIK")
    st.markdown("""
    **Bem-vindo!**  
    Este app interativo cobre as análises do *Case FEGIK* em **várias abas**:
    - **Visão Geral**: descrição do projeto e instruções.  
    - **Portfólio de Ativos**: explore os ativos de cada fundo por tipo.  
    - **Portfólio de Ações**: (em breve) análise específica de cotas de ações.  
    - **Portfólio de Imóveis**: (em breve) análise de imóveis e vacância.  
    Selecione um *fundo* na barra lateral para começar.
    """)

def show_dashboard_header(df_fundo):
    st.title(f"📊 Análise do Fundo: {df_fundo['Nome_Fundo'].iloc[0]}")
    st.markdown("Escolha uma das abas para ver os detalhes.")

def show_portfolio_ativos(df_ativos, cnpj, tipos_sel):
    st.subheader("📊 Portfólio de Ativos por Tipo")
    if not tipos_sel:
        st.warning("Selecione pelo menos um tipo de ativo na sidebar.")
        return
    for tipo in tipos_sel:
        st.markdown(f"### 🔖 Tipo: {tipo}")
        df_tipo = df_ativos[
            (df_ativos["CNPJ_Fundo"] == cnpj) &
            (df_ativos["Tipo"]       == tipo)
        ][["Data_Referencia", "Nome_Ativo", "Quantidade", "Valor"]].sort_values("Data_Referencia")
        if df_tipo.empty:
            st.info("Sem registros para este tipo de ativo.")
        else:
            st.dataframe(df_tipo, use_container_width=True)

def show_placeholder(title):
    st.subheader(title)
    st.info("Implementação em desenvolvimento...")

# ========================================
# APP PRINCIPAL
# ========================================
def main():
    # Carrega bases
    df_fundos = load_consolidado_geral()
    df_ativos = load_consolidado_ativo()

    # Sidebar
    page, cnpj, tipos_sel = sidebar_selections(df_fundos, df_ativos)

    # Rotas das páginas
    if page == "Visão Geral":
        show_overview()
        return

    # A partir daqui, todas as outras abas exigem um fundo selecionado
    df_fundo = df_fundos[df_fundos["CNPJ_Chave"] == cnpj]
    show_dashboard_header(df_fundo)

    if page == "Portfólio de Ativos":
        show_portfolio_ativos(df_ativos, cnpj, tipos_sel)
    elif page == "Portfólio de Ações":
        show_placeholder("📈 Portfólio de Ações")
    elif page == "Portfólio de Imóveis":
        show_placeholder("🏢 Portfólio de Imóveis")

if __name__ == "__main__":
    main()
