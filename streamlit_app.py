import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime, timedelta
import os
from urllib.parse import quote

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sistema UpDown - Orçamentos", page_icon="🏗️", layout="wide")

# ARQUIVOS
ARQUIVO_MATERIAIS = 'banco_materiais.csv'
ARQUIVO_HISTORICO = 'historico_orcamentos.csv'
ARQUIVO_LOGO = 'logo_updown.png'

# --- FUNÇÕES DE BANCO DE DADOS ---
def carregar_materiais():
    if not os.path.exists(ARQUIVO_MATERIAIS):
        # Inicia com alguns exemplos de MATERIAIS apenas
        dados = [
            {"Material": "Selante Fibrado (Balde 10kg)", "Preco_Unitario": 950.00},
            {"Material": "Borracha Líquida (Lata 18L)", "Preco_Unitario": 800.00},
            {"Material": "Disco de Corte Diamantado", "Preco_Unitario": 150.00},
            {"Material": "Lâmina de Estilete (Pct)", "Preco_Unitario": 25.00},
            {"Material": "Saco de Cimento", "Preco_Unitario": 35.00}
        ]
        df = pd.DataFrame(dados)
        df.to_csv(ARQUIVO_MATERIAIS, index=False)
        return df
    return pd.read_csv(ARQUIVO_MATERIAIS)

def salvar_materiais(df):
    df.to_csv(ARQUIVO_MATERIAIS, index=False)

def carregar_historico():
    if not os.path.exists(ARQUIVO_HISTORICO):
        return pd.DataFrame(columns=["Data", "Cliente", "Total", "Link Zap"])
    return pd.read_csv(ARQUIVO_HISTORICO)

def salvar_historico(dados):
    df_hist = carregar_historico()
    df_novo = pd.concat([df_hist, pd.DataFrame([dados])], ignore_index=True)
    df_novo.to_csv(ARQUIVO_HISTORICO, index=False)

# --- GERADOR DE PDF ---
def gerar_pdf(cliente, cnpj, data, validade, desc_servico, lista_materiais, total_mat, valor_mo, total_final, obs):
    pdf = FPDF()
    pdf.add_page()
    
    # Logo
    if os.path.exists(ARQUIVO_LOGO):
        pdf.image(ARQUIVO_LOGO, 10, 8, 40)
        pdf.ln(20)
    else:
        pdf.ln(10)

    # Cabeçalho
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, txt="ORÇAMENTO DE PRESTAÇÃO DE SERVIÇOS", ln=True, align='C')
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(190, 10, txt="UPDOWN SERVIÇOS DE ALTA PERFORMANCE | CNPJ: 36.130.036/0001-37", ln=True, align='C')
    pdf.ln(10)
    
    # Cliente
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 8, txt="DADOS DO CLIENTE", ln=True, align='L')
    pdf.set_font("Arial", size=11)
    pdf.cell(190, 6, txt=f"Cliente: {cliente}", ln=True)
    pdf.cell(190, 6, txt=f"CNPJ/CPF: {cnpj}", ln=True)
    pdf.cell(190, 6, txt=f"Data: {data}  |  Validade: {validade}", ln=True)
    pdf.ln(10)
    
    # --- 1. DESCRIÇÃO DOS SERVIÇOS ---
    pdf.set_font("Arial", 'B', 14)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(190, 10, txt="  1. DESCRIÇÃO DOS SERVIÇOS A EXECUTAR", ln=True, align='L', fill=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", size=11)
    # Imprime o texto que você digitou
    pdf.multi_cell(190, 6, txt=desc_servico.encode('latin-1', 'replace').decode('latin-1'))
    pdf.ln(10)

    # --- 2. RELAÇÃO DE MATERIAIS ---
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(190, 10, txt="  2. MATERIAIS INCLUSOS", ln=True, align='L', fill=True)
    pdf.ln(5)

    if lista_materiais:
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(110, 8, "Material", 1)
        pdf.cell(20, 8, "Qtd", 1, align='C')
        pdf.cell(30, 8, "Vl. Unit", 1, align='C')
        pdf.cell(30, 8, "Total", 1, align='C')
        pdf.ln()
        
        pdf.set_font("Arial", size=10)
        for item in lista_materiais:
            nome = item['Material'].encode('latin-1', 'replace').decode('latin-1')
            pdf.cell(110, 8, nome, 1)
            pdf.cell(20, 8, str(item['Qtd']), 1, align='C')
            pdf.cell(30, 8, f"R$ {item['Unitario']:,.2f}", 1, align='R')
            pdf.cell(30, 8, f"R$ {item['Total']:,.2f}", 1, align='R')
            pdf.ln()
    else:
        pdf.set_font("Arial", 'I', 11)
        pdf.cell(190, 10, "Nenhum material cobrado separadamente.", ln=True)

    pdf.ln(10)

    # --- 3. RESUMO FINANCEIRO ---
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(190, 10, txt="  3. VALORES E FECHAMENTO", ln=True, align='L', fill=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", size=12)
    
    # Valor dos Materiais
    pdf.cell(140, 8, "Total de Materiais:", 0, align='R')
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(50, 8, f"R$ {total_mat:,.2f}", 0, align='R')
    pdf.ln()
    
    # Valor da Mão de Obra
    pdf.set_font("Arial", size=12)
    pdf.cell(140, 8, "Mão de Obra Especializada (c/ NF):", 0, align='R')
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(50, 8, f"R$ {valor_mo:,.2f}", 0, align='R')
    pdf.ln()
    
    pdf.line(120, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(2)
    
    # TOTAL GERAL
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(140, 12, "TOTAL GERAL:", 0, align='R')
    pdf.cell(50, 12, f"R$ {total_final:,.2f}", 0, align='R')
    pdf.ln(15)
    
    # Observações
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 8, "OBSERVAÇÕES / FORMA DE PAGAMENTO:", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.multi_cell(0, 6, txt=obs.encode('latin-1', 'replace').decode('latin-1'))
    
    # Rodapé
    pdf.ln(20)
    pdf.cell(190, 5, "__________________________________________________", ln=True, align='C')
    pdf.cell(190, 5, "UPDOWN SERVICOS DE ALTA PERFORMANCE", ln=True, align='C')
    
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFACE VISUAL ---
st.sidebar.image(ARQUIVO_LOGO, width=200) if os.path.exists(ARQUIVO_LOGO) else None
st.title("🏗️ Sistema UpDown - Orçamentos")
st.markdown("---")

df_materiais = carregar_materiais()
menu = st.sidebar.radio("Navegação", ["Novo Orçamento", "Banco de Materiais", "Histórico"])

# ==============================================================================
# TELA 1: NOVO ORÇAMENTO (O FLUXO QUE VOCÊ PEDIU)
# ==============================================================================
if menu == "Novo Orçamento":
    st.header("📝 Criar Novo Orçamento")
    
    # --- 1. DADOS DO CLIENTE ---
    with st.expander("1. Dados do Cliente", expanded=True):
        c1, c2, c3 = st.columns([2, 1, 1])
        cliente = c1.text_input("Nome do Cliente")
        cnpj = c2.text_input("CNPJ / CPF")
        zap = c3.text_input("WhatsApp")

    # --- 2. SERVIÇOS (TEXTO MANUAL) ---
    with st.expander("2. Descrição dos Serviços (Manual)", expanded=True):
        st.info("Descreva abaixo todos os serviços que serão prestados.")
        desc_servico = st.text_area("Serviços a Executar:", height=150, placeholder="Ex: 1. Limpeza da fachada...\n2. Aplicação de selante...")

    # --- 3. MATERIAIS (DO BANCO DE DADOS) ---
    with st.expander("3. Adicionar Materiais", expanded=True):
        c1, c2, c3 = st.columns([3, 1, 1])
        
        # Selectbox puxa do CSV
        material_sel = c1.selectbox("Selecione o Material", df_materiais['Material'].unique())
        
        # Pega o preço unitário automático
        preco_base = df_materiais[df_materiais['Material'] == material_sel]['Preco_Unitario'].values[0]
        
        qtd = c2.number_input("Quantidade", min_value=1, value=1)
        
        # Botão Adicionar
        if 'carrinho_materiais' not in st.session_state: st.session_state.carrinho_materiais = []
        
        if c3.button("➕ Adicionar Material"):
            total_item = preco_base * qtd
            st.session_state.carrinho_materiais.append({
                "Material": material_sel,
                "Qtd": qtd,
                "Unitario": preco_base,
                "Total": total_item
            })
            st.success("Material adicionado!")

        # Mostra a tabela de materiais se tiver algo
        soma_materiais = 0.0
        if st.session_state.carrinho_materiais:
            df_cart = pd.DataFrame(st.session_state.carrinho_materiais)
            st.table(df_cart)
            soma_materiais = df_cart['Total'].sum()
            
            if st.button("Limpar Materiais"):
                st.session_state.carrinho_materiais = []
                st.rerun()

    # --- 4. MÃO DE OBRA E FECHAMENTO ---
    st.markdown("---")
    st.header("4. Fechamento de Valores")
    
    col_valores, col_obs = st.columns([1, 1]

