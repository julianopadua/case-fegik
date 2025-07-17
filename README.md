# Case FEGIK – BI e Dados

> Implementado por **Juliano Pádua**

## Sumário

- [Descrição Geral](#descrição-geral)
- [Objetivos do Projeto](#objetivos-do-projeto)
- [Decisões de Projeto](#decisões-de-projeto)
- [Estrutura de Diretórios](#estrutura-de-diretórios)
- [Execução Local](#execução-local)
- [Dependências](#dependências)
- [Notas Finais](#notas-finais)

---

## Descrição Geral

Este projeto foi desenvolvido como parte do processo seletivo para o programa de estágio em BI e Dados da FEGIK. O objetivo central é realizar a extração, o tratamento e a consolidação de informações públicas fornecidas pela Comissão de Valores Mobiliários (CVM) sobre Fundos Imobiliários (FIIs), com foco nos informes trimestrais disponíveis para consulta.

---

## Objetivos do Projeto

O projeto está dividido em três etapas principais:

1. **Extração automatizada dos dados (Webscraping):**
   - Acessar dinamicamente o repositório da CVM.
   - Baixar os arquivos `.zip` contendo os informes trimestrais.

2. **Tratamento e consolidação:**
   - Descompactar os arquivos `.zip` em diretórios organizados por ano.
   - Consolidar os arquivos `.csv` de cada tipo de informe em um único arquivo por categoria, contendo dados de todos os anos disponíveis.

3. **Registro e controle de execução:**
   - Implementar logs persistentes tanto para os downloads quanto para o processo de consolidação, evitando redundâncias e assegurando rastreabilidade.

---

## Decisões de Projeto

- **Separação modular via `utils.py`:** todas as funções auxiliares foram abstraídas para um único módulo reutilizável.
- **Uso de logs persistentes:** tanto os arquivos já baixados quanto os erros e sucessos de processamento são documentados em arquivos na pasta `log/`.
- **Evita downloads redundantes:** ao executar o script mais de uma vez, os arquivos já existentes não são baixados novamente, nem há animação desnecessária.
- **Leitura robusta de arquivos CSV:** os arquivos foram lidos com codificação `latin-1`, separador `;` e aspas desconsideradas, para lidar com inconsistências frequentes nas bases da CVM.
- **Consolidação dinâmica:** o algoritmo identifica automaticamente os tipos de arquivos com base em seus nomes, descartando o sufixo de ano, e agrupa todos os anos de cada tipo em um único arquivo final.

---

## Estrutura de Diretórios

A estrutura do projeto é gerada automaticamente da seguinte forma:

```

case-fegik/
├── data/
│   ├── raw/               ← Arquivos .zip baixados da CVM
│   ├── processed/         ← CSVs extraídos dos arquivos .zip
│   └── consolidated/      ← Arquivos CSV únicos por tipo de dado
├── log/
│   ├── downloads\_log.csv  ← Histórico de downloads
│   └── processamento.log  ← Log de consolidação e extração
├── output/
├── img/
├── src/
│   ├── main.py            ← Script principal
│   └── utils.py           ← Módulo com funções auxiliares
├── config.yaml            ← Configuração de caminhos
├── requirements.txt       ← Dependências do projeto
├── .gitignore
└── README.md

````

---

## Execução Local

### Pré-requisitos

- Python **3.10 ou superior**
- `pip` instalado

### Passo a passo

1. Clone o repositório:

```bash
git clone https://github.com/seu-usuario/case-fegik.git
cd case-fegik
````

2. Instale as dependências:

```bash
pip install -r requirements.txt
```

3. Execute o script principal:

```bash
python src/main.py
```

Ao final da execução, os dados estarão disponíveis em `data/consolidated/`, prontos para análise ou visualização em ferramentas como Power BI.

---

## Dependências

As bibliotecas utilizadas estão listadas no arquivo `requirements.txt`, com versões mínimas recomendadas:

```
requests>=2.31.0
beautifulsoup4>=4.12.3
tqdm>=4.66.4
pyyaml>=6.0.1
```

Essas versões foram escolhidas para garantir estabilidade com os métodos utilizados no parsing de HTML, manipulação de arquivos e progresso de download.

---


