import pandas as pd
import plotly.express as px
import streamlit as st

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Analytics Expansão - DNA de Sucesso", layout="wide")

st.title("🎯 Inteligência de Performance: O que faz uma loja vender mais?")
st.markdown("---")

# 2. UPLOAD E TRATAMENTO DE DADOS
uploaded_file = st.file_uploader("📂 Suba a base de dados das lojas (Excel)", type=['xlsx'])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.astype(str).str.strip()
    
    # MAPEAMENTO DAS COLUNAS
    col_fat = "MÉDIA FATURAMENTO DE MAR'25 ATÉ FEV'26"
    col_dre = "DRE_AC FEV/26"
    col_uf = "UF"
    col_porte = "TAMANHO DA CIDADE"
    col_posicao = "POSIÇÃO DA LOJA"
    col_estacionamento = "ESTACIONAMENTO"
    col_loja = "LOJAS"

    # --- BARRA LATERAL (FILTROS) ---
    st.sidebar.header("⚙️ Filtros")
    
    # Filtro 1: Estado
    lista_ufs = sorted(df[col_uf].dropna().unique().tolist())
    opcao_uf = st.sidebar.selectbox("Selecione o Estado:", ["Todos os Estados"] + lista_ufs)
    
    if opcao_uf == "Todos os Estados":
        df_filtrado = df.copy()
    else:
        df_filtrado = df[df[col_uf] == opcao_uf].copy()

    # Filtro 2: Faturamento (Slider de Intervalo)
    fat_min_data = float(df_filtrado[col_fat].min())
    fat_max_data = float(df_filtrado[col_fat].max())
    
    faixa_faturamento = st.sidebar.slider(
        "Filtrar por Faixa de Faturamento:",
        min_value=fat_min_data,
        max_value=fat_max_data,
        value=(fat_min_data, fat_max_data),
        format="R$ {:,.0f}"
    )
    
    # EXIBIÇÃO DO VALOR SELECIONADO (O que você pediu)
    st.sidebar.write(f"📊 **Selecionado:** R$ {faixa_faturamento[0]:,.0f} até R$ {faixa_faturamento[1]:,.0f}")
    
    # Aplicação final dos filtros
    df_view = df_filtrado[
        (df_filtrado[col_fat] >= faixa_faturamento[0]) & 
        (df_filtrado[col_fat] <= faixa_faturamento[1])
    ].copy()

    # --- LÓGICA DE CLASSIFICAÇÃO (REGRA 400K + DRE) ---
    def classificar_performance(row):
        faturamento = row[col_fat]
        dre = row[col_dre]
        if faturamento < 400000:
            return '🔴 Ruim' if dre < 0 else '🟡 Baixa'
        return '💎 Alta'

    df_view['Performance'] = df_view.apply(classificar_performance, axis=1)

    # --- KPIs ---
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total de Lojas", len(df_view))
    with c2:
        qtd_ruim = len(df_view[df_view['Performance'] == '🔴 Ruim'])
        st.metric("Lojas 'Ruins'", qtd_ruim)
    with c3:
        qtd_baixa = len(df_view[df_view['Performance'] == '🟡 Baixa'])
        st.metric("Lojas 'Baixas'", qtd_baixa)
    with c4:
        media_fat = df_view[col_fat].mean() if not df_view.empty else 0
        st.metric("Faturamento Médio", f"R$ {media_fat:,.2f}")

    # --- ABAS DE ANÁLISE ---
    tab_geo, tab_dna, tab_listagem = st.tabs(["🌎 Visão Geográfica", "🧬 DNA do Sucesso", "📋 Tabela Detalhada (DRE)"])

    with tab_geo:
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.subheader("Performance por Estado")
            fig_uf = px.histogram(df_view, x=col_uf, color="Performance", barmode="group",
                                  color_discrete_map={'💎 Alta': '#27ae60', '🟡 Baixa': '#f1c40f', '🔴 Ruim': '#e74c3c'}, 
                                  text_auto=True)
            st.plotly_chart(fig_uf, use_container_width=True)
        with col_g2:
            st.subheader("Dispersão: Faturamento vs DRE")
            fig_scat = px.scatter(df_view, x=col_fat, y=col_dre, color="Performance", hover_name=col_loja,
                                 color_discrete_map={'💎 Alta': '#27ae60', '🟡 Baixa': '#f1c40f', '🔴 Ruim': '#e74c3c'})
            fig_scat.add_hline(y=0, line_dash="dash", line_color="red")
            fig_scat.add_vline(x=400000, line_dash="dash", line_color="orange")
            st.plotly_chart(fig_scat, use_container_width=True)

    with tab_dna:
        st.subheader("Análise de Padrões (Proporção)")
        analise_alvo = st.selectbox("Cruzar performance com:", [col_posicao, col_estacionamento, col_porte])
        
        fig_dna = px.histogram(df_view, x=analise_alvo, color="Performance", 
                               barmode="group", barnorm="percent",
                               color_discrete_map={'💎 Alta': '#27ae60', '🟡 Baixa': '#f1c40f', '🔴 Ruim': '#e74c3c'})
        st.plotly_chart(fig_dna, use_container_width=True)

    with tab_listagem:
        st.subheader(f"Lista de Lojas Filtradas")
        df_display = df_view[[col_loja, col_uf, col_fat, col_dre, 'Performance', col_posicao]].copy()
        df_display[col_dre] = df_display[col_dre].map("{:.2%}".format)
        df_display[col_fat] = df_display[col_fat].map("R$ {:,.2f}".format)
        st.dataframe(df_display.sort_values(by=col_fat, ascending=False), use_container_width=True)

else:
    st.info("👋 Suba o arquivo Excel para iniciar a filtragem e análise.")
