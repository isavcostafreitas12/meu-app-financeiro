import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import date

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(page_title="Gestão Financeira", layout="wide", page_icon="📈")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    h1 { color: #2c3e50; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    </style>
""", unsafe_allow_html=True)

ARQUIVO_DADOS = 'dados_financeiros.csv'

# ==========================================
# 2. INICIALIZAÇÃO E CARREGAMENTO DE DADOS
# ==========================================
if 'financas' not in st.session_state:
    if os.path.exists(ARQUIVO_DADOS):
        df_salvo = pd.read_csv(ARQUIVO_DADOS)
        df_salvo['Data'] = pd.to_datetime(df_salvo['Data'])
        
        if 'Conta' not in df_salvo.columns:
            df_salvo.insert(2, 'Conta', 'Não Especificada')
            
        st.session_state.financas = df_salvo
    else:
        st.session_state.financas = pd.DataFrame(columns=['Data', 'Tipo', 'Conta', 'Categoria', 'Descrição', 'Valor'])

# ==========================================
# 3. PAINEL LATERAL (Entrada de Dados)
# ==========================================
with st.sidebar:
    st.header("📝 Nova Transação")
    
    with st.form(key='form_transacao', clear_on_submit=True):
        data_input = st.date_input("Data", value=date.today())
        tipo_input = st.radio("Tipo de Movimentação", ["Entrada 🟢", "Saída 🔴"])
        
        conta_input = st.selectbox("Conta / Instituição", ["Nubank", "Banco Inter", "C6 Bank", "Dinheiro Físico", "Outra"])
        
        if "Entrada" in tipo_input:
            cat_opcoes = ["Salário", "Bolsa/Estágio", "Mesada", "Rendimento de Investimento", "Transferência Recebida", "Venda", "Outros"]
        else:
            cat_opcoes = [
                "Alimentação", "Vestuário", "Higiene e Cuidados", "Saúde", 
                "Transporte", "Cursos/Educação", "Investimento", "Moradia", 
                "Lazer e Assinaturas", "Finanças/Taxas", "Outros"
            ]
            
        categoria_input = st.selectbox("Categoria", cat_opcoes)
        desc_input = st.text_input("Descrição (Ex: Compra de livros, Lanche)")
        valor_input = st.number_input("Valor (R$)", min_value=0.01, format="%.2f", step=10.0)
        
        submit_button = st.form_submit_button(label="Adicionar Transação")
        
        if submit_button:
            tipo_limpo = "Entrada" if "Entrada" in tipo_input else "Saída"
            nova_linha = pd.DataFrame({
                'Data': [pd.to_datetime(data_input)],
                'Tipo': [tipo_limpo],
                'Conta': [conta_input],
                'Categoria': [categoria_input],
                'Descrição': [desc_input],
                'Valor': [valor_input]
            })
            
            st.session_state.financas = pd.concat([st.session_state.financas, nova_linha], ignore_index=True)
            st.session_state.financas.to_csv(ARQUIVO_DADOS, index=False)
            
            st.success("Guardado com sucesso no ficheiro!")

    if st.button("Limpar todos os dados 🗑️"):
        st.session_state.financas = pd.DataFrame(columns=['Data', 'Tipo', 'Conta', 'Categoria', 'Descrição', 'Valor'])
        st.session_state.financas.to_csv(ARQUIVO_DADOS, index=False)
        st.rerun()

# ==========================================
# 4. PAINEL PRINCIPAL (Dashboard e Análises)
# ==========================================
st.title("📊 Análise Inteligente de Finanças")

df = st.session_state.financas.copy()

if df.empty:
    st.info("👋 Olá! Adicione a sua primeira transação no menu lateral. Ela ficará guardada automaticamente.")
else:
    total_entradas = df[df['Tipo'] == 'Entrada']['Valor'].sum()
    total_saidas = df[df['Tipo'] == 'Saída']['Valor'].sum()
    saldo_atual = total_entradas - total_saidas
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Total de Entradas", value=f"R$ {total_entradas:,.2f}")
    with col2:
        st.metric(label="Total de Saídas", value=f"R$ {total_saidas:,.2f}")
    with col3:
        cor_saldo = "normal" if saldo_atual >= 0 else "inverse"
        st.metric(label="Saldo Atual", value=f"R$ {saldo_atual:,.2f}", delta="Líquido", delta_color=cor_saldo)

    st.markdown("---")

    col_graf1, col_graf2 = st.columns(2)
    
    with col_graf1:
        st.subheader("Despesas por Categoria 📉")
        df_saidas = df[df['Tipo'] == 'Saída']
        if not df_saidas.empty:
            df_agrupado = df_saidas.groupby('Categoria')['Valor'].sum().reset_index()
            fig_pie = px.pie(df_agrupado, values='Valor', names='Categoria', hole=0.4, color_discrete_sequence=px.colors.sequential.Sunset)
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.write("Sem saídas registadas.")

    with col_graf2:
        st.subheader("Movimentações por Conta 🏦")
        df_conta = df.groupby(['Conta', 'Tipo'])['Valor'].sum().reset_index()
        if not df_conta.empty:
            cores = {'Entrada': '#2ecc71', 'Saída': '#e74c3c'}
            fig_bar_conta = px.bar(df_conta, x='Conta', y='Valor', color='Tipo', barmode='group', color_discrete_map=cores)
            fig_bar_conta.update_layout(xaxis_title="Conta / Instituição", yaxis_title="Valor (R$)")
            st.plotly_chart(fig_bar_conta, use_container_width=True)
        else:
            st.write("Sem dados suficientes por conta.")

    st.markdown("---")

    st.subheader("📋 Histórico de Transações")
    df_exibicao = df.copy()
    df_exibicao['Data'] = df_exibicao['Data'].dt.strftime('%d/%m/%Y')
    df_exibicao['Valor'] = df_exibicao['Valor'].apply(lambda x: f"R$ {x:,.2f}")
    
    df_exibicao = df_exibicao[['Data', 'Tipo', 'Conta', 'Categoria', 'Descrição', 'Valor']]
    st.dataframe(df_exibicao, use_container_width=True, hide_index=True)
