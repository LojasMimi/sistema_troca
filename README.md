
# ♻️ Processo de Trocas — Lojas Mimi

Este é um aplicativo web desenvolvido em **Python** com **Streamlit** para auxiliar no processo de trocas de produtos com fornecedores nas Lojas Mimi. A aplicação permite selecionar um fornecedor, buscar produtos por código ou referência, adicionar produtos à lista de troca e gerar um formulário Excel pronto para ser enviado ao fornecedor.

## 📦 Funcionalidades

* ✅ Seleção de fornecedor com base em um cadastro pré-existente
* 🔎 Busca de produtos por **código de barras** ou **referência**
* ➕ Adição de produtos à lista de trocas com definição de quantidade
* 📋 Visualização da lista de trocas atual
* 🗑️ Remoção de itens da lista
* 📄 Geração de formulário Excel (`FORMULARIO_TROCA.xlsx`) com os dados dos produtos
* 📥 Download direto do formulário preenchido

## 📁 Estrutura do Projeto

```
.
├── FORM-TROCAS.xlsx         # Modelo de formulário usado como base para preenchimento
├── fazer_trocas.py          # Código principal do app
└── requirements.txt         # Lista de dependências
```

## 🚀 Como Rodar o Projeto

### 1. Clone o repositório

```bash
git clone https://github.com/LojasMimi/sistema_troca.git
cd sistema_troca
```

### 2. Crie um ambiente virtual (opcional, mas recomendado)

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

### 3. Instale as dependências

Crie um `requirements.txt` com o seguinte conteúdo:

```
streamlit
pandas
openpyxl
```

Depois instale com:

```bash
pip install -r requirements.txt
```

### 4. Coloque o arquivo `FORM-TROCAS.xlsx` na raiz do projeto

Esse arquivo é o modelo que será preenchido com os dados da troca.

### 5. Execute o app

```bash
streamlit run fazer_trocas.py
```

O navegador abrirá automaticamente o aplicativo na URL [http://localhost:8501](http://localhost:8501).

## 🔗 Fonte dos Dados

Os produtos são carregados a partir de um CSV hospedado no GitHub:

```
https://raw.githubusercontent.com/LojasMimi/transferencia_loja/refs/heads/main/cad_concatenado.csv
```

Este arquivo deve conter colunas como:

* `FORNECEDOR`
* `CODIGO`
* `CODIGO BARRA`
* `DESCRIÇÃO`
* `SITUAÇÃO` (opcional)

## 🧠 Tecnologias Usadas

* [Streamlit](https://streamlit.io/)
* [Pandas](https://pandas.pydata.org/)
* [OpenPyXL](https://openpyxl.readthedocs.io/)

## 👨‍💻 Desenvolvedor

Aplicativo desenvolvido por [**Pablo Dantas**](https://github.com/opablodantas) para as **Lojas Mimi**.

---

