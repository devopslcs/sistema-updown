import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime, timedelta
import os
from urllib.parse import quote

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Orçamentos UpDown", page_icon="🏗️", layout="wide")

# Nomes dos arquivos
ARQUIVO_MATERIAIS = 'materiais.csv'
ARQUIVO_HISTORICO = 'historico.csv'
ARQUIVO_LOGO = 'logo_updown.png'

# --- FUNÇÕES DE BANCO DE DADOS ---
def carregar_materiais():
    if not os.path.exists(ARQUIVO_MATERIAIS):
        # Dados padrão iniciais
        dados_iniciais = [
            {"Item": "Impermeabilização de Janelas (Kit)", "Descricao": "Selante fibrado + Mão de obra", "Preco": 3500.00},
            {"Item": "Mão de Obra (Diária Equipe)", "Descricao": "02 Alpinistas + Equipamentos", "Preco": 1200.00},
            {"Item": "Selante Fibrado (Balde)", "Descricao": "Balde 10kg Industrial", "Preco": 950.00},
            {"Item": "Taxa de Mobilização", "Descricao": "Transporte e Montagem", "Preco": 500.00}
        ]
        df = pd.DataFrame(dados_iniciais)
        df.to_csv(ARQUIVO_MATERIAIS, index=False)
        return df
    return pd.read_csv(ARQUIVO_MATERIAIS)

def salvar_tabela_editada(df_novo):
    """Salva o dataframe inteiro de uma vez no CSV"""
    df_novo.to_csv(ARQUIVO_MATERIAIS, index=False)

def carregar_historico():
    if not os.path.exists(ARQUIVO_HISTORICO):
        return pd.DataFrame(columns=["Data", "Cliente", "Total", "Link Zap"])
    return pd.read_csv(ARQUIVO_HISTORICO)

def salvar_historico(dados_orcamento):
    df_hist = carregar_historico()
    df_novo = pd.concat([df_hist, pd.DataFrame([dados_orcamento])], ignore_index=True)
    df_novo.to_csv(ARQUIVO_HISTORICO, index=False)

# --- FUNÇÃO PDF ---
def gerar_pdf(cliente, cnpj, data_emissao, data_validade, itens, subtotal, bdi_percent, total_final, obs):
    pdf = FPDF()
    pdf.add_page()
    
    if os.path.exists(ARQUIVO_LOGO):
        pdf.image(ARQUIVO_LOGO, 10, 8, 40)
        pdf.ln(20)
    else:
        pdf.ln(10)

    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, txt="ORCAMENTO COMERCIAL", ln=True, align='C')
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(190, 10, txt="UPDOWN SERVICOS DE ALTA PERFORMANCE | CNPJ: 36.130.036/0001-37", ln=True, align='C')
    pdf.ln(10)
    
    # Dados
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 8, txt="DADOS DO CLIENTE", ln=True, align='L')
    pdf.set_font("Arial", size=11)
    pdf.cell(190, 6, txt=f"Cliente: {cliente}", ln=True)
    pdf.cell(190, 6, txt=f"CNPJ/CPF: {cnpj}", ln=True)
    pdf.cell(190, 6, txt=f"Data Emissao: {data_emissao}  |  Validade: {data_validade}", ln=True)
    pdf.ln(8)
    
    # Itens
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(90, 8, "Item / Servico", 1)
    pdf.cell(20, 8, "Qtd", 1, align='C')
    pdf.cell(35, 8, "Vl. Unit", 1, align='C')
    pdf.cell(35, 8, "Total", 1, align='C')
    pdf.ln()
    
    pdf.set_font("Arial", size=10)
    for i in itens:
        nome_item = i['Item'].encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(90, 8, nome_item, 1)
        pdf.cell(20, 8, str(i['Qtd']), 1, align='C')
        pdf.cell(35, 8, f"R$ {i['Unitario']:.2f}", 1, align='R')
        pdf.cell(35, 8, f"R$ {i['Total']:.2f}", 1, align='R')
        pdf.ln()
    
    pdf.ln(5)
    
    # Totais
    pdf.set_font("Arial", size=11)
    if bdi_percent != 0:
        pdf.cell(145, 6, "Subtotal:", 0, align='R')
        pdf.cell(35, 6, f"R$ {subtotal:,.2f}", 0, align='R')
        pdf.ln()
        txt_ajuste = f"Ajuste ({bdi_percent}%):"
        val_ajuste = total_final - subtotal
        pdf.cell(145, 6, txt_ajuste, 0, align='R')
        pdf.cell(35, 6, f"R$ {val_ajuste:,.2f}", 0, align='R')
        pdf.ln()
        pdf.line(120, pdf.get_y(), 190, pdf.get_y())
        pdf.ln(2)

    pdf.set_font("Arial", 'B', 14)
    pdf.cell(145, 10, "TOTAL FINAL:", 0, align='R')
    pdf.cell(35, 10, f"R$ {total_final:,.2f}", 0, align='R')
    pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 8, "CONDICOES E OBSERVACOES:", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.multi_cell(0, 6, txt=obs.encode('latin-1', 'replace').decode('latin-1'))
    
    pdf.ln(20)
    pdf.cell(190, 5, "__________________________________________________", ln=True, align='C')
    pdf.cell(190, 5, "UPDOWN SERVICOS DE ALTA PERFORMANCE", ln=True, align='C')
    
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFACE ---
st.sidebar.image(ARQUIVO_LOGO, width=200) if os.path.exists(ARQUIVO_LOGO) else None
st.title("🏗️ Sistema de Orçamentos - UPDOWN")
st.markdown("---")

df_materiais = carregar_materiais()
opcao = st.sidebar.radio("Menu Principal", ["Criar Orçamento", "Gerenciar Itens (Banco de Dados)", "Histórico"])

# --- ABA 1: GERENCIAR ITENS (NOVA VERSÃO EDITÁVEL) ---
if opcao == "Gerenciar Itens (Banco de Dados)":
    st.subheader("📦 Gerenciamento de Materiais e Serviços")
    st.info("💡 Dica: Clique duas vezes na célula para editar. Para excluir, selecione a linha e aperte 'Delete'. Para adicionar, clique na última linha.")
    
    # Editor de Dados (Tabela estilo Excel)
    df_editado = st.data_editor(
        df_materiais,
        num_rows="dynamic", # Permite adicionar e remover linhas
        use_container_width=True,
        column_config={
            "Preco": st.column_config.NumberColumn(
                "Preço Base (R$)",
                help="Valor unitário padrão",
                min_value=0.0,
                step=0.01,
                format="R$ %.2f"
            ),
            "Item": st.column_config.TextColumn(
                "Nome do Item",
                width="medium",
                required=True
            ),
            "Descricao": st.column_config.TextColumn(
                "Descrição Técnica",
                width="large"
            )
        },
        key="editor_materiais"
    )

    # Botão para salvar as alterações
    col_btn1, col_btn2 = st.columns([1, 4])
    if col_btn1.button("💾 Salvar Alterações"):
        salvar_tabela_editada(df_editado)
        st.success("Banco de dados atualizado com sucesso!")
        # Recarregar para garantir
        st.rerun()

# --- ABA 2: HISTÓRICO ---
elif opcao == "Histórico":
    st.subheader("📂 Histórico")
    df_hist = carregar_historico()
    if not df_hist.empty:
        st.metric("Total Vendido", f"R$ {df_hist['Total'].sum():,.2f}")
        st.dataframe(df_hist, use_container_width=True)
    else:
        st.info("Vazio.")

# --- ABA 3: CRIAR ORÇAMENTO ---
elif opcao == "Criar Orçamento":
    st.subheader("📝 Dados do Orçamento")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    cliente = col1.text_input("Nome do Cliente")
    cnpj = col2.text_input("CNPJ / CPF")
    telefone = col3.text_input("WhatsApp (DDD+Num)", placeholder="42999999999")
    
    st.markdown("##### Adicionar Itens")
    c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
    
    # Carrega a lista atualizada (inclusive se você acabou de editar na outra aba)
    df_atualizado = carregar_materiais()
    
    if df_atualizado.empty:
        st.warning("Nenhum item cadastrado! Vá em 'Gerenciar Itens' para cadastrar.")
    else:
        item_sel = c1.selectbox("Item", df_atualizado['Item'].unique())
        
        # Lógica para pegar o preço (segura contra erros de índice)
        try:
            preco_base = df_atualizado.loc[df_atualizado['Item'] == item_sel, 'Preco'].values[0]
        except:
            preco_base = 0.0
            
        qtd = c2.number_input("Qtd", 1, value=1)
        preco_final = c3.number_input("Valor Unit.", value=float(preco_base))
        
        if 'carrinho' not in st.session_state: st.session_state.carrinho = []
        
        if c4.button("➕ Add"):
            st.session_state.carrinho.append({"Item": item_sel, "Qtd": qtd, "Unitario": preco_final, "Total": qtd*preco_final})
            st.success("Adicionado!")

    if st.session_state.carrinho:
        st.markdown("---")
        df_cart = pd.DataFrame(st.session_state.carrinho)
        st.table(df_cart)
        
        subtotal = df_cart['Total'].sum()
        
        st.write("### 📊 Fechamento")
        col_bdi, col_resumo = st.columns([2, 2])
        
        with col_bdi:
            bdi_percent = st.slider("Margem / Desconto (%)", -50, 50, 0)
            
            # SELETOR DE MODELOS DE OBSERVAÇÃO
            st.markdown("**Modelos de Texto:**")
            modelos_obs = {
                "Padrão": "Pagamento: 50% entrada / 50% entrega.\nValidade: 15 dias.\nGarantia: 06 meses.",
                "Condomínio": "Pagamento: 30/60 dias no boleto.\nNecessário agendar isolamento de área.\nGarantia: 06 meses.",
                "Parcelado": "Pagamento: Entrada + 3x no Cartão.\nValidade: 10 dias."
            }
            modelo_selecionado = st.selectbox("Escolha um modelo:", list(modelos_obs.keys()))
            texto_modelo = modelos_obs[modelo_selecionado]
            
            obs = st.text_area("Editar Texto Final:", value=texto_modelo, height=100)
        
        val_bdi = subtotal * (bdi_percent / 100)
        total_final = subtotal + val_bdi
        
        with col_resumo:
            st.write(f"**Subtotal:** R$ {subtotal:,.2f}")
            cor_bdi = "red" if bdi_percent < 0 else "green"
            st.markdown(f"**Ajuste:** :{cor_bdi}[R$ {val_bdi:,.2f}]")
            st.markdown(f"### Total Final: R$ {total_final:,.2f}")

        st.markdown("---")
        
        c_limpar, c_gerar = st.columns([1, 3])
        if c_limpar.button("🗑️ Limpar"):
            st.session_state.carrinho = []
            st.rerun()
            
        if c_gerar.button("✅ Gerar PDF"):
            if not cliente:
                st.error("Nome do cliente é obrigatório!")
            else:
                hoje = datetime.today()
                data_emissao = hoje.strftime("%d/%m/%Y")
                data_validade = (hoje + timedelta(days=15)).strftime("%d/%m/%Y")
                
                # Gera PDF
                pdf_bytes = gerar_pdf(cliente, cnpj, data_emissao, data_validade, st.session_state.carrinho, subtotal, bdi_percent, total_final, obs)
                
                # Gera Link do WhatsApp
                msg_zap = f"Olá {cliente}, segue a proposta da UpDown. Valor Total: R$ {total_final:,.2f}. Qualquer dúvida estou à disposição!"
                link_zap = f"https://wa.me/55{telefone}?text={quote(msg_zap)}" if telefone else "#"
                
                # Salva Histórico
                salvar_historico({"Data": data_emissao, "Cliente": cliente, "Total": total_final, "Link Zap": link_zap})
                
                st.success("Orçamento Gerado com Sucesso!")
                
                # Botões de Ação
                c1, c2 = st.columns(2)
                c1.download_button("⬇️ Baixar PDF", pdf_bytes, file_name=f"Orcamento_{cliente}.pdf", mime="application/pdf")
                if telefone:
                    c2.link_button("📱 Enviar no WhatsApp", link_zap)
                else:
                    c2.warning("Preencha o WhatsApp para habilitar o envio.")
