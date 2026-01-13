import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime, timedelta
import os
from urllib.parse import quote

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sistema UpDown V4", page_icon="🏗️", layout="wide")

# Nomes dos arquivos
ARQUIVO_MATERIAIS = 'materiais_v2.csv' # Mudamos para V2 para criar estrutura nova
ARQUIVO_HISTORICO = 'historico.csv'
ARQUIVO_LOGO = 'logo_updown.png'

# --- FUNÇÕES DE BANCO DE DADOS ---
def carregar_materiais():
    if not os.path.exists(ARQUIVO_MATERIAIS):
        # DADOS EXEMPLO (JÁ COM O TEXTO QUE VOCÊ PEDIU)
        texto_janelas = """1.1 Os selantes das extremidades das janelas estão com tempo de vida útil vencidos, gerando infiltrações e trincas.
1.2 Necessário remoção por completo dos selantes antigos.
1.3 Aplicar selante fibrado em todas as janelas do prédio, restaurando todas as impermeabilizações."""
        
        texto_grades = """2.1 Grades de suspiro com impermeabilizações comprometidas.
2.2 Necessário remover todas as crostas desplacadas.
2.3 Aplicar limpeza manual para descontaminar região.
2.4 Aplicar selante fibrado e borracha líquida para impermeabilização total."""

        dados_iniciais = [
            {
                "Item": "Impermeabilização das Janelas", 
                "Descricao_Tecnica": texto_janelas, 
                "Custo_Material": 4000.00, 
                "Custo_Mao_Obra": 9500.00
            },
            {
                "Item": "Impermeabilização Grades de Ar", 
                "Descricao_Tecnica": texto_grades, 
                "Custo_Material": 4000.00, 
                "Custo_Mao_Obra": 8570.00
            }
        ]
        df = pd.DataFrame(dados_iniciais)
        df.to_csv(ARQUIVO_MATERIAIS, index=False)
        return df
    return pd.read_csv(ARQUIVO_MATERIAIS)

def salvar_tabela_editada(df_novo):
    df_novo.to_csv(ARQUIVO_MATERIAIS, index=False)

def carregar_historico():
    if not os.path.exists(ARQUIVO_HISTORICO):
        return pd.DataFrame(columns=["Data", "Cliente", "Total", "Link Zap"])
    return pd.read_csv(ARQUIVO_HISTORICO)

def salvar_historico(dados_orcamento):
    df_hist = carregar_historico()
    df_novo = pd.concat([df_hist, pd.DataFrame([dados_orcamento])], ignore_index=True)
    df_novo.to_csv(ARQUIVO_HISTORICO, index=False)

# --- FUNÇÃO PDF PRO (COM ESCOPO TÉCNICO E SEPARAÇÃO DE CUSTOS) ---
def gerar_pdf(cliente, cnpj, data_emissao, data_validade, itens, totais, obs):
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
    pdf.cell(190, 6, txt=f"Data: {data_emissao}  |  Validade: {data_validade}", ln=True)
    pdf.ln(10)
    
    # --- SEÇÃO 1: ESCOPO TÉCNICO DETALHADO ---
    pdf.set_font("Arial", 'B', 14)
    pdf.set_fill_color(230, 230, 230) # Cinza claro
    pdf.cell(190, 10, txt="  1. ESCOPO TÉCNICO DOS SERVIÇOS", ln=True, align='L', fill=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", size=11)
    for i in itens:
        # Título do Item
        nome_item = i['Item'].encode('latin-1', 'replace').decode('latin-1')
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(190, 8, txt=f"• {nome_item}", ln=True)
        
        # Descrição Técnica (Multi-linhas)
        pdf.set_font("Arial", size=10)
        desc_tec = i['Descricao_Tecnica'].encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(190, 6, txt=desc_tec)
        pdf.ln(5)
    
    pdf.ln(5)

    # --- SEÇÃO 2: INVESTIMENTO E VALORES ---
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(190, 10, txt="  2. RESUMO DO INVESTIMENTO", ln=True, align='L', fill=True)
    pdf.ln(5)

    # Tabela Simples de Quantitativos
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(100, 8, "Item", 1)
    pdf.cell(30, 8, "Qtd", 1, align='C')
    pdf.cell(60, 8, "Valor Total do Item", 1, align='C')
    pdf.ln()
    
    pdf.set_font("Arial", size=10)
    for i in itens:
        nome_item = i['Item'].encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(100, 8, nome_item, 1)
        pdf.cell(30, 8, str(i['Qtd']), 1, align='C')
        pdf.cell(60, 8, f"R$ {i['Total_Item']:,.2f}", 1, align='R')
        pdf.ln()

    pdf.ln(5)

    # --- QUADRO RESUMO (SEPARAÇÃO MATERIAL X MÃO DE OBRA) ---
    pdf.set_font("Arial", size=11)
    
    # Linha Material
    pdf.cell(130, 8, "Total de Materiais:", 0, align='R')
    pdf.cell(60, 8, f"R$ {totais['Material']:,.2f}", 0, align='R')
    pdf.ln()
    
    # Linha Mão de Obra (com NF)
    pdf.cell(130, 8, "Total Mão de Obra (c/ NF):", 0, align='R')
    pdf.cell(60, 8, f"R$ {totais['Mao_Obra']:,.2f}", 0, align='R')
    pdf.ln()

    # Ajuste BDI
    if totais['BDI_Valor'] != 0:
        texto_bdi = f"Ajuste / Desconto ({totais['BDI_Percent']}%):"
        pdf.cell(130, 8, texto_bdi, 0, align='R')
        cor = (200, 0, 0) if totais['BDI_Valor'] < 0 else (0, 0, 0)
        pdf.set_text_color(*cor)
        pdf.cell(60, 8, f"R$ {totais['BDI_Valor']:,.2f}", 0, align='R')
        pdf.set_text_color(0, 0, 0)
        pdf.ln()

    pdf.line(100, pdf.get_y(), 190, pdf.get_y())
    
    # TOTAL GERAL
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(130, 12, "TOTAL GERAL:", 0, align='R')
    pdf.cell(60, 12, f"R$ {totais['Final']:,.2f}", 0, align='R')
    pdf.ln(10)
    
    # Obs
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 8, "CONDICOES E PAGAMENTO:", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.multi_cell(0, 6, txt=obs.encode('latin-1', 'replace').decode('latin-1'))
    
    # Rodapé
    pdf.ln(20)
    pdf.cell(190, 5, "__________________________________________________", ln=True, align='C')
    pdf.cell(190, 5, "UPDOWN SERVICOS DE ALTA PERFORMANCE", ln=True, align='C')
    
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFACE ---
st.sidebar.image(ARQUIVO_LOGO, width=200) if os.path.exists(ARQUIVO_LOGO) else None
st.title("🏗️ Sistema Pro - UPDOWN V4")
st.markdown("---")

df_materiais = carregar_materiais()
opcao = st.sidebar.radio("Menu Principal", ["Criar Orçamento", "Gerenciar Itens (Banco de Dados)", "Histórico"])

# --- ABA 1: GERENCIAR ITENS (AVANÇADO) ---
if opcao == "Gerenciar Itens (Banco de Dados)":
    st.subheader("📦 Banco de Dados (Com Descritivo Técnico)")
    st.info("Aqui você define o Custo do Material e da Mão de Obra separadamente. O sistema soma tudo no final.")
    
    df_editado = st.data_editor(
        df_materiais,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Item": st.column_config.TextColumn("Nome do Serviço", width="medium", required=True),
            "Descricao_Tecnica": st.column_config.TextColumn("Escopo Técnico (1.1, 1.2...)", width="large", help="Cole aqui o texto detalhado"),
            "Custo_Material": st.column_config.NumberColumn("Valor Material (R$)", format="R$ %.2f", step=10.0),
            "Custo_Mao_Obra": st.column_config.NumberColumn("Valor Mão de Obra (R$)", format="R$ %.2f", step=10.0),
        },
        key="editor_materiais_v4"
    )

    if st.button("💾 Salvar Alterações"):
        salvar_tabela_editada(df_editado)
        st.success("Banco de dados atualizado!")
        st.rerun()

# --- ABA 2: HISTÓRICO ---
elif opcao == "Histórico":
    st.subheader("📂 Histórico")
    df_hist = carregar_historico()
    if not df_hist.empty:
        st.dataframe(df_hist, use_container_width=True)
    else:
        st.info("Vazio.")

# --- ABA 3: CRIAR ORÇAMENTO ---
elif opcao == "Criar Orçamento":
    st.subheader("📝 Novo Orçamento Técnico")
    
    c1, c2, c3 = st.columns([2, 1, 1])
    cliente = c1.text_input("Cliente")
    cnpj = c2.text_input("CNPJ / CPF")
    telefone = c3.text_input("WhatsApp")
    
    st.markdown("##### Selecionar Serviços")
    col_sel1, col_sel2, col_sel3 = st.columns([3, 1, 1])
    
    df_atual = carregar_materiais()
    
    if not df_atual.empty:
        item_sel = col_sel1.selectbox("Serviço", df_atual['Item'].unique())
        
        # Pega dados do item
        dados_item = df_atual[df_atual['Item'] == item_sel].iloc[0]
        
        # Mostra prévia dos valores (para conferencia)
        st.caption(f"💰 Base: Material R$ {dados_item['Custo_Material']:.2f} | Mão de Obra R$ {dados_item['Custo_Mao_Obra']:.2f}")
        
        qtd = col_sel2.number_input("Qtd", 1, value=1)
        
        if 'carrinho_v4' not in st.session_state: st.session_state.carrinho_v4 = []
        
        if col_sel3.button("➕ Adicionar"):
            total_mat = dados_item['Custo_Material'] * qtd
            total_mo = dados_item['Custo_Mao_Obra'] * qtd
            st.session_state.carrinho_v4.append({
                "Item": item_sel,
                "Descricao_Tecnica": dados_item['Descricao_Tecnica'],
                "Qtd": qtd,
                "Unit_Material": dados_item['Custo_Material'],
                "Unit_Mao_Obra": dados_item['Custo_Mao_Obra'],
                "Total_Material": total_mat,
                "Total_Mao_Obra": total_mo,
                "Total_Item": total_mat + total_mo
            })
            st.success("Adicionado!")

    # EXIBIÇÃO DO CARRINHO E TOTAIS
    if st.session_state.carrinho_v4:
        st.markdown("---")
        df_cart = pd.DataFrame(st.session_state.carrinho_v4)
        
        # Exibe tabela simplificada na tela
        st.table(df_cart[["Item", "Qtd", "Total_Material", "Total_Mao_Obra", "Total_Item"]])
        
        # SOMAS
        soma_material = df_cart['Total_Material'].sum()
        soma_mo = df_cart['Total_Mao_Obra'].sum()
        soma_bruta = soma_material + soma_mo
        
        st.write("### 📊 Fechamento Financeiro")
        col_bdi, col_resumo = st.columns([2, 2])
        
        with col_bdi:
            bdi_percent = st.slider("Ajuste / Desconto (%)", -50, 50, 0)
            
            modelos = {
                "Padrão": "Pagamento: 50% entrada / 50% entrega.\nValidade: 15 dias.",
                "Parcelado": "Entrada + 3 parcelas (30/60/90).\nSujeito a aprovação."
            }
            mod = st.selectbox("Modelo Texto", list(modelos.keys()))
            obs = st.text_area("Condições", value=modelos[mod], height=100)
            
        valor_bdi = soma_bruta * (bdi_percent / 100)
        total_final = soma_bruta + valor_bdi
        
        with col_resumo:
            st.markdown(f"**Total Material:** R$ {soma_material:,.2f}")
            st.markdown(f"**Total Mão de Obra:** R$ {soma_mo:,.2f}")
            st.divider()
            st.markdown(f"Subtotal: R$ {soma_bruta:,.2f}")
            st.markdown(f"Ajuste ({bdi_percent}%): R$ {valor_bdi:,.2f}")
            st.markdown(f"### 🏁 TOTAL: R$ {total_final:,.2f}")

        # GERAÇÃO
        st.markdown("---")
        c_limpar, c_gerar = st.columns([1, 3])
        
        if c_limpar.button("🗑️ Limpar"):
            st.session_state.carrinho_v4 = []
            st.rerun()
            
        if c_gerar.button("✅ Gerar Proposta Técnica (PDF)"):
            if not cliente:
                st.error("Preencha o Cliente!")
            else:
                hoje = datetime.today().strftime("%d/%m/%Y")
                validade = (datetime.today() + timedelta(days=15)).strftime("%d/%m/%Y")
                
                totais_dict = {
                    "Material": soma_material,
                    "Mao_Obra": soma_mo,
                    "BDI_Percent": bdi_percent,
                    "BDI_Valor": valor_bdi,
                    "Final": total_final
                }
                
                pdf_bytes = gerar_pdf(cliente, cnpj, hoje, validade, st.session_state.carrinho_v4, totais_dict, obs)
                
                link_zap = f"https://wa.me/55{telefone}?text={quote(f'Olá {cliente}, segue proposta. Total: R$ {total_final:,.2f}')}" if telefone else "#"
                salvar_historico({"Data": hoje, "Cliente": cliente, "Total": total_final, "Link Zap": link_zap})
                
                st.success("Proposta Gerada!")
                c1, c2 = st.columns(2)
                c1.download_button("⬇️ Baixar PDF", pdf_bytes, f"Proposta_{cliente}.pdf", "application/pdf")
                if telefone: c2.link_button("📱 WhatsApp", link_zap)
