import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime, timedelta
import os
from urllib.parse import quote
from PIL import Image

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sistema UpDown Pro", page_icon="🏗️", layout="wide")

# ARQUIVOS DE DADOS E IMAGENS
ARQUIVO_MATERIAIS = 'banco_materiais.csv'
ARQUIVO_HISTORICO = 'historico_orcamentos.csv'
ARQUIVO_LOGO = 'Logo sem fundo.png' # Certifique-se que o arquivo existe com este nome exato
ARQUIVO_WATERMARK = 'watermark_temp.png'

# --- FUNÇÃO AUXILIAR: GERAR MARCA D'ÁGUA TRANSPARENTE ---
def preparar_marca_dagua():
    # Só gera se o logo existe e a marca d'água ainda não foi criada
    if os.path.exists(ARQUIVO_LOGO):
        if not os.path.exists(ARQUIVO_WATERMARK):
            try:
                img = Image.open(ARQUIVO_LOGO).convert("RGBA")
                datas = img.getdata()
                new_data = []
                # Ajusta a transparência (Alpha) para 10% (0.10)
                for item in datas:
                    new_data.append((item[0], item[1], item[2], int(item[3] * 0.10)))
                img.putdata(new_data)
                img.save(ARQUIVO_WATERMARK, "PNG")
            except Exception as e:
                st.error(f"Erro ao criar marca d'água: {e}")

# --- FUNÇÕES DE BANCO DE DADOS ---
def carregar_materiais():
    if not os.path.exists(ARQUIVO_MATERIAIS):
        dados = [
            {"Material": "Selante Fibrado (Balde 10kg)", "Descricao": "Cor Cinza", "Preco_Unitario": 950.00},
            {"Material": "Borracha Líquida (Lata 18L)", "Descricao": "Impermeabilizante", "Preco_Unitario": 800.00},
        ]
        df = pd.DataFrame(dados)
        df.to_csv(ARQUIVO_MATERIAIS, index=False)
        return df
    
    df = pd.read_csv(ARQUIVO_MATERIAIS)
    if "Descricao" not in df.columns:
        df["Descricao"] = ""
        cols = ["Material", "Descricao", "Preco_Unitario"]
        cols = [c for c in cols if c in df.columns] + [c for c in df.columns if c not in cols]
        df = df[cols]
    return df

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

# --- CLASSE PDF (HEADER COM LOGO E MARCA D'ÁGUA) ---
class PDF(FPDF):
    def header(self):
        # 1. MARCA D'ÁGUA (Fundo Centralizado)
        # Colocamos primeiro para ficar atrás do texto
        if os.path.exists(ARQUIVO_WATERMARK):
            # A4 largura = 210mm. Imagem w=120. (210-120)/2 = 45 (centralizado)
            # y=80 para ficar no meio da folha verticalmente
            self.image(ARQUIVO_WATERMARK, x=45, y=80, w=120)
        
        # 2. LOGO CABEÇALHO (Canto Superior Esquerdo)
        if os.path.exists(ARQUIVO_LOGO):
            self.image(ARQUIVO_LOGO, x=10, y=8, w=30)
        
        # 3. TEXTOS DO CABEÇALHO (Ao lado do Logo)
        self.set_y(12)
        self.set_x(42) # Move para a direita do logo (10+30+margem)
        self.set_font("Arial", 'B', 14)
        self.cell(0, 5, "UPDOWN - SERVIÇOS DE ALTA PERFORMANCE", ln=True, align='L')
        
        self.set_x(42)
        self.set_font("Arial", '', 10)
        self.cell(0, 5, "CNPJ: 36.130.036/0001-37", ln=True, align='L')
        
        # Linha separadora
        self.ln(12)
        self.set_draw_color(200, 200, 200) # Cinza claro
        self.line(10, 32, 200, 32)
        self.ln(5)

# --- GERADOR DE PDF ---
def gerar_pdf(cliente, cnpj, data, validade, blocos, total_calc, total_final, texto_comercial, obs):
    # Garante que a marca d'água existe antes de gerar o PDF
    preparar_marca_dagua()
    
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, txt="PROPOSTA TÉCNICA E COMERCIAL", ln=True, align='C')
    pdf.ln(5)
    
    # Dados do Cliente
    pdf.set_fill_color(245, 245, 245)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(190, 8, "  DADOS DO CLIENTE:", ln=True, fill=True)
    pdf.set_font("Arial", '', 11)
    pdf.cell(190, 6, f"  Cliente: {cliente}", ln=True)
    pdf.cell(190, 6, f"  CNPJ/CPF: {cnpj}", ln=True)
    pdf.cell(190, 6, f"  Data: {data}   |   Validade: {validade}", ln=True)
    pdf.ln(5)
    
    # Blocos de Serviço
    for i, bloco in enumerate(blocos, 1):
        pdf.set_font("Arial", 'B', 13)
        pdf.set_fill_color(255, 204, 102) # Laranja UpDown
        pdf.set_text_color(0, 0, 0)
        
        # Quebra de página se estiver no fim
        if pdf.get_y() > 240: pdf.add_page()
        
        pdf.cell(190, 8, txt=f"  ITEM {i}. {bloco['titulo'].upper()}", ln=True, align='L', fill=True)
        pdf.ln(2)
        
        # Descrição
        pdf.set_font("Arial", '', 11)
        desc_limpa = bloco['descricao'].encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(190, 6, txt=desc_limpa)
        pdf.ln(3)
        
        # Tabela de Materiais
        if bloco['materiais']:
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(190, 6, "Materiais Inclusos:", ln=True)
            pdf.set_fill_color(240, 240, 240)
            pdf.cell(110, 6, "Material", 1, 0, 'L', True)
            pdf.cell(20, 6, "Qtd", 1, 0, 'C', True)
            pdf.cell(30, 6, "Unit", 1, 0, 'C', True)
            pdf.cell(30, 6, "Total", 1, 1, 'C', True)
            
            pdf.set_font("Arial", '', 10)
            for mat in bloco['materiais']:
                nome = mat['nome'].encode('latin-1', 'replace').decode('latin-1')
                nome = (nome[:55] + '...') if len(nome) > 55 else nome
                pdf.cell(110, 6, nome, 1)
                pdf.cell(20, 6, str(mat['qtd']), 1, 0, 'C')
                pdf.cell(30, 6, f"{mat['unit']:,.2f}", 1, 0, 'R')
                pdf.cell(30, 6, f"{mat['total']:,.2f}", 1, 1, 'R')
            pdf.ln(2)

        # Totais do Bloco
        pdf.set_font("Arial", '', 11)
        pdf.cell(150, 6, "Total Materiais:", 0, align='R')
        pdf.cell(40, 6, f"R$ {bloco['soma_materiais']:,.2f}", 0, align='R')
        pdf.ln()
        pdf.cell(150, 6, "Mão de Obra (c/ NF):", 0, align='R')
        pdf.cell(40, 6, f"R$ {bloco['valor_mo']:,.2f}", 0, align='R')
        pdf.ln()
        
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(150, 8, f"TOTAL DO SERVIÇO {i}:", 0, align='R')
        pdf.cell(40, 8, f"R$ {bloco['total_bloco']:,.2f}", 0, align='R')
        pdf.ln(8)
        
        # Linha separadora
        pdf.set_draw_color(220, 220, 220)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)

    # Proposta Comercial
    if pdf.get_y() > 200: pdf.add_page()

    pdf.set_font("Arial", 'B', 13)
    pdf.set_fill_color(50, 50, 50) # Cinza Escuro
    pdf.set_text_color(255, 255, 255) # Branco
    pdf.cell(190, 8, txt="  PROPOSTA COMERCIAL", ln=True, align='L', fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)
    
    pdf.set_font("Arial", '', 11)
    txt_com_limpo = texto_comercial.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(190, 6, txt=txt_com_limpo)
    pdf.ln(5)
    
    # Ajuste de Valores
    if total_final != total_calc:
        pdf.set_font("Arial", '', 11)
        pdf.cell(140, 8, "Soma dos Serviços:", 0, align='R')
        pdf.cell(50, 8, f"R$ {total_calc:,.2f}", 0, align='R')
        pdf.ln()
        diff = total_final - total_calc
        txt_ajuste = "Desconto:" if diff < 0 else "Ajuste:"
        pdf.cell(140, 8, txt_ajuste, 0, align='R')
        pdf.cell(50, 8, f"R$ {diff:,.2f}", 0, align='R')
        pdf.ln(2)

    # Valor Final
    pdf.set_font("Arial", 'B', 16)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(140, 12, "VALOR FINAL:", 0, align='R', fill=True)
    pdf.cell(50, 12, f"R$ {total_final:,.2f}", 0, align='R', fill=True)
    pdf.ln(10)
    
    # Obs Rodapé
    pdf.set_font("Arial", 'I', 9)
    obs_limpa = obs.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(190, 5, txt=f"Obs: {obs_limpa}")
    
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFACE PRINCIPAL ---
if os.path.exists(ARQUIVO_LOGO):
    st.sidebar.image(ARQUIVO_LOGO, width=200)
else:
    # Aviso caso o logo não seja encontrado (pra te ajudar a debugar)
    st.sidebar.warning("Logo não encontrado! Verifique se 'Logo sem fundo.png' está na pasta.")

st.title("🏗️ Sistema UpDown - Comercial")
st.markdown("---")

df_materiais = carregar_materiais()
menu = st.sidebar.radio("Menu", ["Novo Orçamento", "Banco de Materiais", "Histórico"])

# ==============================================================================
# TELA 1: NOVO ORÇAMENTO
# ==============================================================================
if menu == "Novo Orçamento":
    with st.expander("👤 1. Dados do Cliente", expanded=True):
        c1, c2, c3 = st.columns([2, 1, 1])
        cliente = c1.text_input("Cliente")
        cnpj = c2.text_input("CNPJ/CPF")
        zap = c3.text_input("WhatsApp")

    if 'blocos' not in st.session_state: st.session_state.blocos = []

    st.markdown("### 📋 2. Serviços a Executar")
    if st.button("➕ Adicionar Novo Serviço"):
        st.session_state.blocos.append({
            "titulo": "", "descricao": "", "materiais": [], 
            "valor_mo": 0.0, "soma_materiais": 0.0, "total_bloco": 0.0
        })

    remove_idx = []
    
    # LOOP DE BLOCOS
    for i, bloco in enumerate(st.session_state.blocos):
        st.markdown("---")
        with st.container(border=True):
            c_tit, c_del = st.columns([6, 1])
            bloco['titulo'] = c_tit.text_input(f"Título do Serviço {i+1}", value=bloco['titulo'], placeholder="Ex: Impermeabilização Janelas", key=f"t_{i}")
            if c_del.button("🗑️ Serviço", key=f"d_{i}", help="Remover este serviço inteiro"): 
                remove_idx.append(i)
            
            bloco['descricao'] = st.text_area(f"Descrição Técnica {i+1}", value=bloco['descricao'], height=100, key=f"desc_{i}")
            
            st.markdown(f"**Materiais deste serviço:**")
            
            # SELETOR DE ADIÇÃO (DROPDOWN)
            c_m, c_q, c_a = st.columns([3, 1, 1])
            if not df_materiais.empty:
                mat_sel = c_m.selectbox("Adicionar Item", df_materiais['Material'].unique(), key=f"s_{i}", index=None, placeholder="Selecione para adicionar...")
                
                # Pega preço
                pr = 0.0
                if mat_sel:
                    try: pr = df_materiais[df_materiais['Material'] == mat_sel]['Preco_Unitario'].values[0]
                    except: pass
                
                qtd = c_q.number_input("Qtd", 1, key=f"q_{i}")
                
                if c_a.button("Add", key=f"add_{i}"):
                    if mat_sel:
                        # Adiciona à lista
                        bloco['materiais'].append({"nome": mat_sel, "qtd": qtd, "unit": pr, "total": pr*qtd})
                        st.rerun()
                    else:
                        st.warning("Selecione um material.")

            # TABELA EDITÁVEL INTELIGENTE
            soma_temp = 0.0
            if bloco['materiais']:
                df_b = pd.DataFrame(bloco['materiais'])
                
                edited_df = st.data_editor(
                    df_b,
                    column_config={
                        "nome": st.column_config.TextColumn("Material", disabled=True),
                        "qtd": st.column_config.NumberColumn("Qtd", min_value=0.01, step=0.01, required=True),
                        "unit": st.column_config.NumberColumn("Unit", format="R$ %.2f", disabled=True),
                        "total": st.column_config.NumberColumn("Total", format="R$ %.2f", disabled=True)
                    },
                    num_rows="dynamic",
                    use_container_width=True,
                    key=f"editor_{i}",
                    hide_index=True
                )
                
                # LÓGICA DE ATUALIZAÇÃO E RECÁLCULO
                new_materials = []
                for idx, row in edited_df.iterrows():
                    if pd.isna(row['nome']) or row['nome'] == "": continue
                    new_total = row['unit'] * row['qtd']
                    new_materials.append({
                        "nome": row['nome'], "qtd": row['qtd'], "unit": row['unit'], "total": new_total
                    })
                    soma_temp += new_total
                
                if new_materials != bloco['materiais']:
                    bloco['materiais'] = new_materials
                    bloco['soma_materiais'] = soma_temp
                    st.rerun()
                else:
                    bloco['soma_materiais'] = soma_temp
            else:
                bloco['soma_materiais'] = 0.0

            # FECHAMENTO DO BLOCO
            c_mo, c_tot = st.columns(2)
            bloco['valor_mo'] = c_mo.number_input(f"Mão de Obra (c/ NF) - Serviço {i+1}", 0.0, step=100.0, value=bloco['valor_mo'], key=f"mo_{i}")
            bloco['total_bloco'] = bloco['soma_materiais'] + bloco['valor_mo']
            c_tot.metric(f"Total Serviço {i+1}", f"R$ {bloco['total_bloco']:,.2f}")

    if remove_idx:
        for x in sorted(remove_idx, reverse=True): del st.session_state.blocos[x]
        st.rerun()

    st.markdown("---")
    st.header("💰 3. Proposta Comercial")
    
    total_calc = sum(b['total_bloco'] for b in st.session_state.blocos)
    
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"Soma dos Serviços: R$ {total_calc:,.2f}")
        txt_com = st.text_area("Texto da Proposta Comercial", "Condições de Pagamento:\n- 50% entrada / 50% entrega.\n\nO valor contempla material e mão de obra conforme descrito.", height=150)
    
    with col2:
        st.success("Valor Final para o Cliente")
        total_final = st.number_input("VALOR FINAL (R$)", value=float(total_calc), step=100.0)
    
    obs = st.text_input("Rodapé (Obs)", "Validade: 15 dias.")

    st.markdown("---")
    if st.button("✅ GERAR PROPOSTA PDF", type="primary"):
        if not cliente:
            st.error("Nome do Cliente obrigatório.")
        elif not st.session_state.blocos:
            st.error("Adicione serviços.")
        else:
            hoje = datetime.today().strftime("%d/%m/%Y")
            val = (datetime.today() + timedelta(days=15)).strftime("%d/%m/%Y")
            
            pdf_bytes = gerar_pdf(cliente, cnpj, hoje, val, st.session_state.blocos, total_calc, total_final, txt_com, obs)
            
            link = f"https://wa.me/55{zap}?text={quote(f'Olá {cliente}, proposta: R$ {total_final:,.2f}')}" if zap else "#"
            salvar_historico({"Data": hoje, "Cliente": cliente, "Total": total_final, "Link Zap": link})
            
            st.success("Gerado com sucesso!")
            c1, c2 = st.columns(2)
            c1.download_button("⬇️ Baixar PDF", pdf_bytes, f"Proposta_{cliente}.pdf", "application/pdf")
            if zap: c2.link_button("📱 WhatsApp", link)

# ==============================================================================
# TELA 2: BANCO DE MATERIAIS
# ==============================================================================
elif menu == "Banco de Materiais":
    st.header("📦 Banco de Materiais")
    st.info("Gerencie seus materiais aqui.")

    df_edit = st.data_editor(
        df_materiais,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Material": st.column_config.TextColumn("Nome", width="medium", required=True),
            "Descricao": st.column_config.TextColumn("Descrição", width="large"),
            "Preco_Unitario": st.column_config.NumberColumn("Preço (R$)", format="R$ %.2f")
        },
        key="editor"
    )

    if st.button("💾 Salvar Alterações"):
        salvar_materiais(df_edit)
        st.success("Salvo!")
        st.rerun()

    st.markdown("---")
    with st.expander("☁️ Backup e Restauração"):
        csv = df_materiais.to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Baixar Backup", csv, "backup_materiais.csv", "text/csv")
        up = st.file_uploader("Restaurar Backup", type=["csv"])
        if up:
            if st.button("Carregar"):
                try:
                    df_up = pd.read_csv(up)
                    salvar_materiais(df_up)
                    st.success("Restaurado!")
                    st.rerun()
                except: st.error("Erro no arquivo.")

# ==============================================================================
# TELA 3: HISTÓRICO
# ==============================================================================
elif menu == "Histórico":
    st.header("📂 Histórico")
    st.dataframe(carregar_historico(), use_container_width=True)
