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
        df["TICKET FSJ MAR'26"] = pd.to_numeric(df["TICKET FSJ MAR'26"], errors='coerce').fillna(0)
    
    # Garante que colunas de localização sejam strings
    for col in ["UF", "CIDADE", "MESORREGIÃO", "LOJAS"]:
        if col in df.columns:
            df[col] = df[col].astype(str).replace('nan', 'Não Informado')
            
    return df

if uploaded_file is not None:
    df = load_data(uploaded_file)

    # --- SIDEBAR / FILTROS ---
    st.sidebar.header("Filtros de Localização")

    estados = sorted([x for x in df["UF"].unique() if x])
    estados_selecionados = st.sidebar.multiselect("Selecione o Estado (UF):", options=estados, default=estados)

    df_uf = df[df["UF"].isin(estados_selecionados)]
    
    cidades = sorted([x for x in df_uf["CIDADE"].unique() if x])
    cidades_selecionadas = st.sidebar.multiselect("Selecione a Cidade:", options=cidades, default=cidades)

    mesos_list = [x for x in df_uf["MESORREGIÃO"].unique() if x and x != 'Não Informado']
    mesos = sorted(mesos_list)
    mesos_selecionados = st.sidebar.multiselect("Selecione a Mesorregião:", options=mesos, default=mesos)

    # Filtragem Final
    df_filtrado = df_uf[
        (df_uf["CIDADE"].isin(cidades_selecionadas)) & 
        (df_uf["MESORREGIÃO"].isin(mesos_selecionados))
    ]

    if not df_filtrado.empty:
        # --- KPIs PRINCIPAIS ---
        # Aumentei para 6 colunas para caber os novos indicadores
        m1, m2, m3, m4, m5, m6 = st.columns(6)
        
        venda_total = df_filtrado["VENDA MAR'26"].sum()
        qtd_lojas = df_filtrado["LOJAS"].nunique()
        # Média de DRE (Multiplicado por 100 para exibir % se estiver em decimal)
        media_dre = df_filtrado["DRE FEV'26"].mean() * 100 
        ticket_medio = df_filtrado["TICKET FSJ MAR'26"].mean()
        media_faturamento = df_filtrado["MÉDIA FATURAMENTO DE ABR'25 ATÉ MAR'26"].mean()
        populacao_total = df_filtrado["POPULAÇÃO RAIO DE 1KM"].sum()

        m1.metric("Qtd de Lojas", f"{qtd_lojas}")
        m2.metric("Venda Total (Mar/26)", f"R$ {venda_total/1_000_000:.1f}M")
        m3.metric("Média DRE", f"{media_dre:.2f}%")
        m4.metric("Ticket Médio", f"R$ {ticket_medio:.2f}")
        m5.metric("Média Fat. Anual", f"R$ {media_faturamento:,.0f}")
        m6.metric("População Total", f"{int(populacao_total):,}")

        st.divider()

        # --- ANÁLISE POR MESORREGIÕES ---
        st.subheader("🌐 Análise por Mesorregiões")
        
        df_meso = df_filtrado.groupby("MESORREGIÃO").agg({
            "VENDA MAR'26": "sum",
            "LOJAS": "count",
            "DRE FEV'26": "mean"
        }).reset_index()
        df_meso["DRE %"] = df_meso["DRE FEV'26"] * 100

        col_m1, col_m2 = st.columns([2, 1])
        with col_m1:
            # Gráfico de Vendas por Meso
            fig_meso = px.bar(df_meso, x="MESORREGIÃO", y="VENDA MAR'26", color="DRE %", 
                             text_auto='.2s', title="Vendas por Mesorregião (Cor = Média DRE %)", 
                             color_continuous_scale="RdYlGn")
            st.plotly_chart(fig_meso, use_container_width=True)
        with col_m2:
            fig_pie_meso = px.pie(df_meso, values="VENDA MAR'26", names="MESORREGIÃO", 
                                 title="% Participação nas Vendas", hole=0.4)
            st.plotly_chart(fig_pie_meso, use_container_width=True)

        # --- DETALHAMENTO ---
        st.divider()
        st.subheader("📍 Detalhamento por Loja")
        c1, c2 = st.columns(2)
        with c1:
            fig_vendas = px.bar(df_filtrado.sort_values("VENDA MAR'26", ascending=False), 
                               x="LOJAS", y="VENDA MAR'26", color="DRE FEV'26", 
                               title="Ranking de Vendas (Cor = Lucratividade DRE)")
            st.plotly_chart(fig_vendas, use_container_width=True)
        with c2:
            fig_pop = px.scatter(df_filtrado, x="POPULAÇÃO RAIO DE 1KM", y="VENDA MAR'26",
                                size="CLIENTES MAR'26", color="MESORREGIÃO", hover_name="LOJAS",
                                title="Eficiência: População vs Vendas")
            st.plotly_chart(fig_pop, use_container_width=True)

        st.subheader("📋 Dados Selecionados")
        st.dataframe(df_filtrado, use_container_width=True)
    else:
        st.warning("⚠️ Nenhum dado encontrado para os filtros selecionados.")

else:
    st.info("💡 Por favor, faça o upload do arquivo 'Teste de lojas.xlsx' na barra lateral.")
