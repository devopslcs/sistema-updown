import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime, timedelta
import os
from urllib.parse import quote

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sistema UpDown Pro", page_icon="🏗️", layout="wide")

# ARQUIVOS DE DADOS
ARQUIVO_MATERIAIS = 'banco_materiais.csv'
ARQUIVO_HISTORICO = 'historico_orcamentos.csv'
ARQUIVO_LOGO = 'logo_updown.png'

# --- FUNÇÕES DE BANCO DE DADOS ---
def carregar_materiais():
    if not os.path.exists(ARQUIVO_MATERIAIS):
        # Cria arquivo inicial se não existir
        dados = [
            {"Material": "Selante Fibrado (Balde 10kg)", "Preco_Unitario": 950.00},
            {"Material": "Borracha Líquida (Lata 18L)", "Preco_Unitario": 800.00},
            {"Material": "Disco de Corte", "Preco_Unitario": 150.00},
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

# --- GERADOR DE PDF (CORRIGIDO PARA TEXTOS LONGOS) ---
def gerar_pdf(cliente, cnpj, data, validade, blocos, total_calc, total_final, texto_comercial, obs):
    class PDF(FPDF):
        def header(self):
            # Logo no cabeçalho de todas as páginas
            if os.path.exists(ARQUIVO_LOGO):
                self.image(ARQUIVO_LOGO, 10, 8, 40)
            self.ln(25)

    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15) # Garante quebra de página automática
    pdf.add_page()
    
    # Cabeçalho do Documento
    pdf.set_y(30) # Garante que comece abaixo da logo
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, txt="PROPOSTA TÉCNICA E COMERCIAL", ln=True, align='C')
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(190, 6, txt="UPDOWN SERVIÇOS DE ALTA PERFORMANCE | CNPJ: 36.130.036/0001-37", ln=True, align='C')
    pdf.ln(10)
    
    # Cliente
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 8, txt="DADOS DO CLIENTE", ln=True, align='L')
    pdf.set_font("Arial", size=11)
    pdf.cell(190, 6, txt=f"Cliente: {cliente}", ln=True)
    pdf.cell(190, 6, txt=f"CNPJ/CPF: {cnpj}", ln=True)
    pdf.cell(190, 6, txt=f"Data: {data}  |  Validade: {validade}", ln=True)
    pdf.ln(10)
    
    # --- BLOCOS DE SERVIÇO ---
    for i, bloco in enumerate(blocos, 1):
        # Título do Serviço (Com Multi_cell para não estourar se for titulo gigante)
        pdf.set_font("Arial", 'B', 14)
        pdf.set_fill_color(230, 230, 230)
        # Salva posição Y
        y_antes = pdf.get_y()
        # Imprime titulo
        pdf.multi_cell(190, 10, txt=f"ITEM {i}. {bloco['titulo'].upper()}", align='L', fill=True)
        pdf.ln(2)
        
        # Descrição (Multi_cell garante quebra de linha)
        pdf.set_font("Arial", size=11)
        descricao_limpa = bloco['descricao'].encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(190, 6, txt=descricao_limpa)
        pdf.ln(5)
        
        # Tabela de Materiais do Bloco
        if bloco['materiais']:
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(190, 6, "Materiais Inclusos neste item:", ln=True)
            
            # Cabeçalho Tabela
            pdf.set_fill_color(245, 245, 245)
            pdf.cell(110, 6, "Material", 1, 0, 'L', True)
            pdf.cell(20, 6, "Qtd", 1, 0, 'C', True)
            pdf.cell(30, 6, "Unit", 1, 0, 'C', True)
            pdf.cell(30, 6, "Total", 1, 1, 'C', True) # ln=1 quebra linha
            
            pdf.set_font("Arial", size=10)
            for mat in bloco['materiais']:
                # Trata nome do material para não quebrar tabela se for gigante
                nome_full = mat['nome'].encode('latin-1', 'replace').decode('latin-1')
                nome_curto = (nome_full[:55] + '...') if len(nome_full) > 55 else nome_full
                
                pdf.cell(110, 6, nome_curto, 1)
                pdf.cell(20, 6, str(mat['qtd']), 1, 0, 'C')
                pdf.cell(30, 6, f"{mat['unit']:,.2f}", 1, 0, 'R')
                pdf.cell(30, 6, f"{mat['total']:,.2f}", 1, 1, 'R')
            pdf.ln(2)

        # Valores do Bloco
        pdf.set_font("Arial", size=11)
        pdf.cell(150, 6, "Total Materiais:", 0, align='R')
        pdf.cell(40, 6, f"R$ {bloco['soma_materiais']:,.2f}", 0, align='R')
        pdf.ln()
        
        pdf.cell(150, 6, "Mão de Obra (c/ NF):", 0, align='R')
        pdf.cell(40, 6, f"R$ {bloco['valor_mo']:,.2f}", 0, align='R')
        pdf.ln()
        
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(150, 8, f"TOTAL DO SERVIÇO {i}:", 0, align='R')
        pdf.cell(40, 8, f"R$ {bloco['total_bloco']:,.2f}", 0, align='R')
        pdf.ln(10)
    
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    # --- PROPOSTA COMERCIAL ---
    # Verifica se cabe na página, senão cria nova
    if pdf.get_y() > 220:
        pdf.add_page()

    pdf.set_font("Arial", 'B', 14)
    pdf.set_fill_color(220, 220, 220)
    pdf.cell(190, 10, txt="  PROPOSTA COMERCIAL", ln=True, align='L', fill=True)
    pdf.ln(5)
    
    # Texto Comercial (Multi_cell para textos longos)
    pdf.set_font("Arial", size=11)
    texto_com_limpo = texto_comercial.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(190, 6, txt=texto_com_limpo)
    pdf.ln(5)
    
    # Valores Finais
    if total_final != total_calc:
        pdf.set_font("Arial", size=11)
        pdf.cell(140, 8, "Soma dos Serviços:", 0, align='R')
        pdf.cell(50, 8, f"R$ {total_calc:,.2f}", 0, align='R')
        pdf.ln()
        
        diff = total_final - total_calc
        txt_ajuste = "Desconto Aplicado:" if diff < 0 else "Ajuste:"
        pdf.cell(140, 8, txt_ajuste, 0, align='R')
        pdf.cell(50, 8, f"R$ {diff:,.2f}", 0, align='R')
        pdf.ln(2)

    pdf.set_font("Arial", 'B', 18)
    pdf.cell(140, 12, "VALOR FINAL:", 0, align='R')
    pdf.cell(50, 12, f"R$ {total_final:,.2f}", 0, align='R')
    pdf.ln(10)
    
    # Observações Rodapé
    pdf.set_font("Arial", size=9)
    obs_limpa = obs.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(190, 5, txt=f"Obs: {obs_limpa}")
    
    # Rodapé Final
    pdf.ln(15)
    pdf.cell(190, 5, "__________________________________________________", ln=True, align='C')
    pdf.cell(190, 5, "UPDOWN SERVICOS DE ALTA PERFORMANCE", ln=True, align='C')
    
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFACE ---
st.sidebar.image(ARQUIVO_LOGO, width=200) if os.path.exists(ARQUIVO_LOGO) else None
st.title("🏗️ Sistema UpDown - Comercial")
st.markdown("---")

df_materiais = carregar_materiais()

# MENU
menu = st.sidebar.radio("Menu", ["Novo Orçamento", "Banco de Materiais", "Histórico"])

# ==============================================================================
# TELA 1: NOVO ORÇAMENTO (BLOCO A BLOCO)
# ==============================================================================
if menu == "Novo Orçamento":
    
    # 1. DADOS
    with st.expander("👤 1. Dados do Cliente", expanded=True):
        c1, c2, c3 = st.columns([2, 1, 1])
        cliente = c1.text_input("Cliente")
        cnpj = c2.text_input("CNPJ/CPF")
        zap = c3.text_input("WhatsApp")

    if 'blocos' not in st.session_state: st.session_state.blocos = []

    # 2. BLOCOS DE SERVIÇO
    st.markdown("### 📋 2. Serviços a Executar")
    if st.button("➕ Adicionar Novo Serviço"):
        st.session_state.blocos.append({
            "titulo": "", "descricao": "", "materiais": [], 
            "valor_mo": 0.0, "soma_materiais": 0.0, "total_bloco": 0.0
        })

    remove_idx = []
    for i, bloco in enumerate(st.session_state.blocos):
        st.markdown("---")
        with st.container(border=True):
            c_tit, c_del = st.columns([6, 1])
            bloco['titulo'] = c_tit.text_input(f"Título do Serviço {i+1}", value=bloco['titulo'], placeholder="Ex: Impermeabilização Janelas", key=f"t_{i}")
            if c_del.button("🗑️", key=f"d_{i}"): remove_idx.append(i)
            
            # DESCRIÇÃO GRANDE (TEXT AREA)
            bloco['descricao'] = st.text_area(f"Descrição Técnica {i+1}", value=bloco['descricao'], height=150, key=f"desc_{i}", help="Escreva o texto longo aqui. Ele será ajustado automaticamente no PDF.")
            
            # MATERIAIS DO BLOCO
            st.markdown(f"**Materiais deste serviço:**")
            c_m, c_q, c_a = st.columns([3, 1, 1])
            if not df_materiais.empty:
                mat_sel = c_m.selectbox("Item", df_materiais['Material'].unique(), key=f"s_{i}")
                try: pr = df_materiais[df_materiais['Material'] == mat_sel]['Preco_Unitario'].values[0]
                except: pr = 0.0
                qtd = c_q.number_input("Qtd", 1, key=f"q_{i}")
                if c_a.button("Add", key=f"add_{i}"):
                    bloco['materiais'].append({"nome": mat_sel, "qtd": qtd, "unit": pr, "total": pr*qtd})
                    st.rerun()

            if bloco['materiais']:
                df_b = pd.DataFrame(bloco['materiais'])
                st.dataframe(df_b, use_container_width=True, hide_index=True)
                bloco['soma_materiais'] = df_b['total'].sum()
                if st.button("Limpar Materiais", key=f"lp_{i}"):
                    bloco['materiais'] = []
                    st.rerun()
            else:
                bloco['soma_materiais'] = 0.0

            # MÃO DE OBRA
            c_mo, c_tot = st.columns(2)
            bloco['valor_mo'] = c_mo.number_input(f"Mão de Obra (c/ NF) - Serviço {i+1}", 0.0, step=100.0, value=bloco['valor_mo'], key=f"mo_{i}")
            bloco['total_bloco'] = bloco['soma_materiais'] + bloco['valor_mo']
            c_tot.metric(f"Total Serviço {i+1}", f"R$ {bloco['total_bloco']:,.2f}")

    if remove_idx:
        for x in sorted(remove_idx, reverse=True): del st.session_state.blocos[x]
        st.rerun()

    # 3. PROPOSTA COMERCIAL
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
    st.header("📦 Banco de Materiais (Salvo Automaticamente)")
    st.info("Adicione ou edite materiais aqui. As alterações são salvas automaticamente no sistema.")

    df_edit = st.data_editor(
        df_materiais,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Material": st.column_config.TextColumn("Nome do Material", width="large", required=True),
            "Preco_Unitario": st.column_config.NumberColumn("Preço Unitário (R$)", format="R$ %.2f")
        },
        key="editor"
    )

    if st.button("💾 Salvar Alterações"):
        salvar_materiais(df_edit)
        st.success("Banco de dados atualizado!")
        st.rerun()

    st.markdown("---")
    with st.expander("☁️ Backup e Restauração (Para Segurança)"):
        st.warning("Use isso se mudar de computador ou se o site reiniciar.")
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
