import pandas as pd
import plotly.express as px
import streamlit as st

# 1. Título do App
st.set_page_config(page_title="Data Discovery - Sucesso de Lojas", layout="wide")
st.title("🔍 Analisador de Padrões de Performance")

# 2. Upload da Base de Dados (suas lojas atuais)
uploaded_file = st.file_uploader("Suba o Excel com o histórico das suas lojas", type=['xlsx', 'csv'])

if uploaded_file:
    df = pd.read_excel(uploaded_file) if "xlsx" in uploaded_file.name else pd.read_csv(uploaded_file)
    
    st.subheader("📊 Visão Geral dos Dados")
    st.write(df.head())

    # 3. Definição de Performance
    # Vamos assumir que você tem uma coluna 'Vendas' ou 'ROI'
    meta_sucesso = st.slider("Defina o que é uma loja de 'Alta Performance' (Vendas acima de:)", 
                             min_value=float(df['Vendas'].min()), 
                             max_value=float(df['Vendas'].max()))

    df['Categoria'] = df['Vendas'].apply(lambda x: 'Alta Performance' if x >= meta_sucesso else 'Performance Comum')

    # 4. Análise de Padrões (Ex: Posição, Vagas, Presença de Polos)
    st.subheader("🎯 Quais padrões as lojas de Alta Performance possuem?")
    
    col_analise = st.selectbox("Escolha uma característica para comparar:", 
                               ['Posicao', 'Vagas', 'Visibilidade', 'Presenca_Polo_Gerador'])

    # Gráfico comparativo
    fig = px.histogram(df, x=col_analise, color="Categoria", barmode="group",
                       title=f"Impacto de {col_analise} na Performance",
                       color_discrete_map={'Alta Performance': '#00ffcc', 'Performance Comum': '#4a5568'})
    
    st.plotly_chart(fig, use_container_width=True)

    # 5. Correlação Numérica
    st.subheader("📈 Correlação entre Variáveis (O que mais pesa?)")
    # Mostra o que mais tem correlação com a coluna 'Vendas'
    correlacao = df.corr(numeric_only=True)['Vendas'].sort_values(ascending=False)
    st.write(correlacao)

else:
    st.info("Aguardando upload do arquivo para iniciar a análise.")
