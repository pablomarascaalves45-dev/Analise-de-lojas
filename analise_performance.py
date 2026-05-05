import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Laboratório de Lojas", layout="wide")

st.title("📊 Laboratório de Performance de Lojas")

# --- COMPONENTE DE UPLOAD ---
uploaded_file = st.sidebar.file_uploader("Suba sua planilha 'Teste de lojas.xlsx' aqui", type=["xlsx"])

def load_data(file):
    df = pd.read_excel(file)
    df.columns = [c.strip() for c in df.columns]
    
    # Tratamento do Ticket Médio: Remove 'R$ ', troca vírgula por ponto e converte para float
    if "TICKET FSJ MAR'26" in df.columns:
        df["TICKET FSJ MAR'26"] = (
            df["TICKET FSJ MAR'26"]
            .astype(str)
            .str.replace('R\$ ', '', regex=True)
            .str.replace('.', '', regex=False)
            .str.replace(',', '.', regex=False)
            .astype(float)
        )
    return df

if uploaded_file is not None:
    df = load_data(uploaded_file)

    # --- SIDEBAR / FILTROS ---
    st.sidebar.header("Filtros de Localização")

    # 1. Filtro de UF (Estado)
    estados = sorted(df["UF"].unique().tolist())
    estados_selecionados = st.sidebar.multiselect("Selecione o Estado (UF):", options=estados, default=estados)

    # Filtrando cidades com base no estado selecionado
    df_uf = df[df["UF"].isin(estados_selecionados)]
    cidades = sorted(df_uf["CIDADE"].unique().tolist())
    
    # 2. Filtro de Cidade
    cidades_selecionadas = st.sidebar.multiselect("Selecione a Cidade:", options=cidades, default=cidades)

    # 3. Filtro de Mesorregião
    mesos = sorted(df_uf["MESORREGIÃO"].unique().tolist())
    mesos_selecionados = st.sidebar.multiselect("Selecione a Mesorregião:", options=mesos, default=mesos)

    # Filtragem Final do DataFrame
    df_filtrado = df_uf[
        (df_uf["CIDADE"].isin(cidades_selecionadas)) & 
        (df_uf["MESORREGIÃO"].isin(mesos_selecionados))
    ]

    # --- KPIs PRINCIPAIS ---
    col1, col2, col3, col4 = st.columns(4)
    
    venda_total = df_filtrado["VENDA MAR'26"].sum()
    media_faturamento = df_filtrado["MÉDIA FATURAMENTO DE ABR'25 ATÉ MAR'26"].mean()
    populacao_total = df_filtrado["POPULAÇÃO RAIO DE 1KM"].sum()
    ticket_medio = df_filtrado["TICKET FSJ MAR'26"].mean()

    col1.metric("Venda Total (Mar/26)", f"R$ {venda_total:,.2f}")
    col2.metric("Média Fat. Anual", f"R$ {media_faturamento:,.2f}")
    col3.metric("Ticket Médio (FSJ)", f"R$ {ticket_medio:.2f}")
    col4.metric("População (Raio 1km)", f"{int(populacao_total):,}")

    st.divider()

    # --- ANÁLISE POR MESORREGIÕES ---
    st.subheader("🌐 Análise por Mesorregiões")
    
    # Agrupando dados por mesorregião para o cenário
    df_meso = df_filtrado.groupby("MESORREGIÃO").agg({
        "VENDA MAR'26": "sum",
        "LOJAS": "count",
        "POPULAÇÃO RAIO DE 1KM": "sum"
    }).reset_index()
    df_meso.columns = ["Mesorregião", "Total Vendas", "Qtd Lojas", "População Total"]

    col_m1, col_m2 = st.columns([2, 1])

    with col_m1:
        fig_meso = px.bar(
            df_meso, 
            x="Mesorregião", 
            y="Total Vendas",
            color="Total Vendas",
            text_auto='.2s',
            title="Volume de Vendas por Mesorregião",
            color_continuous_scale="Viridis"
        )
        st.plotly_chart(fig_meso, use_container_width=True)

    with col_m2:
        fig_pie_meso = px.pie(
            df_meso, 
            values="Total Vendas", 
            names="Mesorregião", 
            title="% Participação de Vendas",
            hole=0.4
        )
        st.plotly_chart(fig_pie_meso, use_container_width=True)

    st.divider()

    # --- GRÁFICOS DE DETALHE ---
    st.subheader("📍 Detalhamento por Loja")
    c1, c2 = st.columns(2)

    with c1:
        fig_vendas = px.bar(
            df_filtrado.sort_values("VENDA MAR'26", ascending=False), 
            x="LOJAS", 
            y="VENDA MAR'26", 
            title="Vendas Individuais por Loja",
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
            color="MESORREGIÃO", # Cor por mesorregião para análise visual
            hover_name="LOJAS",
            title="Eficiência: População vs Vendas (por Mesorregião)"
        )
        st.plotly_chart(fig_pop, use_container_width=True)

    st.subheader("📋 Base de Dados Selecionada")
    st.dataframe(df_filtrado, use_container_width=True)

else:
    st.info("💡 Por favor, faça o upload do arquivo 'Teste de lojas.xlsx' na barra lateral para carregar os filtros.")
