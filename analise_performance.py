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
    cidades = sorted([x for x in df_uf["CIDADE"].unique() if x])
    cidades_selecionadas = st.sidebar.multiselect("Selecione a Cidade:", options=cidades, default=cidades)

    mesos_list = [x for x in df_uf["MESORREGIÃO"].unique() if x and x != 'Não Informado']
    mesos = sorted(mesos_list)
    mesos_selecionados = st.sidebar.multiselect("Selecione a Mesorregião:", options=mesos, default=mesos)

    df_filtrado = df_uf[
        (df_uf["CIDADE"].isin(cidades_selecionadas)) & 
        (df_uf["MESORREGIÃO"].isin(mesos_selecionados))
    ]

    if not df_filtrado.empty:
        # --- KPIs PRINCIPAIS ---
        m1, m2, m3, m4, m5, m6 = st.columns(6)
        
        venda_total = df_filtrado["VENDA MAR'26"].sum()
        qtd_lojas = df_filtrado["LOJAS"].nunique()
        media_dre = df_filtrado["DRE FEV'26"].mean() * 100 
        ticket_medio = df_filtrado["TICKET FSJ MAR'26"].mean()
        media_faturamento = df_filtrado["MÉDIA FATURAMENTO DE ABR'25 ATÉ MAR'26"].mean()
        populacao_total = df_filtrado["POPULAÇÃO RAIO DE 1KM"].sum()

        m1.metric("Qtd de Lojas", f"{qtd_lojas}")
        m2.metric("Venda Total", f"R$ {venda_total/1_000_000:.1f}M")
        m3.metric("Média DRE", f"{media_dre:.2f}%")
        m4.metric("Ticket Médio", f"R$ {ticket_medio:.2f}")
        m5.metric("Média Fat. Anual", f"R$ {media_faturamento:,.0f}")
        m6.metric("População Total", f"{int(populacao_total):,}")

        st.divider()

        # --- SEÇÃO DE ANÁLISE DE PERFORMANCE AUTOMÁTICA ---
        st.subheader("🏆 Insights de Melhor Performance")
        
        # Agrupamento para encontrar a melhor Mesorregião
        perf_meso = df_filtrado.groupby("MESORREGIÃO")["VENDA MAR'26"].sum().sort_values(ascending=False)
        melhor_meso = perf_meso.index[0]
        venda_melhor_meso = perf_meso.values[0]

        # Agrupamento para encontrar a melhor Cidade
        # Incluímos o 'TAMANHO DA CIDADE' para responder à sua pergunta
        perf_cidade = df_filtrado.groupby(["CIDADE", "MESORREGIÃO", "TAMANHO DA CIDADE"])["VENDA MAR'26"].sum().reset_index()
        perf_cidade = perf_cidade.sort_values(by="VENDA MAR'26", ascending=False).iloc[0]

        c_ins1, c_ins2, c_ins3 = st.columns(3)
        
        with c_ins1:
            st.info(f"**Mesorregião Líder:**\n\n{melhor_meso}")
            st.caption(f"Faturamento: R$ {venda_melhor_meso:,.2f}")
        
        with c_ins2:
            st.success(f"**Cidade Líder em Vendas:**\n\n{perf_cidade['CIDADE']}")
            st.caption(f"Localizada em: {perf_cidade['MESORREGIÃO']}")

        with c_ins3:
            st.warning(f"**Porte da Cidade Líder:**\n\n{perf_cidade['TAMANHO DA CIDADE']}")
            st.caption("Classificação conforme base de dados")

        st.divider()

        # --- ANÁLISE VISUAL POR PORTE E MESORREGIÃO ---
        st.subheader("📈 Performance por Porte da Cidade e Região")
        col_v1, col_v2 = st.columns(2)

        with col_v1:
            # Gráfico de barras comparando faturamento por Mesorregião e Porte
            fig_porte = px.bar(
                df_filtrado, 
                x="MESORREGIÃO", 
                y="VENDA MAR'26", 
                color="TAMANHO DA CIDADE",
                title="Distribuição de Vendas: Região vs Porte da Cidade",
                barmode="group",
                color_discrete_sequence=px.colors.qualitative.Prism
            )
            st.plotly_chart(fig_porte, use_container_width=True)

        with col_v2:
            # Matriz de Performance (Treemap)
            fig_tree = px.treemap(
                df_filtrado, 
                path=["MESORREGIÃO", "TAMANHO DA CIDADE", "CIDADE"], 
                values="VENDA MAR'26",
                color="DRE FEV'26",
                color_continuous_scale="RdYlGn",
                title="Hierarquia de Performance (Tamanho = Venda | Cor = DRE %)"
            )
            st.plotly_chart(fig_tree, use_container_width=True)

        # --- GRÁFICOS ORIGINAIS (RANKING E DISPERSÃO) ---
        st.divider()
        st.subheader("📍 Detalhamento por Loja")
        c1, c2 = st.columns(2)
        with c1:
            fig_vendas = px.bar(df_filtrado.sort_values("VENDA MAR'26", ascending=False), 
                               x="LOJAS", y="VENDA MAR'26", color="VENDA MAR'26", title="Ranking Geral de Lojas")
            st.plotly_chart(fig_vendas, use_container_width=True)
        with c2:
            fig_pop = px.scatter(df_filtrado, x="POPULAÇÃO RAIO DE 1KM", y="VENDA MAR'26",
                                size="CLIENTES MAR'26", color="MESORREGIÃO", hover_name="LOJAS",
                                title="Eficiência: População vs Vendas")
            st.plotly_chart(fig_pop, use_container_width=True)

        st.subheader("📋 Dados Detalhados")
        st.dataframe(df_filtrado, use_container_width=True)
    else:
        st.warning("⚠️ Nenhum dado encontrado para os filtros selecionados.")

else:
    st.info("💡 Por favor, faça o upload do arquivo 'Teste de lojas.xlsx' na barra lateral.")
