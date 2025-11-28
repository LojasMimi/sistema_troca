import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from io import BytesIO
from openpyxl import load_workbook, Workbook

# ==================================================
# CONFIGURAÇÃO BÁSICA
# ==================================================
st.set_page_config(page_title="Processo de Trocas", layout="wide")
st.title("♻️ Processo de Trocas")

# ==================================================
# ESTADO DA SESSÃO
# ==================================================
if "trocas_dados" not in st.session_state:
    st.session_state.trocas_dados = []

# ==================================================
# VALIDAÇÕES AUXILIARES
# ==================================================
def validar_ean(ean):
    """Valida o EAN antes de qualquer requisição à API."""
    if pd.isna(ean):
        return False, "Código de barras vazio."

    ean = str(ean).strip()

    if not ean.isdigit():
        return False, "O código de barras deve conter apenas números."

    if len(ean) > 14:
        return False, "O código de barras não pode ter mais de 14 dígitos."

    if len(ean) < 1:
        return False, "Código de barras inválido."

    return True, ean.zfill(14)


def validar_quantidade(qtd):
    """Valida a quantidade."""
    try:
        qtd = int(qtd)
        if qtd < 1:
            return False, "Quantidade deve ser pelo menos 1."
        return True, qtd
    except:
        return False, "Quantidade inválida."


# ==================================================
# FUNÇÃO PARA CONSULTA VIA API
# ==================================================
API_HEADERS = {
    "x-api-key": "ce085caefd32e119fa8557d1fbd0376e",
    "Cookie": "JSESSIONID=ACFE9BE2A3FBE06EA8CA86E169E5543D"
}

def buscar_produto_api(ean_input):
    """Consulta no sistema: Produto → Fornecedor → Dados fornecedor com tratamento de erros."""
    try:
        valid, ean_or_msg = validar_ean(ean_input)
        if not valid:
            return None, ean_or_msg

        ean = ean_or_msg

        url_prod = f"https://lojasmimi.varejofacil.com/api/v1/produto/produtos/consulta/{ean}"
        r_prod = requests.get(url_prod, headers=API_HEADERS)

        if r_prod.status_code == 404:
            return None, f"Produto não encontrado (404)."

        produto = r_prod.json()
        produto_id = produto.get("id")
        descricao = produto.get("descricao")

        if not produto_id:
            return None, "Produto não encontrado."

        # fornecedores
        url_forns = f"https://lojasmimi.varejofacil.com/api/v1/produto/produtos/{produto_id}/fornecedores"
        r_forns = requests.get(url_forns, headers=API_HEADERS)
        items = r_forns.json().get("items", [])
        if not items:
            return None, "Nenhum fornecedor encontrado."

        fornecedor_id = items[0].get("fornecedorId")
        referencia = items[0].get("referencia")

        # dados do fornecedor
        url_forn = f"https://lojasmimi.varejofacil.com/api/v1/pessoa/fornecedores/{fornecedor_id}"
        r_forn = requests.get(url_forn, headers=API_HEADERS)
        forn_data = r_forn.json()
        fantasia = forn_data.get("fantasia")

        return {
            "CODIGO BARRA": ean,
            "CODIGO": referencia,
            "DESCRICAO": descricao,
            "FORNECEDOR": fantasia
        }, None

    except requests.exceptions.RequestException:
        return None, "Falha de comunicação com a API. Tente novamente."

    except Exception as e:
        return None, f"Erro inesperado: {e}"


# ==================================================
# FUNÇÃO PARA GERAR FORMULÁRIO EXCEL
# ==================================================
def gerar_formulario_excel(dados):
    fornecedores = set(item['FORNECEDOR'] for item in dados)

    if len(fornecedores) > 1:
        return None, "❌ Existem múltiplos fornecedores na lista."

    try:
        modelo_path = "FORM-TROCAS.xlsx"
        wb = load_workbook(modelo_path)
        ws = wb.active

        fornecedor = fornecedores.pop()
        ws["B3"] = fornecedor

        for i, item in enumerate(dados[:27]):
            row = i + 6
            ws[f"A{row}"] = item["CODIGO BARRA"]
            ws[f"B{row}"] = item["CODIGO"]
            ws[f"C{row}"] = item["DESCRICAO"]
            ws[f"D{row}"] = item["QUANTIDADE"]

        output = BytesIO()
        wb.save(output)
        output.seek(0)
        return output, None

    except Exception as e:
        return None, f"Erro ao gerar formulário: {e}"


# ==================================================
# FUNÇÃO PARA GERAR ARQUIVO MODELO DO LOTE
# ==================================================
def gerar_modelo_lote():
    wb = Workbook()
    ws = wb.active
    ws.title = "TROCAS"

    ws["A1"] = "CODIGO DE BARRAS"
    ws["B1"] = "QUANTIDADE"

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return output

# ==================================================
# 🟦 ABAS DO SISTEMA
# ==================================================
tab1, tab2, tab3 = st.tabs(["🔍 INDIVIDUAL", "📦 LOTE", "📋 RELATÓRIO"])

# ==================================================
# 1️⃣ INDIVIDUAL
# ==================================================
with tab1:
    st.subheader("🔍 Buscar Produto Para Troca")

    col1, col2 = st.columns([4, 2])
    ean_input = col1.text_input("Digite o Código de Barras (EAN):")
    quantidade = col2.number_input("Quantidade", min_value=1, step=1, value=1)

    if st.button("🔎 Buscar Produto"):
        valid_qtd, qtd_or_msg = validar_quantidade(quantidade)
        if not valid_qtd:
            st.error(qtd_or_msg)
        else:
            resultado, erro = buscar_produto_api(ean_input)
            if erro:
                st.error(erro)
            else:
                # evitar duplicados
                if any(p["CODIGO BARRA"] == resultado["CODIGO BARRA"] for p in st.session_state.trocas_dados):
                    st.warning("⚠️ Produto já estava na lista. Quantidade somada.")
                    for p in st.session_state.trocas_dados:
                        if p["CODIGO BARRA"] == resultado["CODIGO BARRA"]:
                            p["QUANTIDADE"] += qtd_or_msg
                else:
                    resultado["QUANTIDADE"] = qtd_or_msg
                    st.session_state.trocas_dados.append(resultado)

                st.success(f"✅ Produto adicionado: {resultado['DESCRICAO']}")


# ==================================================
# 2️⃣ LOTE
# ==================================================
with tab2:
    st.subheader("📦 Lançar Trocas em Lote")

    st.markdown("### 📤 Baixar modelo Excel")
    st.download_button(
        label="📥 Baixar Modelo Excel",
        data=gerar_modelo_lote(),
        file_name="MODELO_TROCAS_LOTE.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.markdown("---")

    uploaded_file = st.file_uploader("📁 Envie o arquivo preenchido", type=["xlsx"])

    if uploaded_file:
        try:
            df_lote = pd.read_excel(uploaded_file)
        except:
            st.error("❌ Arquivo corrompido ou ilegível.")
            st.stop()

        if "CODIGO DE BARRAS" not in df_lote or "QUANTIDADE" not in df_lote:
            st.error("❌ O arquivo deve conter 'CODIGO DE BARRAS' e 'QUANTIDADE'.")
            st.stop()

        st.success("Arquivo carregado!")

        if df_lote["CODIGO DE BARRAS"].duplicated().any():
            st.warning("⚠️ Códigos duplicados encontrados — as quantidades serão somados.")
            df_lote = df_lote.groupby("CODIGO DE BARRAS", as_index=False)["QUANTIDADE"].sum()

        if st.button("🚀 Processar Lote"):
            sucessos = []
            falhas = []
            fornecedores = set()

            progress = st.progress(0)
            total = len(df_lote)

            for i, row in df_lote.iterrows():

                valid_ean, ean_or_msg = validar_ean(row["CODIGO DE BARRAS"])
                if not valid_ean:
                    falhas.append({"CODIGO": row["CODIGO DE BARRAS"], "ERRO": ean_or_msg})
                    progress.progress((i + 1) / total)
                    continue

                valid_qtd, qtd_or_msg = validar_quantidade(row["QUANTIDADE"])
                if not valid_qtd:
                    falhas.append({"CODIGO": row["CODIGO DE BARRAS"], "ERRO": qtd_or_msg})
                    progress.progress((i + 1) / total)
                    continue

                resultado, erro = buscar_produto_api(ean_or_msg)

                if erro:
                    falhas.append({"CODIGO": row["CODIGO DE BARRAS"], "ERRO": erro})
                else:
                    fornecedores.add(resultado["FORNECEDOR"])
                    resultado["QUANTIDADE"] = qtd_or_msg
                    sucessos.append(resultado)

                progress.progress((i + 1) / total)

            if len(fornecedores) > 1:
                st.error("❌ O lote contém produtos de múltiplos fornecedores. Processo cancelado.")
                st.write("Fornecedores encontrados:", fornecedores)
                st.stop()

            st.subheader("📊 Resultado do Lote")
            st.success(f"✅ Sucessos: {len(sucessos)}")
            st.error(f"❌ Falhas: {len(falhas)}")

            if falhas:
                st.write("### ❌ Erros encontrados")
                st.dataframe(pd.DataFrame(falhas))

            # adicionar ao relatório
            for item in sucessos:
                if any(p["CODIGO BARRA"] == item["CODIGO BARRA"] for p in st.session_state.trocas_dados):
                    for p in st.session_state.trocas_dados:
                        if p["CODIGO BARRA"] == item["CODIGO BARRA"]:
                            p["QUANTIDADE"] += item["QUANTIDADE"]
                else:
                    st.session_state.trocas_dados.append(item)

            st.success("🎉 Produtos válidos adicionados ao relatório!")


# ==================================================
# 3️⃣ RELATÓRIO
# ==================================================
with tab3:
    st.subheader("📋 Produtos Adicionados Para Troca")

    if st.session_state.trocas_dados:
        df_trocas = pd.DataFrame(st.session_state.trocas_dados)
        st.dataframe(df_trocas, use_container_width=True)

        colA, colB = st.columns([1, 3])

        if colA.button("🗑️ Remover Último Item"):
            removido = st.session_state.trocas_dados.pop()
            st.warning(f"Item removido: {removido['DESCRICAO']} (Qtd: {removido['QUANTIDADE']})")

        if colB.button("📄 Gerar Formulário de Troca"):

            total_itens = len(st.session_state.trocas_dados)

            # 🔥 NOVA VALIDAÇÃO — LIMITE DE 27 ITENS
            if total_itens > 27:
                st.error("❌ O formulário suporta no máximo 27 itens.")
                st.error(f"Você possui {total_itens} itens — reduza a lista para continuar.")
                st.stop()

            excel_bytes, erro = gerar_formulario_excel(st.session_state.trocas_dados)

            if erro:
                st.error(erro)
            else:
                st.success("✅ Formulário gerado!")
                st.download_button(
                    label="📥 Baixar Formulário",
                    data=excel_bytes,
                    file_name="FORMULARIO_TROCAS.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    else:
        st.info("Nenhum produto adicionado ainda.")

# ==================================================
# RODAPÉ
# ==================================================
st.markdown("""
<hr style='border: 0; height: 1px; background: #ccc; margin-top: 2em; margin-bottom: 1em;' />
<div style='text-align: center; color: grey; font-size: 0.8em;'>
    Aplicativo desenvolvido por <a href="https://github.com/opablodantas" target="_blank"><strong>PABLO</strong></a> para as lojas <strong>MIMI</strong>. Todos os direitos reservados.
</div>
""", unsafe_allow_html=True)
