import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da página
st.set_page_config(page_title="Dashboard de Lojas", layout="wide")

# Função para carregar os dados
@st.cache_data
def load_data():
    df = pd.read_excel("Teste de lojas.xlsx")
    # Limpeza simples: remover espaços dos nomes das colunas
    df.columns = [c.strip() for c in df.columns]
    return df

try:
    df = load_data()

    st.title("📊 Laboratório de Performance de Lojas")
    st.markdown("Análise interativa baseada na planilha `Teste de lojas.xlsx`")

    # --- SIDEBAR / FILTROS ---
    st.sidebar.header("Filtros")
    lojas_selecionadas = st.sidebar.multiselect(
        "Selecione as Lojas:",
        options=df["Loja"].unique(),
        default=df["Loja"].unique()
    )

    df_filtrado = df[df["Loja"].isin(lojas_selecionadas)]

    # --- KPIs PRINCIPAIS ---
    col1, col2, col3 = st.columns(3)
    
    total_vendas = df_filtrado["Vendas"].sum()
    ticket_medio = df_filtrado["Ticket Médio"].mean()
    atingimento_meta = (df_filtrado["Vendas"].sum() / df_filtrado["Meta"].sum()) * 100

    col1.metric("Total de Vendas", f"R$ {total_vendas:,.2f}")
    col2.metric("Ticket Médio (Média)", f"R$ {ticket_medio:,.2f}")
    col3.metric("Atingimento de Meta", f"{atingimento_meta:.1f}%")

    st.divider()

    # --- GRÁFICOS ---
    tab1, tab2 = st.tabs(["Análise de Vendas", "Visão de Dados"])

    with tab1:
        col_graf1, col_graf2 = st.columns(2)

        # Gráfico de Barras: Vendas por Loja
        fig_vendas = px.bar(
            df_filtrado, 
            x="Loja", 
            y="Vendas", 
            title="Vendas por Unidade",
            color="Vendas",
            color_continuous_scale="Viridis"
        )
        col_graf1.plotly_chart(fig_vendas, use_container_width=True)

        # Gráfico de Comparação: Vendas vs Meta
        fig_meta = px.bar(
            df_filtrado, 
            x="Loja", 
            y=["Vendas", "Meta"], 
            title="Vendas vs Meta",
            barmode="group"
        )
        col_graf2.plotly_chart(fig_meta, use_container_width=True)

    with tab2:
        st.subheader("Tabela de Dados")
        st.dataframe(df_filtrado, use_container_width=True)

except Exception as e:
    st.error(f"Erro ao carregar o arquivo: {e}")
    st.info("Certifique-se de que o arquivo 'Teste de lojas.xlsx' está na mesma pasta do código.")
