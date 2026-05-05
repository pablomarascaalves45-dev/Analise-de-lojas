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
    
    # Tratamento do Ticket Médio
    if "TICKET FSJ MAR'26" in df.columns:
        df["TICKET FSJ MAR'26"] = (
            df["TICKET FSJ MAR'26"]
            .astype(str)
            .str.replace('R\$ ', '', regex=True)
            .str.replace('.', '', regex=False)
            .str.replace(',', '.', regex=False)
            .str.strip()
        )
        # Converte para float e preenche erro com 0
        df["TICKET FSJ MAR'26"] = pd.to_numeric(df["TICKET FSJ MAR'26"], errors='coerce').fillna(0)
    
    # Garante que colunas de localização sejam strings e sem nulos para não quebrar o sorted
    for col in ["UF", "CIDADE", "MESORREGIÃO", "LOJAS"]:
        if col in df.columns:
            df[col] = df[col].astype(str).replace('nan', 'Não Informado')
            
    return df

if uploaded_file is not None:
    df = load_data(uploaded_file)

    # --- SIDEBAR / FILTROS ---
    st.sidebar.header("Filtros de Localização")

    # 1. Filtro de UF
    estados = sorted([x for x in df["UF"].unique() if x])
    estados_selecionados = st.sidebar.multiselect("Selecione o Estado (UF):", options=estados, default=estados)

    # Filtragem intermediária por UF
    df_uf = df[df["UF"].isin(estados_selecionados)]
    
    # 2. Filtro de Cidade (Garante que não há erro se df_uf estiver vazio)
    cidades = sorted([x for x in df_uf["CIDADE"].unique() if x])
    cidades_selecionadas = st.sidebar.multiselect("Selecione a Cidade:", options=cidades, default=cidades)

    # 3. Filtro de Mesorregião (CORREÇÃO DO ERRO DO SORTED)
    # Filtramos apenas valores válidos e transformamos em lista para o sorted
    mesos_list = [x for x in df_uf["MESORREGIÃO"].unique() if x and x != 'Não Informado']
    mesos = sorted(mesos_list)
    mesos_selecionados = st.sidebar.multiselect("Selecione a Mesorregião:", options=mesos, default=mesos)

    # Filtragem Final
    df_filtrado = df_uf[
        (df_uf["CIDADE"].isin(cidades_selecionadas)) & 
        (df_uf["MESORREGIÃO"].isin(mesos_selecionados))
    ]

    # Verifica se o filtro retornou algo para não dar erro nos cálculos
    if not df_filtrado.empty:
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
        
        df_meso = df_filtrado.groupby("MESORREGIÃO").agg({
            "VENDA MAR'26": "sum",
            "LOJAS": "count"
        }).reset_index()
        df_meso.columns = ["Mesorregião", "Total Vendas", "Qtd Lojas"]

        col_m1, col_m2 = st.columns([2, 1])
        with col_m1:
            fig_meso = px.bar(df_meso, x="Mesorregião", y="Total Vendas", color="Total Vendas", 
                             text_auto='.2s', title="Vendas por Mesorregião", color_continuous_scale="Viridis")
            st.plotly_chart(fig_meso, use_container_width=True)
        with col_m2:
            fig_pie_meso = px.pie(df_meso, values="Total Vendas", names="Mesorregião", 
                                 title="% Participação", hole=0.4)
            st.plotly_chart(fig_pie_meso, use_container_width=True)

        # --- DETALHAMENTO ---
        st.divider()
        st.subheader("📍 Detalhamento por Loja")
        c1, c2 = st.columns(2)
        with c1:
            fig_vendas = px.bar(df_filtrado.sort_values("VENDA MAR'26", ascending=False), 
                               x="LOJAS", y="VENDA MAR'26", color="VENDA MAR'26", title="Ranking de Vendas")
            st.plotly_chart(fig_vendas, use_container_width=True)
        with c2:
            fig_pop = px.scatter(df_filtrado, x="POPULAÇÃO RAIO DE 1KM", y="VENDA MAR'26",
                                size="CLIENTES MAR'26", color="MESORREGIÃO", hover_name="LOJAS",
                                title="População vs Vendas")
            st.plotly_chart(fig_pop, use_container_width=True)

        st.subheader("📋 Dados Selecionados")
        st.dataframe(df_filtrado, use_container_width=True)
    else:
        st.warning("⚠️ Nenhum dado encontrado para os filtros selecionados.")

else:
    st.info("💡 Por favor, faça o upload do arquivo 'Teste de lojas.xlsx' na barra lateral.")
