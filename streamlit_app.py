import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime, timedelta
import os
from urllib.parse import quote
from PIL import Image
import io

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sistema UpDown Pro", page_icon="🏗️", layout="wide")

# ARQUIVOS DE DADOS E IMAGENS
ARQUIVO_MATERIAIS = 'banco_materiais.csv'
ARQUIVO_HISTORICO = 'historico_orcamentos.csv'
ARQUIVO_LOGO = 'Logo sem fundo.png' 
ARQUIVO_WATERMARK = 'watermark_temp.png'

# --- FUNÇÕES DE SUPORTE ---
def preparar_marca_dagua():
    if os.path.exists(ARQUIVO_LOGO) and not os.path.exists(ARQUIVO_WATERMARK):
        try:
            img = Image.open(ARQUIVO_LOGO).convert("RGBA")
            datas = img.getdata()
            new_data = [(item[0], item[1], item[2], int(item[3] * 0.10)) for item in datas]
            img.putdata(new_data)
            img.save(ARQUIVO_WATERMARK, "PNG")
        except: pass

def carregar_materiais():
    if not os.path.exists(ARQUIVO_MATERIAIS):
        df = pd.DataFrame([{"Material": "Exemplo", "Descricao": "Item", "Preco_Unitario": 0.0}])
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

# --- CLASSE PDF ---
class PDF(FPDF):
    def header(self):
        if os.path.exists(ARQUIVO_WATERMARK):
            self.image(ARQUIVO_WATERMARK, x=45, y=80, w=120)
        if os.path.exists(ARQUIVO_LOGO):
            self.image(ARQUIVO_LOGO, x=10, y=8, w=30)
        self.set_y(12)
        self.set_x(42)
        self.set_font("Arial", 'B', 14)
        self.cell(0, 5, "UPDOWN - SERVIÇOS DE ALTA PERFORMANCE", ln=True, align='L')
        self.set_x(42)
        self.set_font("Arial", '', 10)
        self.cell(0, 5, "CNPJ: 36.130.036/0001-37", ln=True, align='L')
        self.ln(12)
        self.line(10, 32, 200, 32)
        self.ln(5)

# --- GERADOR DE PDF ---
def gerar_pdf(cliente, cnpj, data, validade, blocos, total_calc, total_final, texto_comercial, obs):
    preparar_marca_dagua()
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, txt="PROPOSTA TÉCNICA E COMERCIAL", ln=True, align='C')
    pdf.ln(5)
    
    # Dados Cliente
    pdf.set_fill_color(245, 245, 245)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(190, 8, "  DADOS DO CLIENTE:", ln=True, fill=True)
    pdf.set_font("Arial", '', 11)
    pdf.cell(190, 6, f"  Cliente: {cliente}", ln=True)
    pdf.cell(190, 6, f"  CNPJ/CPF: {cnpj}", ln=True)
    pdf.cell(190, 6, f"  Data: {data}   |   Validade: {validade}", ln=True)
    pdf.ln(5)

    for i, bloco in enumerate(blocos, 1):
        if pdf.get_y() > 200: pdf.add_page()
        
        pdf.set_font("Arial", 'B', 13)
        pdf.set_fill_color(255, 204, 102)
        pdf.cell(190, 8, txt=f"  ITEM {i}. {bloco['titulo'].upper()}", ln=True, fill=True)
        pdf.ln(3)

        # 1. Foto e Descrição da Avaria
        if bloco['desc_avaria']:
            pdf.set_font("Arial", 'B', 10)
            pdf.set_text_color(180, 0, 0)
            pdf.multi_cell(190, 5, txt=f"AVARIA: {bloco['desc_avaria'].encode('latin-1', 'replace').decode('latin-1')}")
            pdf.set_text_color(0, 0, 0)
            pdf.ln(2)

        if bloco['foto']:
            try:
                img_pil = Image.open(bloco['foto'])
                img_path = f"temp_img_{i}.png"
                img_pil.save(img_path)
                pdf.image(img_path, x=65, w=80) 
                pdf.ln(4)
                os.remove(img_path)
            except: pass

        # 2. Solução Técnica
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(190, 6, "Solução Técnica Proposta:", ln=True)
        pdf.set_font("Arial", '', 11)
        pdf.multi_cell(190, 6, txt=bloco['descricao'].encode('latin-1', 'replace').decode('latin-1'))
        pdf.ln(3)

        # 3. Tabela Materiais
        if bloco['materiais']:
            pdf.set_font("Arial", 'B', 10)
            pdf.set_fill_color(240, 240, 240)
            pdf.cell(110, 6, "Material", 1, 0, 'L', True)
            pdf.cell(20, 6, "Qtd", 1, 0, 'C', True)
            pdf.cell(30, 6, "Unit", 1, 0, 'C', True)
            pdf.cell(30, 6, "Total", 1, 1, 'C', True)
            pdf.set_font("Arial", '', 10)
            for mat in bloco['materiais']:
                nome = mat['nome'][:55]
                pdf.cell(110, 6, nome.encode('latin-1', 'replace').decode('latin-1'), 1)
                pdf.cell(20, 6, str(mat['qtd']), 1, 0, 'C')
                pdf.cell(30, 6, f"{mat['unit']:,.2f}", 1, 0, 'R')
                pdf.cell(30, 6, f"{mat['total']:,.2f}", 1, 1, 'R')
            pdf.ln(2)

        # Totais Bloco
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(150, 6, f"TOTAL ITEM {i}:", 0, align='R')
        pdf.cell(40, 6, f"R$ {bloco['total_bloco']:,.2f}", 0, align='R')
        pdf.ln(10)

    # Proposta Comercial Final
    if pdf.get_y() > 200: pdf.add_page()
    pdf.set_font("Arial", 'B', 13)
    pdf.set_fill_color(50, 50, 50)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(190, 8, txt="  PROPOSTA COMERCIAL", ln=True, fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)
    pdf.set_font("Arial", '', 11)
    pdf.multi_cell(190, 6, txt=texto_comercial.encode('latin-1', 'replace').decode('latin-1'))
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 16)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(140, 12, "VALOR FINAL:", 0, align='R', fill=True)
    pdf.cell(50, 12, f"R$ {total_final:,.2f}", 0, align='R', fill=True)
    
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFACE PRINCIPAL ---
if os.path.exists(ARQUIVO_LOGO):
    st.sidebar.image(ARQUIVO_LOGO, width=200)

st.title("🏗️ UpDown Pro - Gestão Comercial")
df_materiais = carregar_materiais()
menu = st.sidebar.radio("Menu", ["Novo Orçamento", "Banco de Materiais", "Histórico"])

if menu == "Novo Orçamento":
    with st.expander("👤 1. Dados do Cliente", expanded=True):
        c1, c2, c3 = st.columns([2, 1, 1])
        cliente = c1.text_input("Cliente")
        cnpj = c2.text_input("CNPJ/CPF")
        zap = c3.text_input("WhatsApp (ex: 42999999999)")

    if 'blocos' not in st.session_state: st.session_state.blocos = []

    if st.button("➕ Adicionar Novo Serviço"):
        st.session_state.blocos.append({
            "titulo": "", "descricao": "", "desc_avaria": "", "foto": None,
            "materiais": [], "valor_mo": 0.0, "soma_materiais": 0.0, "total_bloco": 0.0
        })

    remove_idx = []
    for i, bloco in enumerate(st.session_state.blocos):
        with st.container(border=True):
            ct, cd = st.columns([6, 1])
            bloco['titulo'] = ct.text_input(f"Título do Serviço {i+1}", value=bloco['titulo'], key=f"t_{i}")
            if cd.button("🗑️", key=f"del_{i}"): remove_idx.append(i)

            st.markdown("**📸 Diagnóstico Visual**")
            cf1, cf2 = st.columns([1, 2])
            bloco['foto'] = cf1.file_uploader(f"Foto da Avaria {i+1}", type=['jpg','png','jpeg'], key=f"f_{i}")
            bloco['desc_avaria'] = cf2.text_area(f"Descrição da Avaria {i+1}", value=bloco['desc_avaria'], key=f"da_{i}", height=100, placeholder="Ex: Infiltração severa com desplacamento de reboco...")
            
            if bloco['foto']: cf1.image(bloco['foto'], width=150)

            bloco['descricao'] = st.text_area(f"Solução Técnica {i+1}", value=bloco['descricao'], key=f"desc_{i}", placeholder="O que será feito para resolver?")

            # Lógica de Materiais
            st.markdown("**📦 Materiais**")
            cm, cq, ca = st.columns([3, 1, 1])
            mat_sel = cm.selectbox("Item", df_materiais['Material'].unique(), key=f"s_{i}", index=None)
            qtd = cq.number_input("Qtd", 1.0, key=f"q_{i}")
            if ca.button("Add", key=f"add_{i}"):
                if mat_sel:
                    pr = df_materiais[df_materiais['Material'] == mat_sel]['Preco_Unitario'].values[0]
                    bloco['materiais'].append({"nome": mat_sel, "qtd": qtd, "unit": pr, "total": pr*qtd})
                    st.rerun()

            if bloco['materiais']:
                df_b = pd.DataFrame(bloco['materiais'])
                edited_df = st.data_editor(df_b, key=f"ed_{i}", use_container_width=True, hide_index=True)
                bloco['soma_materiais'] = edited_df['total'].sum()
            
            bloco['valor_mo'] = st.number_input(f"Mão de Obra {i+1}", 0.0, value=bloco['valor_mo'], key=f"mo_{i}")
            bloco['total_bloco'] = bloco['soma_materiais'] + bloco['valor_mo']
            st.info(f"Subtotal do Item: R$ {bloco['total_bloco']:,.2f}")

    if remove_idx:
        for x in sorted(remove_idx, reverse=True): del st.session_state.blocos[x]
        st.rerun()

    st.markdown("---")
    total_calc = sum(b['total_bloco'] for b in st.session_state.blocos)
    c1, c2 = st.columns(2)
    txt_com = c1.text_area("Condições Comerciais", "Pagamento: 50% entrada / 50% conclusão.", height=150)
    total_final = c2.number_input("VALOR FINAL COM DESCONTO (R$)", value=float(total_calc))
    obs_f = st.text_input("Observações de Rodapé", "Validade da proposta: 15 dias.")

    if st.button("✅ GERAR PDF E FINALIZAR", type="primary"):
        if not cliente: st.error("Nome do cliente é obrigatório.")
        else:
            hoje = datetime.today().strftime("%d/%m/%Y")
            val = (datetime.today() + timedelta(days=15)).strftime("%d/%m/%Y")
            pdf_bytes = gerar_pdf(cliente, cnpj, hoje, val, st.session_state.blocos, total_calc, total_final, txt_com, obs_f)
            
            link = f"https://wa.me/55{zap}?text={quote(f'Olá {cliente}, segue a proposta da UpDown: R$ {total_final:,.2f}')}" if zap else "#"
            salvar_historico({"Data": hoje, "Cliente": cliente, "Total": total_final, "Link Zap": link})
            
            st.success("Orçamento concluído!")
            st.download_button("⬇️ Baixar Proposta PDF", pdf_bytes, f"Proposta_{cliente}.pdf", "application/pdf")
            if zap: st.link_button("📱 Enviar via WhatsApp", link)

elif menu == "Banco de Materiais":
    st.header("📦 Gerenciamento de Materiais")
    df_edit = st.data_editor(df_materiais, num_rows="dynamic", use_container_width=True)
    if st.button("💾 Salvar Banco de Dados"):
        salvar_materiais(df_edit)
        st.success("Dados atualizados!")

elif menu == "Histórico":
    st.header("📂 Últimos Orçamentos")
    st.dataframe(carregar_historico(), use_container_width=True)
