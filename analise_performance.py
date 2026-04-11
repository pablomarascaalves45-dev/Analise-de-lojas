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
    lista_ufs = sorted(df[col_uf].dropna().unique().tolist())
    opcao_uf = st.sidebar.selectbox("Selecione o Estado:", ["Todos os Estados"] + lista_ufs)
    
    if opcao_uf == "Todos os Estados":
        df_view = df.copy()
    else:
        df_view = df[df[col_uf] == opcao_uf].copy()

    # --- LÓGICA DE CLASSIFICAÇÃO PERSONALIZADA ---
    def classificar_performance(row):
        faturamento = row[col_fat]
        dre = row[col_dre]
        
        if faturamento < 400000:
            if dre < 0:
                return '🔴 Ruim'
            else:
                return '🟡 Baixa'
        else:
            return '💎 Alta'

    df_view['Performance'] = df_view.apply(classificar_performance, axis=1)

    # --- INDICADORES RÁPIDOS (KPIs) ---
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total de Lojas", len(df_view))
    with c2:
        qtd_ruim = len(df_view[df_view['Performance'] == '🔴 Ruim'])
        st.metric("Lojas 'Ruins' (Venda < 400k + DRE < 0)", qtd_ruim)
    with c3:
        qtd_baixa = len(df_view[df_view['Performance'] == '🟡 Baixa'])
        st.metric("Lojas 'Baixas' (Venda < 400k)", qtd_baixa)
    with c4:
        st.metric("Faturamento Médio", f"R$ {df_view[col_fat].mean():,.2f}")

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
            st.subheader("Faturamento vs DRE")
            fig_scat = px.scatter(df_view, x=col_fat, y=col_dre, color="Performance", hover_name=col_loja,
                                 color_discrete_map={'💎 Alta': '#27ae60', '🟡 Baixa': '#f1c40f', '🔴 Ruim': '#e74c3c'})
            fig_scat.add_hline(y=0, line_dash="dash", line_color="red")
            fig_scat.add_vline(x=400000, line_dash="dash", line_color="orange")
            st.plotly_chart(fig_scat, use_container_width=True)

    with tab_dna:
        st.subheader("Quais características levam a lojas 'Ruins' ou 'Altas'?")
        analise_alvo = st.selectbox("Cruzar com:", [col_posicao, col_estacionamento, col_porte])
        fig_dna = px.histogram(df_view, x=analise_alvo, color="Performance", barmode="percent",
                               color_discrete_map={'💎 Alta': '#27ae60', '🟡 Baixa': '#f1c40f', '🔴 Ruim': '#e74c3c'})
        st.plotly_chart(fig_dna, use_container_width=True)

    with tab_listagem:
        st.subheader(f"Detalhamento das Lojas - {opcao_uf}")
        # Formatação para exibição
        df_display = df_view[[col_loja, col_uf, col_fat, col_dre, 'Performance', col_posicao]].copy()
        df_display[col_dre] = df_display[col_dre].map("{:.2%}".format)
        df_display[col_fat] = df_display[col_fat].map("R$ {:,.2f}".format)
        
        st.dataframe(df_display.sort_values(by='Performance'), use_container_width=True)

else:
    st.info("👋 Suba o Excel para visualizar a análise de DRE e Performance.")
