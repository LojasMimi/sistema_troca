import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
from openpyxl import load_workbook

# ================ CONFIGURAÇÃO INICIAL ================
st.set_page_config(page_title="Processo de Trocas", layout="wide")
st.title("♻️ Processo de Trocas")

# ================ ESTADO DA SESSÃO ================
if "trocas_dados" not in st.session_state:
    st.session_state.trocas_dados = []

# ================ FUNÇÕES ================
@st.cache_data(show_spinner=False)
def carregar_csv_combinado():
    url = "https://raw.githubusercontent.com/LojasMimi/transferencia_loja/refs/heads/main/cad_concatenado.csv"
    df = pd.read_csv(url, dtype=str)
    df = df.loc[:, ~df.columns.str.contains("^Unnamed", case=False)]
    df.columns = df.columns.str.strip().str.upper()

    def dedup_columns(cols):
        seen = {}
        new_cols = []
        for col in cols:
            if col in seen:
                seen[col] += 1
                new_cols.append(f"{col}_{seen[col]}")
            else:
                seen[col] = 0
                new_cols.append(col)
        return new_cols

    df.columns = dedup_columns(df.columns)

    if "SITUACAO" in df.columns:
        df["SITUACAO"] = df["SITUACAO"].str.replace("ç", "c", regex=False)
    if "DESCRIÇÃO" in df.columns:
        df["DESCRIÇÃO"] = df["DESCRIÇÃO"].str.replace("ç", "c", regex=False)

    return df

def buscar_produto(codigo, coluna, df):
    codigo = str(codigo).strip()
    resultado = df[df[coluna].astype(str).str.strip() == codigo]
    return resultado.iloc[0] if not resultado.empty else None

def gerar_formulario_excel(dados):
    fornecedores = set(item['FORNECEDOR'] for item in dados)

    if len(fornecedores) > 1:
        return None, "❌ Existem múltiplos fornecedores na lista de troca."

    try:
        # Carrega modelo
        modelo_path = "FORM-TROCAS.xlsx"
        wb = load_workbook(modelo_path)
        ws = wb.active

        # Define o fornecedor
        fornecedor = fornecedores.pop()
        ws["C3"] = fornecedor

        # Preenche os dados
        for i, item in enumerate(dados[:27]):  # A6 até A32 são 27 linhas
            row = i + 6
            ws[f"A{row}"] = item["CODIGO BARRA"]
            ws[f"B{row}"] = item["CODIGO"]
            ws[f"C{row}"] = item["DESCRICAO"]
            ws[f"D{row}"] = item["QUANTIDADE"]

        # Salva em memória
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        return output, None

    except Exception as e:
        return None, f"Erro ao gerar o formulário: {e}"

# ================ INTERFACE: PROCESSO DE TROCAS ================
df_combinado = carregar_csv_combinado()

# Seleção de fornecedor
fornecedores_unicos = sorted(df_combinado["FORNECEDOR"].dropna().unique())
selected_fornecedor = st.selectbox("Selecione o Fornecedor para realizar a troca:", [""] + fornecedores_unicos)

if selected_fornecedor:
    # Filtra df para o fornecedor selecionado
    df_fornecedor = df_combinado[df_combinado["FORNECEDOR"] == selected_fornecedor]

    st.subheader("🔍 Buscar Produto para Troca")

    col1, col2, col3 = st.columns([3, 4, 2])
    tipo_busca = col1.selectbox("Buscar por:", ["CÓDIGO DE BARRAS", "REF"])

    # Lista de identificadores filtrada para o fornecedor e tipo_busca
    coluna_id = "CODIGO BARRA" if tipo_busca == "CÓDIGO DE BARRAS" else "CODIGO"
    identificadores_disponiveis = sorted(df_fornecedor[coluna_id].dropna().astype(str).str.strip().unique())
    
    identificador = col2.selectbox(f"Selecione o {tipo_busca}:", [""] + identificadores_disponiveis)
    quantidade = col3.number_input("Quantidade", min_value=1, step=1, value=1)

    if st.button("🔎 Buscar Produto para Troca"):
        if not identificador:
            st.warning("❌ Por favor, selecione um identificador válido.")
        else:
            resultado = buscar_produto(identificador, coluna_id, df_fornecedor)

            if resultado is not None:
                st.session_state.trocas_dados.append({
                    "CODIGO BARRA": resultado.get("CODIGO BARRA", ""),
                    "CODIGO": resultado.get("CODIGO", ""),
                    "FORNECEDOR": resultado.get("FORNECEDOR", ""),
                    "DESCRICAO": resultado.get("DESCRIÇÃO", ""),
                    "QUANTIDADE": quantidade
                })
                st.success(f"✅ Produto adicionado à lista de trocas: {resultado.get('DESCRIÇÃO', '')}")
            else:
                st.warning("❌ Produto não encontrado com esse identificador.")

else:
    st.info("Por favor, selecione um fornecedor para iniciar o processo de troca.")

# ================ TABELA DE PRODUTOS PARA TROCA ================
if st.session_state.trocas_dados:
    st.subheader(f"📋 Produtos para Troca ({len(st.session_state.trocas_dados)} itens)")
    df_trocas = pd.DataFrame(st.session_state.trocas_dados)
    st.dataframe(df_trocas, use_container_width=True)

    colA, colB = st.columns([1, 3])
    if colA.button("🗑️ Remover Último Item"):
        removido = st.session_state.trocas_dados.pop()
        st.warning(f"Item removido: {removido['DESCRICAO']} (Qtd: {removido['QUANTIDADE']})")

    if colB.button("📄 Gerar Formulário de Troca"):
        excel_bytes, erro = gerar_formulario_excel(st.session_state.trocas_dados)

        if erro:
            st.error(erro)
        else:
            st.success("✅ Formulário de troca gerado com sucesso!")
            st.download_button(
                label="📥 Baixar Formulário de Troca",
                data=excel_bytes,
                file_name="FORMULARIO_TROCA.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
else:
    st.info("Nenhum produto adicionado para troca ainda.")

# ================ RODAPÉ ================
st.markdown("""
<hr style='border: 0; height: 1px; background: #ccc; margin-top: 2em; margin-bottom: 1em;' />
<div style='text-align: center; color: grey; font-size: 0.8em;'>
    Aplicativo desenvolvido por <a href="https://github.com/opablodantas" target="_blank"><strong>PABLO</strong></a> para as lojas <strong>MIMI</strong>. Todos os direitos reservados.
</div>
""", unsafe_allow_html=True)
