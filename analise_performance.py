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
    col_uf = "UF"
    col_porte = "TAMANHO DA CIDADE"
    col_posicao = "POSIÇÃO DA LOJA"
    col_estacionamento = "ESTACIONAMENTO"
    col_loja = "LOJAS"

    # --- BARRA LATERAL (FILTROS) ---
    st.sidebar.header("⚙️ Filtros e Parâmetros")
    
    # Filtro de Estado com opção "Todos"
    lista_ufs = sorted(df[col_uf].unique().tolist())
    opcao_uf = st.sidebar.selectbox("Selecione o Estado:", ["Todos os Estados"] + lista_ufs)
    
    # Aplicação do Filtro
    if opcao_uf == "Todos os Estados":
        df_view = df.copy()
    else:
        df_view = df[df[col_uf] == opcao_uf].copy()

    # Régua de Sucesso (calculada sempre sobre o DF TOTAL para manter a referência nacional)
    media_geral = float(df[col_fat].mean())
    meta_sucesso = st.sidebar.slider(
        "Régua de Alta Performance (Referência Nacional)", 
        min_value=float(df[col_fat].min()), 
        max_value=float(df[col_fat].max()), 
        value=media_geral
    )

    df_view['Performance'] = df_view[col_fat].apply(lambda x: '💎 Alta' if x >= meta_sucesso else '📉 Comum')

    # --- KPIs ---
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Qtd de Lojas", len(df_view))
    with c2:
        faturamento_medio = df_view[col_fat].mean()
        diff = faturamento_medio - media_geral
        st.metric("Faturamento Médio", f"R$ {faturamento_medio:,.2f}", delta=f"{diff:,.2f} vs Média Geral")
    with c3:
        qtd_alta = len(df_view[df_view['Performance'] == '💎 Alta'])
        st.metric("Lojas em Alta Performance", qtd_alta)
    with c4:
        %_sucesso = (qtd_alta / len(df_view)) * 100 if len(df_view) > 0 else 0
        st.metric("% de Sucesso no Filtro", f"{%_sucesso:.1f}%")

    # --- ABAS DE ANÁLISE ---
    tab_geo, tab_dna, tab_listagem = st.tabs(["🌎 Visão Geográfica", "🧬 DNA do Sucesso", "📋 Lista Detalhada"])

    with tab_geo:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Performance por UF")
            # Mostra todas as UFs do filtro atual
            fig_uf = px.histogram(df_view, x=col_uf, color="Performance", barmode="group",
                                  color_discrete_map={'💎 Alta': '#27ae60', '📉 Comum': '#e74c3c'}, 
                                  text_auto=True)
            st.plotly_chart(fig_uf, use_container_width=True)
        with col2:
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
        
        # Insight inteligente
        tops = df_view[df_view['Performance'] == '💎 Alta']
        if not tops.empty:
            melhor_valor = tops[analise_alvo].mode()[0]
            st.success(f"💡 No filtro **{opcao_uf}**, o padrão de sucesso em **{analise_alvo}** é: **{melhor_valor}**.")

    with tab_listagem:
        st.subheader(f"Listagem de Lojas - {opcao_uf}")
        st.dataframe(df_view[[col_loja, col_uf, col_fat, 'Performance', col_posicao]].sort_values(by=col_fat, ascending=False), use_container_width=True)

else:
    st.info("Aguardando upload do arquivo Excel...")
