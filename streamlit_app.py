import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime, timedelta
import os
from urllib.parse import quote

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sistema UpDown Modular", page_icon="🏗️", layout="wide")

# ARQUIVOS
ARQUIVO_MATERIAIS = 'banco_materiais.csv'
ARQUIVO_HISTORICO = 'historico_orcamentos.csv'
ARQUIVO_LOGO = 'logo_updown.png'

# --- FUNÇÕES DE BANCO DE DADOS ---
def carregar_materiais():
    if not os.path.exists(ARQUIVO_MATERIAIS):
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

# --- GERADOR DE PDF MODULAR ---
def gerar_pdf_modular(cliente, cnpj, data, validade, blocos_servicos, total_geral_orcamento, obs):
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
    pdf.cell(190, 10, txt="PROPOSTA TÉCNICA E COMERCIAL", ln=True, align='C')
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(190, 10, txt="UPDOWN SERVICOS DE ALTA PERFORMANCE | CNPJ: 36.130.036/0001-37", ln=True, align='C')
    pdf.ln(10)
    
    # Cliente
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 8, txt="DADOS DO CLIENTE", ln=True, align='L')
    pdf.set_font("Arial", size=11)
    pdf.cell(190, 6, txt=f"Cliente: {cliente}", ln=True)
    pdf.cell(190, 6, txt=f"CNPJ/CPF: {cnpj}", ln=True)
    pdf.cell(190, 6, txt=f"Data: {data}  |  Validade: {validade}", ln=True)
    pdf.ln(10)
    
    # --- LOOP DOS BLOCOS DE SERVIÇO ---
    for idx, bloco in enumerate(blocos_servicos, 1):
        # Título do Bloco
        pdf.set_font("Arial", 'B', 14)
        pdf.set_fill_color(230, 230, 230) # Cinza
        pdf.cell(190, 10, txt=f"  ITEM {idx}. {bloco['titulo'].upper()}", ln=True, align='L', fill=True)
        pdf.ln(3)
        
        # Descrição Técnica
        pdf.set_font("Arial", size=11)
        pdf.multi_cell(190, 6, txt=bloco['descricao'].encode('latin-1', 'replace').decode('latin-1'))
        pdf.ln(5)
        
        # Tabela de Materiais (Se houver)
        if bloco['materiais']:
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(190, 6, "Lista de Materiais Inclusos:", ln=True)
            
            pdf.cell(110, 6, "Material", 1)
            pdf.cell(20, 6, "Qtd", 1, align='C')
            pdf.cell(30, 6, "Vl. Unit", 1, align='C')
            pdf.cell(30, 6, "Total", 1, align='C')
            pdf.ln()
            
            pdf.set_font("Arial", size=10)
            for mat in bloco['materiais']:
                nome = mat['nome'].encode('latin-1', 'replace').decode('latin-1')
                pdf.cell(110, 6, nome, 1)
                pdf.cell(20, 6, str(mat['qtd']), 1, align='C')
                pdf.cell(30, 6, f"{mat['unit']:,.2f}", 1, align='R')
                pdf.cell(30, 6, f"{mat['total']:,.2f}", 1, align='R')
                pdf.ln()
            pdf.ln(2)
        
        # Fechamento do Bloco (Valores Específicos)
        pdf.set_font("Arial", size=11)
        pdf.cell(150, 6, "Total Materiais:", 0, align='R')
        pdf.cell(40, 6, f"R$ {bloco['soma_materiais']:,.2f}", 0, align='R')
        pdf.ln()
        
        pdf.cell(150, 6, "Mão de Obra (c/ NF):", 0, align='R')
        pdf.cell(40, 6, f"R$ {bloco['valor_mo']:,.2f}", 0, align='R')
        pdf.ln()
        
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(150, 8, f"TOTAL DO SERVIÇO {idx}:", 0, align='R')
        pdf.cell(40, 8, f"R$ {bloco['total_bloco']:,.2f}", 0, align='R')
        pdf.ln(10) # Espaço para o próximo bloco

    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    # --- TOTAL GERAL ---
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(140, 10, "VALOR TOTAL DA PROPOSTA:", 0, align='R')
    pdf.set_text_color(0, 0, 128) # Azul escuro
    pdf.cell(50, 10, f"R$ {total_geral_orcamento:,.2f}", 0, align='R')
    pdf.set_text_color(0, 0, 0)
    pdf.ln(15)
    
    # Observações
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 8, "OBSERVAÇÕES GERAIS:", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.multi_cell(0, 6, txt=obs.encode('latin-1', 'replace').decode('latin-1'))
    
    # Rodapé
    pdf.ln(20)
    pdf.cell(190, 5, "__________________________________________________", ln=True, align='C')
    pdf.cell(190, 5, "UPDOWN SERVICOS DE ALTA PERFORMANCE", ln=True, align='C')
    
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFACE ---
st.sidebar.image(ARQUIVO_LOGO, width=200) if os.path.exists(ARQUIVO_LOGO) else None
st.title("🏗️ Sistema UpDown Modular")
st.markdown("---")

df_materiais = carregar_materiais()
menu = st.sidebar.radio("Navegação", ["Criar Orçamento Modular", "Banco de Materiais", "Histórico"])

# ==============================================================================
# TELA 1: ORÇAMENTO MODULAR (BLOCOS)
# ==============================================================================
if menu == "Criar Orçamento Modular":
    
    # 1. Dados do Cliente
    with st.expander("👤 Dados do Cliente", expanded=True):
        c1, c2, c3 = st.columns([2, 1, 1])
        cliente = c1.text_input("Cliente")
        cnpj = c2.text_input("CNPJ/CPF")
        zap = c3.text_input("WhatsApp")

    # Inicializa a lista de blocos se não existir
    if 'blocos_servico' not in st.session_state:
        st.session_state.blocos_servico = []

    st.markdown("### 📋 Serviços e Materiais")
    
    # BOTÃO PARA ADICIONAR NOVO BLOCO VAZIO
    if st.button("➕ Adicionar Novo Bloco de Serviço"):
        st.session_state.blocos_servico.append({
            "titulo": "",
            "descricao": "",
            "materiais": [], # Lista de materiais deste bloco
            "valor_mo": 0.0,
            "soma_materiais": 0.0,
            "total_bloco": 0.0
        })
    
    # --- LOOP PARA RENDERIZAR CADA BLOCO ---
    blocos_para_remover = []
    
    for i, bloco in enumerate(st.session_state.blocos_servico):
        st.markdown(f"---")
        with st.container(border=True):
            col_titulo, col_del = st.columns([5, 1])
            
            # Título do Bloco
            with col_titulo:
                bloco['titulo'] = st.text_input(f"Título do Serviço {i+1}", value=bloco['titulo'], placeholder="Ex: Impermeabilização de Janelas", key=f"titulo_{i}")
            
            # Botão de Excluir Bloco
            with col_del:
                if st.button("🗑️ Remover", key=f"del_bloco_{i}", type="secondary"):
                    blocos_para_remover.append(i)

            # Descrição do Serviço
            bloco['descricao'] = st.text_area(f"Descrição Técnica (Serviço {i+1})", value=bloco['descricao'], height=100, key=f"desc_{i}", placeholder="1.1 Remoção do selante...\n1.2 Aplicação nova...")

            # --- ÁREA DE MATERIAIS DESTE BLOCO ---
            st.markdown(f"**Materiais para: {bloco['titulo'] if bloco['titulo'] else 'este serviço'}**")
            
            c_mat, c_qtd, c_add = st.columns([3, 1, 1])
            
            # Seleção de Material (Puxa do Banco)
            if not df_materiais.empty:
                mat_selecionado = c_mat.selectbox("Material", df_materiais['Material'].unique(), key=f"sel_mat_{i}")
                
                try:
                    preco_base = df_materiais[df_materiais['Material'] == mat_selecionado]['Preco_Unitario'].values[0]
                except:
                    preco_base = 0.0
                
                qtd_mat = c_qtd.number_input("Qtd", 1, key=f"qtd_mat_{i}")
                
                if c_add.button("Add Material", key=f"btn_add_mat_{i}"):
                    total_item = preco_base * qtd_mat
                    bloco['materiais'].append({
                        "nome": mat_selecionado,
                        "qtd": qtd_mat,
                        "unit": preco_base,
                        "total": total_item
                    })
                    st.rerun()

            # Tabela de Materiais deste bloco
            soma_mat_bloco = 0.0
            if bloco['materiais']:
                df_bloco = pd.DataFrame(bloco['materiais'])
                st.dataframe(df_bloco, use_container_width=True, hide_index=True)
                soma_mat_bloco = df_bloco['total'].sum()
                
                # Botão limpar materiais deste bloco
                if st.button("Limpar Materiais", key=f"clean_mat_{i}"):
                    bloco['materiais'] = []
                    st.rerun()
            
            bloco['soma_materiais'] = soma_mat_bloco

            # --- FECHAMENTO DESTE BLOCO ---
            c_mo, c_total = st.columns(2)
            bloco['valor_mo'] = c_mo.number_input(f"Mão de Obra (Serviço {i+1}) R$", min_value=0.0, step=100.0, value=bloco['valor_mo'], key=f"mo_{i}")
            
            bloco['total_bloco'] = soma_mat_bloco + bloco['valor_mo']
            
            c_total.metric(f"Total Serviço {i+1}", f"R$ {bloco['total_bloco']:,.2f}")

    # Remove blocos se solicitado
    if blocos_para_remover:
        for index in sorted(blocos_para_remover, reverse=True):
            del st.session_state.blocos_servico[index]
        st.rerun()

    # --- FECHAMENTO GERAL DO ORÇAMENTO ---
    st.markdown("---")
    st.header("🏁 Fechamento Geral")
    
    total_geral_orcamento = sum(b['total_bloco'] for b in st.session_state.blocos_servico)
    
    col_fin1, col_fin2 = st.columns([1, 2])
    
    with col_fin1:
        st.metric("VALOR TOTAL DA PROPOSTA", f"R$ {total_geral_orcamento:,.2f}")
    
    with col_fin2:
        obs = st.text_area("Observações Finais", "Validade da Proposta: 15 dias.\nPagamento: A combinar.")

    if st.button("✅ GERAR PDF COMPLETO", type="primary"):
        if not cliente:
            st.error("Preencha o nome do cliente!")
        elif not st.session_state.blocos_servico:
            st.error("Adicione pelo menos um bloco de serviço!")
        else:
            hoje = datetime.today().strftime("%d/%m/%Y")
            validade = (datetime.today() + timedelta(days=15)).strftime("%d/%m/%Y")
            
            pdf_bytes = gerar_pdf_modular(cliente, cnpj, hoje, validade, st.session_state.blocos_servico, total_geral_orcamento, obs)
            
            # Salva Histórico
            link_zap = f"https://wa.me/55{zap}?text={quote(f'Olá {cliente}, segue proposta. Total: R$ {total_geral_orcamento:,.2f}')}" if zap else "#"
            salvar_historico({"Data": hoje, "Cliente": cliente, "Total": total_geral_orcamento, "Link Zap": link_zap})
            
            st.success("Orçamento Gerado!")
            st.download_button("⬇️ Baixar PDF", pdf_bytes, f"Proposta_{cliente}.pdf", "application/pdf")


# ==============================================================================
# TELA 2: BANCO DE MATERIAIS
# ==============================================================================
elif menu == "Banco de Materiais":
    st.header("📦 Gerenciar Banco de Materiais")
    
    df_editado = st.data_editor(
        df_materiais,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Material": st.column_config.TextColumn("Nome", width="large", required=True),
            "Preco_Unitario":
