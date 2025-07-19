# Case FEGIK – BI e Dados

> Desenvolvido por **Juliano Pádua**

## Sumário

- [Descrição Geral](#descrição-geral)
- [Objetivos do Projeto](#objetivos-do-projeto)
- [Decisões de Projeto](#decisões-de-projeto)
- [Estrutura de Diretórios](#estrutura-de-diretórios)
- [Execução Local](#execução-local)
  - [Com ambiente virtual (recomendado)](#com-ambiente-virtual-recomendado)
  - [Execução do Streamlit](#execução-do-streamlit)
- [Dependências](#dependências)
- [Notas Finais](#notas-finais)

---

## Descrição Geral

Este projeto foi desenvolvido como parte do processo seletivo para o programa de estágio em BI e Dados da FEGIK. Seu objetivo principal é consolidar informações públicas da Comissão de Valores Mobiliários (CVM) sobre Fundos Imobiliários (FIIs) e permitir sua análise em um dashboard interativo.

---

## Objetivos do Projeto

O projeto contempla três etapas principais:

1. **Extração automatizada de dados (Webscraping):**
   - Download dos arquivos `.zip` dos informes trimestrais da CVM.

2. **Tratamento e consolidação:**
   - Extração e unificação dos `.csv` por tipo de documento.

3. **Visualização interativa:**
   - Criação de um painel em Streamlit que permite explorar, comparar e analisar os dados dos fundos.

---

## Decisões de Projeto

- **Modularização:** funções auxiliares estão em `utils.py`, separando lógica de extração e visualização.
- **Logs persistentes:** monitoramento do progresso dos downloads e processamento.
- **Evita redundâncias:** reaproveitamento de arquivos já processados.
- **Pipeline resiliente:** tratamento de arquivos inconsistentes da CVM.

---

## Estrutura de Diretórios

```

case-fegik/
├── data/
│   ├── raw/                ← Arquivos .zip da CVM
│   ├── processed/          ← CSVs extraídos dos .zip
│   └── consolidated/       ← CSVs consolidados por tipo
├── log/
│   ├── downloads\_log.csv   ← Histórico de downloads
│   └── processamento.log   ← Log de processamento
├── src/
│   ├── app.py              ← Aplicação Streamlit
│   ├── main.py             ← Script de extração e tratamento
│   └── utils.py            ← Funções auxiliares
├── config.yaml             ← Arquivo de configuração
├── requirements.txt        ← Dependências do projeto
├── .gitignore
└── README.md

````

---

## Execução Local

### Com ambiente virtual (recomendado)

#### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/case-fegik.git
cd case-fegik
````

### ⚠️ Observação importante para testes locais
Caso deseje **testar o algoritmo de extração e tratamento de dados** (webscraping), você deve **deletar a pasta `data/` inteira antes de executar `main.py`**.

```bash
rm -rf data/
```

> Isso é necessário porque, para hospedar a aplicação na web (por exemplo, via Streamlit Cloud), os arquivos `.csv` consolidados já foram incluídos no repositório. Dessa forma, o script `main.py` detecta que os dados já existem e não baixa novamente.

---

#### 2. Crie e ative um ambiente virtual

##### No **Linux/macOS**:

```bash
python3 -m venv venv
source venv/bin/activate
```

##### No **Windows** (cmd):

```cmd
python -m venv venv
venv\Scripts\activate
```

##### No **Windows PowerShell**:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

#### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

#### 4. Execute o script de extração e consolidação

```bash
python src/main.py
```

Esse script fará o download dos arquivos da CVM e consolidará os dados em `data/consolidated/`.

---

### Execução do Streamlit

Após a extração dos dados:

```bash
streamlit run src/app.py
```

O navegador será aberto automaticamente com o dashboard. A aplicação permite:

* Selecionar um fundo pelo nome ou CNPJ;
* Visualizar indicadores financeiros ao longo do tempo;
* Comparar múltiplos fundos e calcular médias;
* Acessar metadados (endereço, telefone, gestor, CNPJ, site e e-mail);
* Conferir detalhes como segmento de atuação, público-alvo, data de início e mandato;
* Ver seu próprio perfil (LinkedIn, GitHub etc).

---

## Dependências

As principais bibliotecas usadas estão em `requirements.txt`. Incluem:

```
streamlit>=1.35.0
pandas>=2.2.2
requests>=2.31.0
beautifulsoup4>=4.12.3
pyyaml>=6.0.1
tqdm>=4.66.4
plotly>=5.22.0
```

Essas versões garantem compatibilidade com os métodos de scraping, leitura de arquivos e construção de gráficos interativos.

---

## Notas Finais

* A estrutura foi pensada para permitir fácil escalabilidade.
* Outras fontes externas podem ser integradas posteriormente, como Yahoo Finance ou classificações de risco da CVM.
* Sinta-se à vontade para clonar, estudar e adaptar o projeto.

> **Juliano Pádua**
> *LinkedIn, GitHub e contato pessoal a definir no topo da aplicação.*
