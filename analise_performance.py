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
    # Limpa espaços em branco nos nomes das colunas
    df.columns = df.columns.astype(str).str.strip()
    
    # MAPEAMENTO DAS COLUNAS
    col_fat = "MÉDIA FATURAMENTO DE MAR'25 ATÉ FEV'26"
    col_uf = "UF"
    col_porte = "TAMANHO DA CIDADE"
    col_posicao = "POSIÇÃO DA LOJA"
    col_estacionamento = "ESTACIONAMENTO"
    col_loja = "LOJAS"

    # --- BARRA LATERAL (FILTROS) ---
    st.sidebar.header("⚙️ Filtros e Parâmetros")
    
    # Opção de olhar por estado ou todas juntas
    lista_ufs = sorted(df[col_uf].dropna().unique().tolist())
    opcao_uf = st.sidebar.selectbox("Selecione o Estado:", ["Todos os Estados"] + lista_ufs)
    
    # Filtragem do DataFrame
    if opcao_uf == "Todos os Estados":
        df_view = df.copy()
    else:
        df_view = df[df[col_uf] == opcao_uf].copy()

    # Régua de Sucesso
    media_geral = float(df[col_fat].mean())
    meta_sucesso = st.sidebar.slider(
        "Régua de Alta Performance (Referência Nacional)", 
        min_value=float(df[col_fat].min()), 
        max_value=float(df[col_fat].max()), 
        value=media_geral
    )

    # Classificação de Performance
    df_view['Performance'] = df_view[col_fat].apply(lambda x: '💎 Alta' if x >= meta_sucesso else '📉 Comum')

    # --- INDICADORES RÁPIDOS (KPIs) ---
    c1, c2, c3, c4 = st.columns(4)
    
    qtd_total = len(df_view)
    qtd_alta_perf = len(df_view[df_view['Performance'] == '💎 Alta'])
    fat_medio_local = df_view[col_fat].mean()
    taxa_sucesso = (qtd_alta_perf / qtd_total * 100) if qtd_total > 0 else 0

    with c1:
        st.metric("Total de Lojas", qtd_total)
    with c2:
        diff_media = fat_medio_local - media_geral
        st.metric("Faturamento Médio", f"R$ {fat_medio_local:,.2f}", delta=f"{diff_media:,.2f} vs Rede")
    with c3:
        st.metric("Lojas em Alta Performance", qtd_alta_perf)
    with c4:
        st.metric("% de Sucesso", f"{taxa_sucesso:.1f}%")

    # --- ABAS DE ANÁLISE ---
    tab_geo, tab_dna, tab_listagem = st.tabs(["🌎 Visão Geográfica", "🧬 DNA do Sucesso", "📋 Lista Detalhada"])

    with tab_geo:
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.subheader("Performance por Estado")
            fig_uf = px.histogram(df_view, x=col_uf, color="Performance", barmode="group",
                                  color_discrete_map={'💎 Alta': '#27ae60', '📉 Comum': '#e74c3c'}, 
                                  text_auto=True)
            st.plotly_chart(fig_uf, use_container_width=True)
        with col_g2:
            st.subheader("Sucesso por Porte de Cidade")
            fig_porte = px.histogram(df_view, x=col_porte, color="Performance", 
                                     barmode="group", barnorm="percent",
                                     color_discrete_map={'💎 Alta': '#27ae60', '📉 Comum': '#e74c3c'})
            st.plotly_chart(fig_porte, use_container_width=True)

    with tab_dna:
        st.subheader("O que as melhores lojas têm em comum?")
        analise_alvo = st.selectbox("Cruzar performance com:", [col_posicao, col_estacionamento, col_porte])
        
        fig_dna = px.box(df_view, x=analise_alvo, y=col_fat, color="Performance",
                        color_discrete_map={'💎 Alta': '#27ae60', '📉 Comum': '#e74c3c'},
                        points="all")
        st.plotly_chart(fig_dna, use_container_width=True)
        
        tops = df_view[df_view['Performance'] == '💎 Alta']
        if not tops.empty:
            melhor_valor = tops[analise_alvo].mode()[0]
            st.success(f"💡 Padrão de Sucesso em **{opcao_uf}**: Lojas **{melhor_valor}** tendem a ser as melhores em **{analise_alvo}**.")

    with tab_listagem:
        st.subheader(f"Lista de Lojas: {opcao_uf}")
        st.dataframe(df_view[[col_loja, col_uf, col_fat, 'Performance', col_posicao]].sort_values(by=col_fat, ascending=False), use_container_width=True)

else:
    st.info("👋 Por favor, faça o upload do arquivo Excel para começar.")
