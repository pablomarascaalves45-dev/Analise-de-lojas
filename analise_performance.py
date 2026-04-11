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
    # Lendo o arquivo
    df = pd.read_excel(uploaded_file)
    
    # LIMPEZA: Remove espaços extras nos nomes das colunas
    df.columns = df.columns.astype(str).str.strip()
    
    # MAPEAMENTO DAS COLUNAS
    col_fat = "MÉDIA FATURAMENTO DE MAR'25 ATÉ FEV'26"
    col_uf = "UF"
    col_porte = "TAMANHO DA CIDADE"
    col_posicao = "POSIÇÃO DA LOJA"
    col_estacionamento = "ESTACIONAMENTO"
    col_loja = "LOJAS"

    # Verificação de colunas
    colunas_focais = [col_fat, col_uf, col_porte, col_posicao]
    existentes = [c for c in colunas_focais if c in df.columns]
    
    if len(existentes) < len(colunas_focais):
        faltantes = list(set(colunas_focais) - set(existentes))
        st.error(f"⚠️ Colunas não encontradas: {faltantes}")
        st.write("Colunas disponíveis:", list(df.columns))
    else:
        # --- BARRA LATERAL ---
        st.sidebar.header("⚙️ Parâmetros")
        valor_min = float(df[col_fat].min())
        valor_max = float(df[col_fat].max())
        media_faturamento = float(df[col_fat].mean())
        
        meta_sucesso = st.sidebar.slider(
            "Régua de Alta Performance", 
            min_value=valor_min, 
            max_value=valor_max, 
            value=media_faturamento
        )

        df['Performance'] = df[col_fat].apply(lambda x: '💎 Alta' if x >= meta_sucesso else '📉 Comum')

        # --- DASHBOARD ---
        tab_geo, tab_dna, tab_listagem = st.tabs(["🌎 Onde estão?", "🧬 DNA do Sucesso", "📋 Lista"])

        with tab_geo:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Lojas por Estado")
                fig_uf = px.histogram(df, x=col_uf, color="Performance", barmode="group",
                                      color_discrete_map={'💎 Alta': '#27ae60', '📉 Comum': '#e74c3c'}, 
                                      text_auto=True)
                st.plotly_chart(fig_uf, use_container_width=True)
            with col2:
                st.subheader("Sucesso por Porte de Cidade")
                # CORREÇÃO AQUI: barmode="group" com barnorm="percent"
                fig_porte = px.histogram(df, x=col_porte, color="Performance", 
                                         barmode="group", barnorm="percent",
                                         color_discrete_map={'💎 Alta': '#27ae60', '📉 Comum': '#e74c3c'})
                st.plotly_chart(fig_porte, use_container_width=True)

        with tab_dna:
            st.subheader("Análise de Cruzamento")
            analise_alvo = st.selectbox("Analisar impacto de:", [col_posicao, col_estacionamento, col_porte])
            
            fig_dna = px.box(df, x=analise_alvo, y=col_fat, color="Performance",
                            color_discrete_map={'💎 Alta': '#27ae60', '📉 Comum': '#e74c3c'},
                            points="all")
            st.plotly_chart(fig_dna, use_container_width=True)
            
            tops = df[df['Performance'] == '💎 Alta']
            if not tops.empty:
                melhor_valor = tops[analise_alvo].mode()[0]
                st.success(f"💡 **DNA de Sucesso:** Lojas com característica **'{melhor_valor}'** dominam a categoria de Alta Performance em **{analise_alvo}**.")

        with tab_listagem:
            st.dataframe(df[[col_loja, col_uf, col_fat, 'Performance']].sort_values(by=col_fat, ascending=False), use_container_width=True)

else:
    st.info("Aguardando upload do arquivo Excel para iniciar a análise.")
