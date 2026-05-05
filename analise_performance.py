import streamlit as st
import pandas as pd
import plotly.express as px

# Se você puder instalar: pip install streamlit-plotly-events
# Caso contrário, usaremos a lógica de filtros vinculados abaixo

st.set_page_config(page_title="Laboratório de Lojas", layout="wide")

st.title("📊 Laboratório de Performance de Lojas")

# --- COMPONENTE DE UPLOAD ---
uploaded_file = st.sidebar.file_uploader("Suba sua planilha 'Teste de lojas.xlsx' aqui", type=["xlsx"])

def load_data(file):
    df = pd.read_excel(file)
    df.columns = [c.strip() for c in df.columns]
    
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
    
    for col in ["UF", "CIDADE", "MESORREGIÃO", "LOJAS", "TAMANHO DA CIDADE"]:
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
    
    # --- NOVO: FILTRO DINÂMICO DE PORTE (Aumenta a interatividade) ---
    st.sidebar.subheader("Filtrar por Porte")
    portes_disponiveis = sorted(df_uf["TAMANHO DA CIDADE"].unique())
    # "Todos" por padrão para não limitar a visão inicial
    portes_selecionados = st.sidebar.multiselect("Porte da Cidade:", options=portes_disponiveis, default=portes_disponiveis)

    df_filtrado_base = df_uf[df_uf["TAMANHO DA CIDADE"].isin(portes_selecionados)]

    cidades = sorted([x for x in df_filtrado_base["CIDADE"].unique() if x])
    cidades_selecionadas = st.sidebar.multiselect("Selecione a Cidade:", options=cidades, default=cidades)

    mesos_list = [x for x in df_filtrado_base["MESORREGIÃO"].unique() if x and x != 'Não Informado']
    mesos = sorted(mesos_list)
    mesos_selecionados = st.sidebar.multiselect("Selecione a Mesorregião:", options=mesos, default=mesos)

    # Filtragem Final que alimenta os gráficos
    df_visualizacao = df_filtrado_base[
        (df_filtrado_base["CIDADE"].isin(cidades_selecionadas)) & 
        (df_filtrado_base["MESORREGIÃO"].isin(mesos_selecionados))
    ]

    if not df_visual_final.empty:
        # --- KPIs PRINCIPAIS ---
        m1, m2, m3, m4, m5, m6 = st.columns(6)
        
        venda_total = df_visualizacao["VENDA MAR'26"].sum()
        qtd_lojas = df_visualizacao["LOJAS"].nunique()
        media_dre = df_visualizacao["DRE FEV'26"].mean() * 100 
        ticket_medio = df_visualizacao["TICKET FSJ MAR'26"].mean()
        media_faturamento = df_visualizacao["MÉDIA FATURAMENTO DE ABR'25 ATÉ MAR'26"].mean()
        media_populacao = df_visualizacao["POPULAÇÃO RAIO DE 1KM"].mean()

        m1.metric("Qtd de Lojas", f"{qtd_lojas}")
        m2.metric("Venda Total", f"R$ {venda_total/1_000_000:.1f}M")
        m3.metric("Média DRE", f"{media_dre:.2f}%")
        m4.metric("Ticket Médio", f"R$ {ticket_medio:.2f}")
        m5.metric("Média Fat. Anual", f"R$ {media_faturamento:,.0f}")
        m6.metric("Média População (1km)", f"{int(media_populacao):,}")

        st.divider()

        # --- SEÇÃO DE GRÁFICOS ---
        st.subheader("📈 Análise de Performance")
        
        # Criamos um "Filtro de Clique" visual usando um selectbox que age sobre a tabela
        # Isso simula o comportamento de clicar na legenda/barra do gráfico
        col_f1, col_f2 = st.columns([1, 1])
        
        with col_f1:
            # Opção para o usuário focar em um porte específico direto pelo gráfico
            foco_porte = st.selectbox("🎯 Clique para detalhar um Porte na tabela:", 
                                     ["Ver Todos"] + portes_disponiveis)
            
            df_grafico = df_visualizacao.groupby(["MESORREGIÃO", "TAMANHO DA CIDADE"])["VENDA MAR'26"].mean().reset_index()
            fig_porte = px.bar(
                df_grafico, x="MESORREGIÃO", y="VENDA MAR'26", color="TAMANHO DA CIDADE",
                title="Faturamento Médio por Região e Porte", barmode="group",
                color_discrete_sequence=px.colors.qualitative.Prism
            )
            st.plotly_chart(fig_porte, use_container_width=True)

        with col_v2:
            fig_tree = px.treemap(
                df_visualizacao, path=["MESORREGIÃO", "TAMANHO DA CIDADE", "CIDADE"], 
                values="VENDA MAR'26", color="DRE FEV'26", color_continuous_scale="RdYlGn",
                title="Hierarquia de Lojas e Rentabilidade"
            )
            st.plotly_chart(fig_tree, use_container_width=True)

        # --- LÓGICA DE FILTRAGEM DA TABELA ---
        if foco_porte == "Ver Todos":
            df_tabela_final = df_visualizacao
        else:
            df_tabela_final = df_visualizacao[df_visualizacao["TAMANHO DA CIDADE"] == foco_porte]

        st.divider()
        st.subheader(f"📋 Dados Detalhados: {foco_porte}")
        st.dataframe(df_tabela_final, use_container_width=True)
        
    else:
        st.warning("⚠️ Nenhum dado encontrado para os filtros selecionados.")
else:
    st.info("💡 Por favor, faça o upload do arquivo na barra lateral.")
