import os
import pandas as pd
import streamlit as st
import plotly.express as px
from utils import load_config
import io
import zipfile
import requests
import re
from bs4 import BeautifulSoup
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC



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
    path = os.path.join(paths["data_consolidated"], "consolidado_ativo.csv")
    df = pd.read_csv(path, dtype=str).fillna("")
    df["Data_Referencia"] = pd.to_datetime(df["Data_Referencia"], format="%Y-%m-%d", errors="coerce")
    df["Quantidade"]      = pd.to_numeric(df["Quantidade"], errors="coerce").fillna(0)
    df["Valor"]           = pd.to_numeric(df["Valor"],     errors="coerce").fillna(0)
    return df

@st.cache_data
def load_consolidado_imovel():
    path = os.path.join(paths["data_consolidated"], "consolidado_imovel.csv")
    df = pd.read_csv(path, dtype=str).fillna("")
    df.columns = df.columns.str.strip().str.replace("\ufeff", "", regex=False)
    df["Data_Referencia"]         = pd.to_datetime(df["Data_Referencia"], format="%Y-%m-%d", errors="coerce")
    df["Numero_Unidades"]         = pd.to_numeric(df["Numero_Unidades"], errors="coerce").fillna(0)
    df["Percentual_Vacancia"]     = pd.to_numeric(df["Percentual_Vacancia"], errors="coerce").fillna(0)
    df["Percentual_Inadimplencia"]= pd.to_numeric(df["Percentual_Inadimplencia"], errors="coerce").fillna(0)
    df["Percentual_Receitas_FII"] = pd.to_numeric(df["Percentual_Receitas_FII"], errors="coerce").fillna(0)
    return df

@st.cache_data
def load_consolidado_resultado():
    path = os.path.join(paths["data_consolidated"], "consolidado_resultado_contabil_financeiro.csv")
    df = pd.read_csv(path, dtype=str).fillna("")
    df.columns = df.columns.str.strip().str.replace("\ufeff", "", regex=False)
    df["Data_Referencia"] = pd.to_datetime(df["Data_Referencia"], format="%Y-%m-%d", errors="coerce")
    # converter todas as colunas numéricas, exceto identificadores
    non_num = {"Data_Referencia", "CNPJ_Fundo", "CNPJ_Fundo_Classe"}
    for col in df.columns:
        if col not in non_num:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df

@st.cache_data
def load_consolidado_rentabilidade():
    path = os.path.join(paths["data_consolidated"], "consolidado_rentabilidade_efetiva.csv")
    df = pd.read_csv(path, dtype=str).fillna("")
    df.columns = df.columns.str.strip().str.replace("\ufeff", "", regex=False)
    df["Data_Referencia"] = pd.to_datetime(df["Data_Referencia"], format="%Y-%m-%d", errors="coerce")

    # converter ambos os % em numérico
    df["Percentual_Rentabilidade_Efetiva_Mes"] = pd.to_numeric(
        df["Percentual_Rentabilidade_Efetiva_Mes"],
        errors="coerce"
    ).fillna(0)

    df["Percentual_Rentabilidade_Auferida_Ausencia_Garantia"] = pd.to_numeric(
        df.get("Percentual_Rentabilidade_Auferida_Ausencia_Garantia", []),
        errors="coerce"
    ).fillna(0)

    return df

@st.cache_data
def load_consolidado_geral_completo():
    path = os.path.join(paths["data_consolidated"], "consolidado_geral.csv")
    df = pd.read_csv(path, dtype=str).fillna("")
    df.columns = df.columns.str.strip().str.replace("\ufeff", "", regex=False)
    df["Data_Referencia"] = pd.to_datetime(
        df["Data_Referencia"], format="%Y-%m-%d", errors="coerce"
    )
    return df


def get_documents_zip(cnpj_raw: str) -> bytes:
    """Retorna um ZIP em bytes contendo todos os PDFs do gerenciador da B3 para o CNPJ."""
    # prepara CNPJ sem formatação
    cnpj_digits = re.sub(r"\D", "", cnpj_raw)
    base_url = (
        "https://fnet.bmfbovespa.com.br/fnet/publico/"
        f"abrirGerenciadorDocumentosCVM?cnpjFundo={cnpj_digits}"
    )

    # configura Selenium + Chrome headless
    chrome_opts = Options()
    chrome_opts.add_argument("--headless")
    chrome_opts.add_argument("--no-sandbox")
    chrome_opts.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=chrome_opts)

    try:
        driver.get(base_url)
        # espera a tabela carregar
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#tblDocumentosEnviados tbody tr"))
        )
        time.sleep(1)  # dá um segundo pro JS preencher tudo

        # extrai cookies para requests
        session = requests.Session()
        for ck in driver.get_cookies():
            session.cookies.set(ck["name"], ck["value"])

        # parse das linhas
        soup = BeautifulSoup(driver.page_source, "html.parser")
        rows = soup.select("#tblDocumentosEnviados tbody tr")

        # monta ZIP em memória
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for idx, row in enumerate(rows, 1):
                cols = [td.get_text(strip=True) for td in row.select("td")[:-1]]
                tipo = cols[2]
                data_ref = cols[4]
                m = re.match(r"(\d{2})/(\d{2})/(\d{4})", data_ref)
                yyyy_mm = f"{m.group(3)}-{m.group(2)}" if m else data_ref.replace("/", "-")

                for a in row.select("td")[-1].select("a[href]"):
                    href = a["href"]
                    pdf_url = requests.compat.urljoin(base_url, href)
                    r = session.get(pdf_url)
                    r.raise_for_status()
                    safe_tipo = re.sub(r"[^\w\-]", "_", tipo)
                    filename = f"{safe_tipo}_{yyyy_mm}_{idx}.pdf"
                    zf.writestr(filename, r.content)

        buf.seek(0)
        return buf.getvalue()

    finally:
        driver.quit()



# ========================================
# FUNÇÕES DE INTERFACE
# ========================================
def show_fundo_info(df_geral_completo, cnpj):
    """
    Exibe endereço, contato, administrador, e-mail, telefone do fundo
    com base no último registro de consolidação.
    """
    df = df_geral_completo[df_geral_completo["CNPJ_Fundo"] == cnpj]
    if df.empty:
        st.info("Nenhuma informação cadastral disponível.")
        return

    # pega o registro mais recente
    last = df.sort_values("Data_Referencia").iloc[-1]

    st.markdown("### Dados Cadastrais do Fundo")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Administrador:** {last['Nome_Administrador']}  ")
        st.markdown(f"**CNPJ Admin.:** {last['CNPJ_Administrador']}  ")
        st.markdown(f"**Endereço:** {last['Logradouro']}, {last['Numero']} {last['Complemento']}  ")
        st.markdown(f"**Bairro / Cidade:** {last['Bairro']} / {last['Cidade']}–{last['Estado']}  ")
        st.markdown(f"**CEP:** {last['CEP']}  ")
    with col2:
        telefones = "\n".join(filter(None, [last.get(f"Telefone{i}") for i in (1,2,3)]))
        st.markdown(f"**Telefone(s):**  \n{telefones}  ")
        st.markdown(f"**E-mail:** {last['Email']}  ")
        st.markdown(f"**Site:** {last['Site']}  ")
        st.markdown(f"**Público-Alvo:** {last['Publico_Alvo']}  ")
        st.markdown(f"**Gestão:** {last['Tipo_Gestao']}  ")

def sidebar_selections(df_fundos, df_ativos):
    st.sidebar.header("Navegação e Seleção")
    page = st.sidebar.selectbox(
        "Página",
     ["Visão Geral", "Portfólio de Ativos", "Portfólio de Imóveis",
     "Análise Financeira", "Análise Qualitativa", "Informações Adicionais"]
    )


    # seleção global de fundo
    df_op = df_fundos.copy()
    df_op["opcao"] = df_op["CNPJ_Chave"] + " – " + df_op["Nome_Fundo"]
    opcoes = [""] + sorted(df_op["opcao"])
    selec = st.sidebar.selectbox("Fundo:", opcoes, format_func=lambda x: "Selecione um fundo…" if x=="" else x)
    cnpj = None if selec=="" else selec.split(" – ")[0]


    tipos_sel = []
    if page == "Portfólio de Ativos":
        df_f = df_ativos[df_ativos["CNPJ_Fundo"] == cnpj]
        tipos = sorted(df_f["Tipo"].unique())
        tipos_sel = st.sidebar.multiselect("Tipos de ativos:", tipos, default=tipos)

    return page, cnpj, tipos_sel

def show_overview(df_geral_compl, cnpj):
    st.title("Dashboard Case FEGIK")
    st.markdown("## Visão Geral do Fundo")
    show_fundo_info(df_geral_compl, cnpj)
    st.markdown("""
Este aplicativo interativo cobre as análises do Case FEGIK em várias abas:

- **Visão Geral**: instruções e descrição do projeto.
- **Portfólio de Ativos**: detalhes de cada tipo de ativo.
- **Portfólio de Imóveis**: evolução e quantidade de imóveis para venda.
- **Análise Financeira**: receitas, custos, vacância, inadimplência e rentabilidade.
""")
    st.markdown(
    """
    ---
    **Sobre o desenvolvedor**  
    • Juliano E. S. Pádua – [LinkedIn](https://www.linkedin.com/in/julianopadua)  
    • Repositório: https://github.com/julianopadua/case-fegik# 
    • Email: julianofpadua@gmail.com  
    """
    )


def show_dashboard_header(df_fundo):
    st.title(f"Análise do Fundo: {df_fundo['Nome_Fundo'].iloc[0]}")

def show_portfolio_ativos(df_ativos, cnpj, tipos_sel):
    st.subheader("Portfólio de Ativos por Tipo")
    if not tipos_sel:
        st.warning("Selecione pelo menos um tipo de ativo.")
        return

    for tipo in tipos_sel:
        df_tipo = (
            df_ativos.loc[
                (df_ativos["CNPJ_Fundo"] == cnpj) &
                (df_ativos["Tipo"]       == tipo),
                ["Data_Referencia", "Quantidade", "Valor"]
            ]
            .sort_values("Data_Referencia")
            .copy()
        )
        if df_tipo.empty:
            st.info(f"Sem registros para o tipo: {tipo}")
            continue

        df_tipo["Data_Referencia"] = df_tipo["Data_Referencia"].dt.strftime("%Y-%m-%d")
        ts = df_tipo.groupby("Data_Referencia")["Valor"].sum().sort_index()

        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"**{tipo}** — Detalhamento")
            st.dataframe(df_tipo, use_container_width=True)
        with col2:
            st.markdown(f"**{tipo}** — Valor Investido")
            st.line_chart(ts)
        st.markdown("---")

def show_portfolio_imoveis(df_imovel, cnpj):
    st.subheader("Portfólio de Imóveis")
    classes_disponiveis = sorted(df_imovel["Classe"].dropna().unique())
    padrao = [c for c in ["Imóveis para venda acabados", "Imóveis para venda em construção"]
              if c in classes_disponiveis]
    classes_selecionadas = st.multiselect(
        "Selecione as classes de imóvel:",
        options=classes_disponiveis,
        default=padrao
    )

    df_sel = df_imovel.loc[
        (df_imovel["CNPJ_Fundo"] == cnpj) &
        (df_imovel["Classe"].isin(classes_selecionadas))
    ].copy()
    if df_sel.empty:
        st.info("Nenhum imóvel encontrado para as classes selecionadas.")
        return

    df_sel["Data_Referencia"] = df_sel["Data_Referencia"].dt.strftime("%Y-%m-%d")
    df_sel["Numero_Unidades"] = pd.to_numeric(df_sel["Numero_Unidades"], errors="coerce").fillna(0)
    df_sel["Area"]            = pd.to_numeric(df_sel["Area"], errors="coerce").fillna(0)

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("#### Detalhamento de Unidades")
        st.dataframe(
            df_sel[["Data_Referencia", "Classe", "Nome_Imovel", "Endereco",
                    "Numero_Unidades", "Area"]],
            use_container_width=True
        )
    with col2:
        st.markdown("#### Evolução do Número de Unidades")
        ts_unidades = df_sel.groupby("Data_Referencia")["Numero_Unidades"].sum().sort_index()
        st.line_chart(ts_unidades)
    st.markdown("---")

    col3, col4 = st.columns([2, 1])
    with col3:
        st.markdown("#### Indicadores Operacionais")
        st.dataframe(
            df_sel[["Data_Referencia",
                    "Outras_Caracteristicas_Relevantes",
                    "Percentual_Vacancia",
                    "Percentual_Inadimplencia",
                    "Percentual_Receitas_FII"]],
            use_container_width=True
        )
    with col4:
        st.markdown("#### Evolução da Vacância, Inadimplência e Receitas FII")
        ts_stats = (
            df_sel
            .groupby("Data_Referencia")[[

                "Percentual_Vacancia",
                "Percentual_Inadimplencia",
                "Percentual_Receitas_FII"
            ]]
            .mean().sort_index()
            .rename(columns={
                "Percentual_Vacancia": "Vacância",
                "Percentual_Inadimplencia": "Inadimplência",
                "Percentual_Receitas_FII": "Receitas FII"
            })
        )
        st.line_chart(ts_stats)
    st.markdown("---")

def show_analise_financeira(df_fundos, df_res, df_rent, df_imovel, primary_cnpj):
    st.subheader("Análise Financeira e Contábil")

    # 0) Seleção de fundos para comparação
    df_op = df_fundos.copy()
    df_op["opcao"] = df_op["CNPJ_Chave"] + " – " + df_op["Nome_Fundo"]
    default = df_op.loc[df_op["CNPJ_Chave"] == primary_cnpj, "opcao"].iloc[0]
    escolhas = st.multiselect(
        "Selecione fundos para comparação:",
        options=sorted(df_op["opcao"]),
        default=[default]
    )
    cnpjs = [e.split(" – ")[0] for e in escolhas]

    mostrar_media = st.checkbox("Incluir média entre fundos", value=True)

    # 1) Indicadores Principais
    princ_cols = [
        "Resultado_Trimestral_Liquido_Contabil",
        "Resultado_Trimestral_Liquido_Financeiro",
        "Rendimentos_Declarados",
        "Lucro_Contabil",
        "Rendimento_Liquido_Pagar",
        "Parcela_Rendimento_Retido",
        "Percentual_Resultado_Financeiro_Liquido_Declarado"
    ]
    df_princ = df_res[df_res["CNPJ_Fundo"].isin(cnpjs)].copy()
    if not df_princ.empty:
        st.markdown("### Indicadores Principais — Tabela Trimestral")
        df_p = (
            df_princ
            .groupby(["Data_Referencia", "CNPJ_Fundo"], as_index=False)
            .agg({col: "sum" for col in princ_cols})
        )
        df_p["Data_Referencia"] = pd.to_datetime(df_p["Data_Referencia"]).dt.strftime("%Y-%m-%d")
        st.dataframe(df_p, use_container_width=True)

        st.markdown("### Indicadores Principais — Gráficos")
        labels_princ = {
            "Resultado Líquido Contábil":  "Resultado_Trimestral_Liquido_Contabil",
            "Resultado Líquido Financeiro":"Resultado_Trimestral_Liquido_Financeiro",
            "Rendimentos Declarados":      "Rendimentos_Declarados",
            "Lucro Contábil":              "Lucro_Contabil",
            "Rendimento Líquido a Pagar":  "Rendimento_Liquido_Pagar",
            "Parcela de Rendimento Retido":"Parcela_Rendimento_Retido",
            "% Resultado Financeiro Líquido Declarado":"Percentual_Resultado_Financeiro_Liquido_Declarado"
        }
        for label, col in labels_princ.items():
            st.markdown(f"**{label}**")
            pivot = df_p.pivot(
                index="Data_Referencia",
                columns="CNPJ_Fundo",
                values=col
            ).sort_index()
            if mostrar_media:
                pivot["Média"] = pivot.mean(axis=1)
            st.line_chart(pivot)
        st.markdown("---")

    # 2) Receitas Geradas
    st.markdown("### Receitas Geradas")
    receita_cols = [
        "Receita_Aluguel_Investimento_Contabil",
        "Receita_Venda_Investimento_Contabil",
        "Receita_Juros_TVM_Contabil",
        "Receita_Juros_Aplicacao_Contabil",
        "Receita_Venda_Estoque_Contabil"
    ]
    df_rend = df_res[df_res["CNPJ_Fundo"].isin(cnpjs)].copy()
    df_rend = (
        df_rend
        .groupby(["Data_Referencia", "CNPJ_Fundo"], as_index=False)
        .agg({col: "sum" for col in receita_cols})
    )
    df_rend["Data_Referencia"] = pd.to_datetime(df_rend["Data_Referencia"]).dt.strftime("%Y-%m-%d")
    for col in receita_cols:
        pivot = df_rend.pivot(
            index="Data_Referencia",
            columns="CNPJ_Fundo",
            values=col
        ).sort_index()
        # se todos valores forem zero ou NaN, pula
        if pivot.fillna(0).abs().sum().sum() == 0:
            continue
        label = col.replace("_Contabil", "").replace("_", " ").capitalize()
        st.markdown(f"**{label}**")
        if mostrar_media:
            pivot["Média"] = pivot.mean(axis=1)
        st.line_chart(pivot)
    st.markdown("---")


    # 3) Rentabilidade Efetiva x Ausência de Garantia
    st.markdown("### Rentabilidade Efetiva x Ausência de Garantia")
    df_r = df_rent[df_rent["CNPJ_Fundo"].isin(cnpjs)].copy()

    # garantir dtype numérico
    df_r["Percentual_Rentabilidade_Efetiva_Mes"] = pd.to_numeric(
        df_r["Percentual_Rentabilidade_Efetiva_Mes"], errors="coerce"
    ).fillna(0)
    df_r["Percentual_Rentabilidade_Auferida_Ausencia_Garantia"] = pd.to_numeric(
        df_r["Percentual_Rentabilidade_Auferida_Ausencia_Garantia"], errors="coerce"
    ).fillna(0)

    df_r = (
        df_r
        .groupby(["Data_Referencia", "CNPJ_Fundo"], as_index=False)
        .agg({
            "Percentual_Rentabilidade_Efetiva_Mes": "mean",
            "Percentual_Rentabilidade_Auferida_Ausencia_Garantia": "mean"
        })
    )
    df_r["Data_Referencia"] = pd.to_datetime(df_r["Data_Referencia"]).dt.strftime("%Y-%m-%d")

    metrics = {
        "Percentual_Rentabilidade_Efetiva_Mes": "Rentabilidade Efetiva",
        "Percentual_Rentabilidade_Auferida_Ausencia_Garantia": "Rentabilidade sem Garantia"
    }
    for metric, label in metrics.items():
        pivot = df_r.pivot(
            index="Data_Referencia",
            columns="CNPJ_Fundo",
            values=metric
        ).sort_index()
        # se todos valores forem zero ou NaN, pula
        if pivot.fillna(0).abs().sum().sum() == 0:
            continue
        st.markdown(f"**{label}**")
        if mostrar_media:
            pivot["Média"] = pivot.mean(axis=1)
        st.line_chart(pivot)
    st.markdown("---")

def show_analise_qualitativa(df_fundos, df_geral, primary_cnpj):
    st.subheader("Análise Qualitativa dos Fundos")

    # 1) Seleção de fundos (só opções válidas)
    df_op = df_fundos.copy()
    df_op["opcao"] = df_op["CNPJ_Chave"] + " – " + df_op["Nome_Fundo"]
    default = df_op.loc[df_op["CNPJ_Chave"] == primary_cnpj, "opcao"].iloc[0]
    escolhas = st.multiselect(
        "Selecione fundos para análise qualitativa:",
        options=sorted(df_op["opcao"]),
        default=[default]
    )
    cnpjs = [e.split(" – ")[0] for e in escolhas]

    # 2) Último registro por fundo
    df_q = df_geral[df_geral["CNPJ_Fundo"].isin(cnpjs)].copy()
    df_q["Data_Referencia"] = pd.to_datetime(df_q["Data_Referencia"])
    df_q = (
        df_q
        .sort_values(["CNPJ_Fundo", "Data_Referencia"])
        .groupby("CNPJ_Fundo", as_index=False)
        .tail(1)
    )

    # 3) Tabela resumo
    st.markdown("### Tabela Qualitativa dos Fundos")
    cols = [
        "Nome_Fundo", "Publico_Alvo", "Segmento_Atuacao", "Mandato",
        "Tipo_Gestao", "Mercado_Negociacao_Bolsa",
        "Mercado_Negociacao_MBO", "Mercado_Negociacao_MB",
        "Fundo_Exclusivo", "Fundo_Nao_Listado_Exclusivo"
    ]
    st.dataframe(df_q.set_index("CNPJ_Fundo")[cols], use_container_width=True)

    # 4) Histograma: Público-Alvo
    st.markdown("### Distribuição por Público-Alvo")
    df_pub = df_q[["CNPJ_Fundo", "Publico_Alvo"]]
    fig1 = px.histogram(
        df_pub,
        x="Publico_Alvo",
        color="CNPJ_Fundo",
        barmode="group",
        labels={"Publico_Alvo":"Público-Alvo","CNPJ_Fundo":"Fundo","count":"Quantidade"}
    )
    st.plotly_chart(fig1, use_container_width=True)

    # 5) Histograma proporcional: Mercado de Negociação
    st.markdown("### Distribuição Proporcional por Mercado de Negociação")

    mflags = {
        "Mercado_Negociacao_Bolsa": "Bolsa",
        "Mercado_Negociacao_MBO":   "MBO",
        "Mercado_Negociacao_MB":    "MB",
        "Fundo_Exclusivo":          "Exclusivo",
        "Fundo_Nao_Listado_Exclusivo": "Não Listado"
    }

    registros = []
    for _, row in df_q.iterrows():
        # identifica em quais mercados o fundo negocia
        mercados = [
            nome for col, nome in mflags.items()
            if str(row.get(col, "")).strip().upper() == "SIM"
        ]
        if not mercados:
            mercados = ["Não Informado"]
        peso = 1.0 / len(mercados)
        for nome in mercados:
            registros.append({
                "CNPJ_Fundo": row["CNPJ_Fundo"],
                "Mercado":    nome,
                "Peso":       peso
            })

    df_m = pd.DataFrame(registros)

    fig2 = px.bar(
        df_m,
        x="Mercado",
        y="Peso",
        color="CNPJ_Fundo",
        barmode="group",
        labels={
            "Mercado":    "Mercado de Negociação",
            "CNPJ_Fundo": "Fundo",
            "Peso":       "Proporção"
        }
    )
    st.plotly_chart(fig2, use_container_width=True)

def show_info_adicionais(cnpj: str):
    st.subheader("Informações Adicionais e Documentos CVM")
    st.markdown(
        """
        Aqui você pode baixar todos os documentos oficiais enviados à CVM 
        para o fundo selecionado. Eles vêm agrupados num arquivo ZIP, nomeados 
        por tipo e período.
        """
    )
    if st.button("Gerar e baixar ZIP de documentos"):
        with st.spinner("Buscando documentos e montando ZIP..."):
            zip_bytes = get_documents_zip(cnpj)
        st.download_button(
            label="📥 Baixar documentos (ZIP)",
            data=zip_bytes,
            file_name=f"{cnpj}_{re.sub(r'D','',cnpj)}.zip",
            mime="application/zip"
        )

def main():
    df_fundos        = load_consolidado_geral()
    df_geral_compl   = load_consolidado_geral_completo()   # <-- novo
    df_ativos        = load_consolidado_ativo()
    df_imovel        = load_consolidado_imovel()
    df_res           = load_consolidado_resultado()
    df_rent          = load_consolidado_rentabilidade()

    page, cnpj, tipos_sel = sidebar_selections(df_fundos, df_ativos)

    if page == "Visão Geral":
        show_overview(df_geral_compl, cnpj)
        return


    if cnpj is None:
        st.warning("🔎 Por favor, selecione um fundo para começar.")
        return
    # cabeçalho fixo
    df_fundo = df_fundos[df_fundos["CNPJ_Chave"] == cnpj]
    show_dashboard_header(df_fundo)

    if page == "Portfólio de Ativos":
        show_portfolio_ativos(df_ativos, cnpj, tipos_sel)
    elif page == "Portfólio de Imóveis":
        show_portfolio_imoveis(df_imovel, cnpj)
    elif page == "Análise Financeira":
        show_analise_financeira(df_fundos, df_res, df_rent, df_imovel, cnpj)
    elif page == "Análise Qualitativa":
        show_analise_qualitativa(df_fundos, df_geral_compl, cnpj)
    else:  
        show_info_adicionais(cnpj)
    

if __name__ == "__main__":
    main()

