import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import os
from urllib.parse import quote
from PIL import Image

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="UpDown Pro - Business Premium", page_icon="🏗️", layout="wide")

# CONFIGURAÇÃO DE ARQUIVOS
ARQUIVO_MATERIAIS = 'banco_materiais.csv'
ARQUIVO_HISTORICO = 'historico_orcamentos.csv'
ARQUIVO_LOGO = 'Logo sem fundo.png'
ARTES_INTRO = ['capa_1.png', 'capa_2.png', 'capa_3.png']
ARTES_OUTRO = ['capa_4.png', 'capa_5.png', 'capa_6.png', 'capa_7.png', 'capa_8.png']

# --- FUNÇÕES AUXILIARES ---
def formatar_qtd(valor):
    """Exibe 1 em vez de 1.0 e 1.5 em vez de 1.50"""
    return f"{int(valor)}" if valor == int(valor) else f"{valor}".replace('.', ',')

def carregar_materiais():
    if not os.path.exists(ARQUIVO_MATERIAIS):
        return pd.DataFrame(columns=["Material", "Descricao", "Preco_Unitario"])
    return pd.read_csv(ARQUIVO_MATERIAIS)

# --- CLASSE PDF CUSTOMIZADA ---
class UpDownPDF(FPDF):
    def __init__(self, intro_count, total_outro_start):
        super().__init__()
        self.intro_count = intro_count
        self.total_outro_start = total_outro_start

    def header(self):
        # O cabeçalho só aparece nas páginas de ORÇAMENTO (após as capas e antes do encerramento)
        if self.intro_count < self.page_no() < self.total_outro_start:
            if os.path.exists(ARQUIVO_LOGO):
                self.image(ARQUIVO_LOGO, x=10, y=8, w=25)
            self.set_y(10)
            self.set_x(38)
            self.set_font("helvetica", 'B', 12)
            self.cell(0, 5, "UPDOWN - SERVIÇOS DE ALTA PERFORMANCE", ln=True)
            self.set_font("helvetica", '', 9)
            self.set_x(38)
            self.cell(0, 5, "CNPJ: 36.130.036/0001-37 | @updown.altaperformance", ln=True)
            self.ln(10)
            self.line(10, 28, 200, 28)

    def footer(self):
        if self.intro_count < self.page_no() < self.total_outro_start:
            self.set_y(-15)
            self.set_font("helvetica", 'I', 8)
            self.cell(0, 10, f"Página {self.page_no()}", align='C')

# --- MOTOR DE GERAÇÃO DE PDF ---
def gerar_pdf_premium(cliente, cnpj, data, blocos, total_calc, total_final, texto_comercial, obs):
    # Calculamos onde o orçamento termina para saber quando parar de mostrar o header
    # Inicialmente não sabemos, então estimamos após rodar o conteúdo
    pdf = UpDownPDF(intro_count=len(ARTES_INTRO), total_outro_start=999) 
    pdf.set_auto_page_break(auto=True, margin=25)

    # 1. PÁGINAS DE INTRODUÇÃO (CAPA 1, 2, 3)
    for arte in ARTES_INTRO:
        pdf.add_page()
        if os.path.exists(arte):
            # w=210, h=297 é o tamanho exato da folha A4 em mm
            pdf.image(arte, x=0, y=0, w=210, h=297)
        else:
            pdf.cell(0, 10, f"Aviso: Arquivo {arte} não encontrado.", ln=True)

    # 2. CONTEÚDO DO ORÇAMENTO
    pdf.add_page()
    pdf.ln(20)
    pdf.set_font("helvetica", 'B', 16)
    pdf.cell(190, 10, "PROPOSTA TÉCNICA E COMERCIAL", ln=True, align='C')
    pdf.ln(5)

    # Dados do Cliente
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("helvetica", 'B', 10)
    pdf.cell(190, 8, " DADOS DO CLIENTE", ln=True, fill=True)
    pdf.set_font("helvetica", '', 10)
    pdf.cell(95, 7, f" Cliente: {cliente}", border='B')
    pdf.cell(95, 7, f" Data: {data}", border='B', ln=True)
    pdf.cell(190, 7, f" CNPJ/CPF: {cnpj}", border='B', ln=True)
    pdf.ln(8)

    # Blocos de Serviço
    for i, bloco in enumerate(blocos, 1):
        if pdf.get_y() > 220: pdf.add_page()
        
        pdf.set_font("helvetica", 'B', 12)
        pdf.set_fill_color(255, 140, 0) # Laranja UpDown
        pdf.set_text_color(255, 255, 255)
        pdf.cell(190, 9, f"  {i}. {bloco['titulo'].upper()}", ln=True, fill=True)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(2)

        # Diagnóstico e Fotos
        pdf.set_font("helvetica", 'B', 10)
        pdf.cell(190, 6, "Diagnóstico da Avaria:", ln=True)
        pdf.set_font("helvetica", '', 10)
        pdf.multi_cell(190, 5, bloco['desc_avaria'])
        pdf.ln(2)

        if bloco['fotos']:
            y_fotos = pdf.get_y()
            largura_f = 60 if len(bloco['fotos']) > 1 else 90
            for idx, foto in enumerate(bloco['fotos']):
                img = Image.open(foto)
                temp_name = f"temp_{i}_{idx}.png"
                img.save(temp_name)
                pdf.image(temp_name, x=10 + (idx * (largura_f + 5)), y=y_fotos, w=largura_f)
            pdf.set_y(y_fotos + largura_f * 0.8 + 5)

        # Solução
        pdf.set_font("helvetica", 'B', 10)
        pdf.cell(190, 6, "Solução Técnica Proposta:", ln=True)
        pdf.set_font("helvetica", '', 10)
        pdf.multi_cell(190, 5, bloco['descricao'])
        pdf.ln(4)

        # Tabela de Materiais
        if bloco['materiais']:
            pdf.set_fill_color(245, 245, 245)
            pdf.set_font("helvetica", 'B', 9)
            pdf.cell(110, 6, " Insumo", 1, 0, 'L', True)
            pdf.cell(20, 6, "Qtd", 1, 0, 'C', True)
            pdf.cell(30, 6, "Unit.", 1, 0, 'C', True)
            pdf.cell(30, 6, "Total", 1, 1, 'C', True)
            pdf.set_font("helvetica", '', 9)
            for m in bloco['materiais']:
                pdf.cell(110, 6, f" {m['nome'][:55]}", 1)
                pdf.cell(20, 6, formatar_qtd(m['qtd']), 1, 0, 'C')
                pdf.cell(30, 6, f"{m['unit']:,.2f}", 1, 0, 'R')
                pdf.cell(30, 6, f"{m['total']:,.2f}", 1, 1, 'R')
        
        pdf.set_font("helvetica", 'B', 10)
        pdf.cell(150, 7, "Subtotal do Item (Materiais + Mão de Obra + NF): ", 0, 0, 'R')
        pdf.cell(40, 7, f"R$ {bloco['total_bloco']:,.2f}", 0, 1, 'R')
        pdf.ln(5)

    # Fechamento Comercial
    if pdf.get_y() > 200: pdf.add_page()
    pdf.set_font("helvetica", 'B', 13)
    pdf.cell(190, 10, "CONDIÇÕES COMERCIAIS", ln=True)
    pdf.set_font("helvetica", '', 11)
    pdf.multi_cell(190, 6, texto_comercial)
    pdf.ln(5)
    
    pdf.set_fill_color(30, 30, 30)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", 'B', 14)
    pdf.cell(140, 12, " INVESTIMENTO TOTAL ESTIMADO:", 0, 0, 'R', True)
    pdf.cell(50, 12, f"R$ {total_final:,.2f} ", 0, 1, 'R', True)
    pdf.set_text_color(0, 0, 0)
    
    if obs:
        pdf.ln(5)
        pdf.set_font("helvetica", 'I', 9)
        pdf.multi_cell(190, 5, f"Observações: {obs}")

    # 3. PÁGINAS DE ENCERRAMENTO (CAPA 4 A 8)
    pdf.total_outro_start = pdf.page_no() + 1
    for arte in ARTES_OUTRO:
        pdf.add_page()
        if os.path.exists(arte):
            pdf.image(arte, x=0, y=0, w=210, h=297)

    # Limpeza de temporários
    for f in os.listdir():
        if f.startswith("temp_"): os.remove(f)

    return pdf.output(dest='S').encode('latin-1')

# --- INTERFACE STREAMLIT ---
st.title("🏗️ UpDown Pro - Gerador de Propostas Premium")

df_materiais = carregar_materiais()
menu = st.sidebar.radio("Navegação", ["Criar Orçamento", "Banco de Materiais"])

if menu == "Criar Orçamento":
    with st.expander("👤 Dados do Cliente", expanded=True):
        col1, col2 = st.columns(2)
        cliente = col1.text_input("Nome do Cliente / Condomínio")
        cnpj = col2.text_input("CNPJ / CPF")
        zap = st.text_input("WhatsApp para contato")

    if 'blocos' not in st.session_state: st.session_state.blocos = []

    if st.button("➕ Adicionar Serviço ao Orçamento"):
        st.session_state.blocos.append({
            "titulo": "", "descricao": "", "desc_avaria": "", "fotos": [],
            "materiais": [], "valor_mo": 0.0, "soma_materiais": 0.0, "total_bloco": 0.0
        })

    remover_idx = None
    for i, bloco in enumerate(st.session_state.blocos):
        with st.container(border=True):
            c_tit, c_btn = st.columns([6, 1])
            bloco['titulo'] = c_tit.text_input(f"Título do Serviço {i+1}", value=bloco['titulo'], key=f"t_{i}")
            if c_btn.button("🗑️", key=f"del_{i}"): remover_idx = i

            st.write("**📸 Diagnóstico e Imagens**")
            col_f1, col_f2 = st.columns([1, 2])
            fotos_upload = col_f1.file_uploader(f"Anexar até 3 fotos (Item {i+1})", type=['jpg','jpeg','png'], key=f"f_{i}", accept_multiple_files=True)
            bloco['fotos'] = fotos_upload[:3] if fotos_upload else []
            bloco['desc_avaria'] = col_f2.text_area(f"O que foi identificado na avaria?", value=bloco['desc_avaria'], key=f"da_{i}", height=100)
            
            bloco['descricao'] = st.text_area(f"Solução Técnica Proposta (O que faremos)", value=bloco['descricao'], key=f"sol_{i}")

            st.write("**📦 Insumos e Mão de Obra**")
            cm, cq, ca = st.columns([3, 1, 1])
            sel = cm.selectbox("Material", df_materiais['Material'].unique() if not df_materiais.empty else [], key=f"sel_{i}", index=None)
            qtd = cq.number_input("Qtd", 1.0, key=f"q_{i}", step=1.0)
            if ca.button("Add", key=f"add_{i}"):
                if sel:
                    preco = df_materiais[df_materiais['Material'] == sel]['Preco_Unitario'].values[0]
                    bloco['materiais'].append({"nome": sel, "qtd": qtd, "unit": preco, "total": preco*qtd})
                    st.rerun()

            if bloco['materiais']:
                df_tab = pd.DataFrame(bloco['materiais'])
                st.table(df_tab[['nome', 'qtd', 'total']])
                bloco['soma_materiais'] = df_tab['total'].sum()
            
            bloco['valor_mo'] = st.number_input(f"Mão de Obra + NF (R$)", 0.0, value=bloco['valor_mo'], key=f"mo_{i}")
            bloco['total_bloco'] = bloco['soma_materiais'] + bloco['valor_mo']
            st.info(f"Subtotal Item {i+1}: R$ {bloco['total_bloco']:,.2f}")

    if remover_idx is not None:
        del st.session_state.blocos[remover_idx]
        st.rerun()

    st.divider()
    total_calc = sum(b['total_bloco'] for b in st.session_state.blocos)
    
    col_c1, col_c2 = st.columns(2)
    txt_com = col_c1.text_area("Condições Comerciais", "Pagamento: 50% de sinal e 50% na conclusão.\nInício: A combinar.", height=150)
    total_final = col_c2.number_input("VALOR FINAL NEGOCIADO (R$)", value=float(total_calc))
    obs_f = st.text_input("Observações de Rodapé (Garantia, Validade etc)")

    if st.button("🚀 GERAR PROPOSTA PDF COMPLETA", type="primary", use_container_width=True):
        if not cliente:
            st.error("Nome do cliente obrigatório.")
        else:
            hoje = datetime.today().strftime("%d/%m/%Y")
            pdf_bytes = gerar_pdf_premium(cliente, cnpj, hoje, st.session_state.blocos, total_calc, total_final, txt_com, obs_f)
            st.success("Proposta gerada com sucesso!")
            st.download_button("⬇️ Baixar PDF", pdf_bytes, f"Proposta_{cliente}.pdf", "application/pdf")

elif menu == "Banco de Materiais":
    st.header("📦 Gerenciamento de Insumos")
    df_m = carregar_materiais()
    df_edit = st.data_editor(df_m, num_rows="dynamic", use_container_width=True)
    if st.button("Salvar Alterações"):
        salvar_materiais(df_edit)
        st.success("Banco de dados atualizado!")
