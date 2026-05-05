import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Laboratório de Lojas", layout="wide")

st.title("📊 Laboratório de Performance de Lojas")

# --- COMPONENTE DE UPLOAD ---
# Isso resolve o erro: se o arquivo não estiver no GitHub, você sobe ele pelo navegador
uploaded_file = st.sidebar.file_uploader("Suba sua planilha 'Teste de lojas.xlsx' aqui", type=["xlsx"])

def load_data(file):
    df = pd.read_excel(file)
    # Limpa nomes de colunas (remove espaços extras)
    df.columns = [c.strip() for c in df.columns]
    return df

if uploaded_file is not None:
    df = load_data(uploaded_file)

    # --- SIDEBAR / FILTROS ---
    st.sidebar.header("Filtros")
    # Usando a coluna 'LOJAS' que identifiquei na sua planilha
    lojas_selecionadas = st.sidebar.multiselect(
        "Selecione as Lojas:",
        options=df["LOJAS"].unique(),
        default=df["LOJAS"].unique()[:5] # Padrão: primeiras 5 lojas
    )

    df_filtrado = df[df["LOJAS"].isin(lojas_selecionadas)]

    # --- KPIs PRINCIPAIS ---
    col1, col2, col3, col4 = st.columns(4)
    
    # Ajustado para os nomes exatos das colunas da sua planilha
    venda_total = df_filtrado["VENDA MAR'26"].sum()
    media_faturamento = df_filtrado["MÉDIA FATURAMENTO DE ABR'25 ATÉ MAR'26"].mean()
    populacao_total = df_filtrado["POPULAÇÃO RAIO DE 1KM"].sum()
    ticket_medio = df_filtrado["TICKET FSJ MAR'26"].replace('R\$ ', '', regex=True).replace(',', '.', regex=True).astype(float).mean()

    col1.metric("Venda Total (Mar/26)", f"R$ {venda_total:,.2f}")
    col2.metric("Média Fat. Anual", f"R$ {media_faturamento:,.2f}")
    col3.metric("Ticket Médio (FSJ)", f"R$ {ticket_medio:.2f}")
    col4.metric("População (Raio 1km)", f"{int(populacao_total):,}")

    st.divider()

    # --- GRÁFICOS ---
    c1, c2 = st.columns(2)

    with c1:
        fig_vendas = px.bar(
            df_filtrado, 
            x="LOJAS", 
            y="VENDA MAR'26", 
            title="Vendas por Loja (Março/2026)",
            color="VENDA MAR'26",
            color_continuous_scale="Blues"
        )
        st.plotly_chart(fig_vendas, use_container_width=True)

    with c2:
        fig_pop = px.scatter(
            df_filtrado,
            x="POPULAÇÃO RAIO DE 1KM",
            y="VENDA MAR'26",
            size="CLIENTES MAR'26",
            color="CIDADE",
            hover_name="LOJAS",
            title="Relação: População vs Vendas"
        )
        st.plotly_chart(fig_pop, use_container_width=True)

    st.subheader("Dados Detalhados")
    st.dataframe(df_filtrado)

else:
    st.info("💡 Por favor, faça o upload do arquivo 'Teste de lojas.xlsx' na barra lateral para começar.")
    # Exemplo visual de como deve ser a planilha
    st.image("https://streamlit.io/images/brand/streamlit-logo-secondary-colormark-darktext.png", width=200)
