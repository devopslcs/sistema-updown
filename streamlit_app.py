import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Orçamentos UpDown", page_icon="🏗️", layout="wide")

# Nomes dos arquivos
ARQUIVO_MATERIAIS = 'materiais.csv'
ARQUIVO_HISTORICO = 'historico.csv'
ARQUIVO_LOGO = 'logo_updown.png' # Certifique-se que a imagem está no GitHub com este nome

# --- FUNÇÕES DE BANCO DE DADOS (CSV) ---
def carregar_materiais():
    if not os.path.exists(ARQUIVO_MATERIAIS):
        # Dados padrão
        dados_iniciais = [
            {"Item": "Impermeabilização de Janelas (Kit)", "Descricao": "Selante fibrado + Mão de obra", "Preco": 3500.00},
            {"Item": "Mão de Obra (Diária Equipe)", "Descricao": "02 Alpinistas + Equipamentos", "Preco": 1200.00},
            {"Item": "Selante Fibrado (Balde)", "Descricao": "Balde 10kg Industrial", "Preco": 950.00},
            {"Item": "Taxa de Mobilização", "Descricao": "Transporte e Montagem", "Preco": 500.00}
        ]
        df = pd.DataFrame(dados_iniciais)
        df.to_csv(ARQUIVO_MATERIAIS, index=False)
        return df
    else:
        return pd.read_csv(ARQUIVO_MATERIAIS)

def salvar_novo_material(novo_item):
    df_atual = carregar_materiais()
    df_novo = pd.concat([df_atual, pd.DataFrame([novo_item])], ignore_index=True)
    df_novo.to_csv(ARQUIVO_MATERIAIS, index=False)
    return df_novo

def carregar_historico():
    if not os.path.exists(ARQUIVO_HISTORICO):
        return pd.DataFrame(columns=["Data", "Cliente", "CNPJ", "Total", "Obs"])
    else:
        return pd.read_csv(ARQUIVO_HISTORICO)

def salvar_historico(dados_orcamento):
    df_hist = carregar_historico()
    df_novo = pd.concat([df_hist, pd.DataFrame([dados_orcamento])], ignore_index=True)
    df_novo.to_csv(ARQUIVO_HISTORICO, index=False)

# --- FUNÇÃO PARA GERAR PDF (COM LOGO E BDI) ---
def gerar_pdf(cliente, cnpj, data, itens, subtotal, bdi_percent, total_final, obs):
    pdf = FPDF()
    pdf.add_page()
    
    # Inserir Logo se existir no GitHub
    if os.path.exists(ARQUIVO_LOGO):
        # x=10, y=8, w=40 (ajuste o w conforme o tamanho da sua logo)
        pdf.image(ARQUIVO_LOGO, 10, 8, 40)
        pdf.ln(20) # Pula espaço da logo
    else:
        pdf.ln(10)

    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, txt="ORCAMENTO COMERCIAL", ln=True, align='C')
    
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(190, 10, txt="UPDOWN SERVICOS DE ALTA PERFORMANCE", ln=True, align='C')
    pdf.cell(190, 5, txt="CNPJ: 36.130.036/0001-37 | Ponta Grossa - PR", ln=True, align='C')
    pdf.ln(10)
    
    # Dados do Cliente
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 8, txt="DADOS DO CLIENTE", ln=True, align='L')
    pdf.set_font("Arial", size=11)
    pdf.cell(190, 6, txt=f"Cliente: {cliente}", ln=True)
    pdf.cell(190, 6, txt=f"CNPJ/CPF: {cnpj}", ln=True)
    pdf.cell(190, 6, txt=f"Data: {data}", ln=True)
    pdf.ln(8)
    
    # Tabela de Itens
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
    
    # --- ÁREA DE TOTAIS COM BDI ---
    pdf.set_font("Arial", size=11)
    
    # Se houver BDI (diferente de 0), mostra o subtotal e o ajuste
    if bdi_percent != 0:
        pdf.cell(145, 6, "Subtotal:", 0, align='R')
        pdf.cell(35, 6, f"R$ {subtotal:,.2f}", 0, align='R')
        pdf.ln()
        
        texto_ajuste = f"Ajuste / Desconto ({bdi_percent}%):"
        valor_ajuste = total_final - subtotal
        pdf.cell(145, 6, texto_ajuste, 0, align='R')
        pdf.cell(35, 6, f"R$ {valor_ajuste:,.2f}", 0, align='R')
        pdf.ln()
        pdf.line(120, pdf.get_y(), 190, pdf.get_y()) # Linha separadora
        pdf.ln(2)

    # Valor Final em destaque
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(145, 10, "TOTAL FINAL:", 0, align='R')
    pdf.cell(35, 10, f"R$ {total_final:,.2f}", 0, align='R')
    pdf.ln(10)
    
    # Observações
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 8, "CONDICOES E OBSERVACOES:", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.multi_cell(0, 6, txt=obs.encode('latin-1', 'replace').decode('latin-1'))
    
    # Rodapé
    pdf.ln(20)
    pdf.cell(190, 5, "__________________________________________________", ln=True, align='C')
    pdf.cell(190, 5, "UPDOWN SERVICOS DE ALTA PERFORMANCE", ln=True, align='C')
    pdf.cell(190, 5, "Celso Alex Sandro de Oliveira", ln=True, align='C')
    
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFACE DO SISTEMA ---
st.sidebar.image(ARQUIVO_LOGO, width=200) if os.path.exists(ARQUIVO_LOGO) else None
st.title("🏗️ Sistema de Orçamentos - UPDOWN")
st.markdown("---")

df_materiais = carregar_materiais()
opcao = st.sidebar.radio("Menu Principal", ["Criar Orçamento", "Cadastrar Item", "Histórico"])

# --- ABA 1: CADASTRAR ITEM ---
if opcao == "Cadastrar Item":
    st.subheader("📦 Novo Item no Banco de Dados")
    with st.form("form_add"):
        c1, c2 = st.columns([3, 1])
        novo_nome = c1.text_input("Nome do Item / Serviço")
        novo_preco = c2.number_input("Preço Base (R$)", min_value=0.0, value=100.0)
        nova_desc = st.text_input("Descrição")
        
        if st.form_submit_button("Salvar no Sistema"):
            novo_item = {"Item": novo_nome, "Descricao": nova_desc, "Preco": novo_preco}
            salvar_novo_material(novo_item)
            st.success("Item salvo com sucesso!")
            st.rerun()
            
    st.write("### Itens Atuais:")
    st.dataframe(df_materiais, use_container_width=True)

# --- ABA 2: HISTÓRICO ---
elif opcao == "Histórico":
    st.subheader("📂 Histórico de Orçamentos")
    df_hist = carregar_historico()
    if not df_hist.empty:
        st.metric("Total Vendido", f"R$ {df_hist['Total'].sum():,.2f}")
        st.dataframe(df_hist, use_container_width=True)
    else:
        st.info("Nenhum histórico encontrado.")

# --- ABA 3: CRIAR ORÇAMENTO (COM BDI) ---
elif opcao == "Criar Orçamento":
    st.subheader("📝 Gerar Orçamento")
    
    col1, col2 = st.columns(2)
    cliente = col1.text_input("Nome do Cliente")
    cnpj = col2.text_input("CNPJ / CPF")
    
    # Adicionar Itens
    st.markdown("##### Adicionar Itens")
    c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
    item_sel = c1.selectbox("Item", df_materiais['Item'].unique())
    preco_base = df_materiais.loc[df_materiais['Item'] == item_sel, 'Preco'].values[0]
    
    qtd = c2.number_input("Qtd", 1, value=1)
    preco_final = c3.number_input("Valor Unit.", value=float(preco_base))
    
    if 'carrinho' not in st.session_state: st.session_state.carrinho = []
    
    if c4.button("➕ Add"):
        st.session_state.carrinho.append({
            "Item": item_sel, "Qtd": qtd, 
            "Unitario": preco_final, "Total": qtd*preco_final
        })
        st.success("Adicionado!")

    # Exibir Carrinho e Totais
    if st.session_state.carrinho:
        st.markdown("---")
        df_cart = pd.DataFrame(st.session_state.carrinho)
        st.table(df_cart)
        
        # CÁLCULOS COM BDI
        subtotal = df_cart['Total'].sum()
        
        st.write("### 📊 Fechamento de Valores")
        col_bdi, col_resumo = st.columns([2, 2])
        
        with col_bdi:
            st.info("Utilize a barra abaixo para aplicar descontos (esquerda) ou margem de lucro (direita).")
            bdi_percent = st.slider("Margem / Desconto (%)", min_value=-50, max_value=50, value=0, step=1)
        
        val_bdi = subtotal * (bdi_percent / 100)
        total_final = subtotal + val_bdi
        
        with col_resumo:
            st.write(f"**Subtotal:** R$ {subtotal:,.2f}")
            cor_bdi = "red" if bdi_percent < 0 else "green"
            st.markdown(f"**Ajuste ({bdi_percent}%):** :{cor_bdi}[R$ {val_bdi:,.2f}]")
            st.markdown(f"### Total Final: R$ {total_final:,.2f}")

        # Botões Finais
        st.markdown("---")
        obs = st.text_area("Observações", "Pagamento: 50% entrada / 50% entrega.\nValidade: 15 dias.")
        
        c_limpar, c_gerar = st.columns([1, 3])
        if c_limpar.button("🗑️ Limpar"):
            st.session_state.carrinho = []
            st.rerun()
            
        if c_gerar.button("✅ Gerar PDF Final"):
            if not cliente:
                st.error("Preencha o nome do cliente!")
            else:
                data_hoje = datetime.today().strftime("%d/%m/%Y")
                
                # Gera o PDF passando os novos valores calculados
                pdf_bytes = gerar_pdf(
                    cliente, cnpj, data_hoje, 
                    st.session_state.carrinho, 
                    subtotal, bdi_percent, total_final, 
                    obs
                )
                
                # Salva no histórico
                salvar_historico({
                    "Data": data_hoje, 
                    "Cliente": cliente, 
                    "Total": total_final,
                    "Obs": f"BDI: {bdi_percent}%"
                })
                
                st.download_button(
                    label="⬇️ Baixar PDF Assinado",
                    data=pdf_bytes,
                    file_name=f"Orcamento_{cliente}.pdf",
                    mime="application/pdf"
                )
