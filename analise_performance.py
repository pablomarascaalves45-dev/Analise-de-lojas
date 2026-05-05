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

        # --- SEÇÃO DE ANÁLISE DE PERFORMANCE POR MÉDIA (EFICIÊNCIA) ---
        st.subheader("🏆 Insights de Melhor Performance (Média por Loja)")
        
        # Agrupamento por Mesorregião usando a MÉDIA
        perf_meso_med = df_filtrado.groupby("MESORREGIÃO")["VENDA MAR'26"].mean().sort_values(ascending=False)
        melhor_meso_med = perf_meso_med.index[0]
        venda_med_meso = perf_meso_med.values[0]

        # Agrupamento por Cidade/Porte usando a MÉDIA
        perf_cid_med = df_filtrado.groupby(["CIDADE", "MESORREGIÃO", "TAMANHO DA CIDADE"])["VENDA MAR'26"].mean().reset_index()
        perf_cid_med = perf_cid_med.sort_values(by="VENDA MAR'26", ascending=False).iloc[0]

        c_ins1, c_ins2, c_ins3 = st.columns(3)
        
        with c_ins1:
            st.info(f"**Mesorregião mais Eficiente:**\n\n{melhor_meso_med}")
            st.caption(f"Média por Loja: R$ {venda_med_meso:,.2f}")
        
        with c_ins2:
            st.success(f"**Cidade com Maior Média:**\n\n{perf_cid_med['CIDADE']}")
            st.caption(f"Mesorregião: {perf_cid_med['MESORREGIÃO']}")

        with c_ins3:
            st.warning(f"**Porte da Cidade Líder (Média):**\n\n{perf_cid_med['TAMANHO DA CIDADE']}")
            st.caption("Faturamento médio superior")

        st.divider()

        # --- ANÁLISE VISUAL POR MÉDIA ---
        st.subheader("📈 Eficiência por Porte e Região (Faturamento Médio)")
        col_v1, col_v2 = st.columns(2)

        with col_v1:
            # Gráfico de barras com a MÉDIA de faturamento
            df_porte_med = df_filtrado.groupby(["MESORREGIÃO", "TAMANHO DA CIDADE"])["VENDA MAR'26"].mean().reset_index()
            fig_porte_med = px.bar(
                df_porte_med, 
                x="MESORREGIÃO", 
                y="VENDA MAR'26", 
                color="TAMANHO DA CIDADE",
                title="Faturamento Médio: Região vs Porte da Cidade",
                barmode="group",
                color_discrete_sequence=px.colors.qualitative.Prism,
                labels={"VENDA MAR'26": "Faturamento Médio (R$)"}
            )
            st.plotly_chart(fig_porte_med, use_container_width=True)

        with col_v2:
            # Treemap baseado na MÉDIA de faturamento
            fig_tree_med = px.treemap(
                df_filtrado, 
                path=["MESORREGIÃO", "TAMANHO DA CIDADE", "CIDADE"], 
                values="VENDA MAR'26", # O Treemap soma por padrão, mas a visualização hierárquica ainda é válida
                color="DRE FEV'26",
                color_continuous_scale="RdYlGn",
                title="Hierarquia de Lojas e Rentabilidade"
            )
            st.plotly_chart(fig_tree_med, use_container_width=True)

        st.subheader("📋 Dados Detalhados")
        st.dataframe(df_filtrado, use_container_width=True)
    else:
        st.warning("⚠️ Nenhum dado encontrado para os filtros selecionados.")

else:
    st.info("💡 Por favor, faça o upload do arquivo 'Teste de lojas.xlsx' na barra lateral.")
