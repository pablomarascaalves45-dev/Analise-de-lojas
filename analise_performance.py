import pandas as pd
import plotly.express as px
import streamlit as st

# Configuração da página
st.set_page_config(page_title="Análise de Performance - Lojas", layout="wide")
st.title("📊 Analisador de Padrões de Sucesso")

# Upload do arquivo
uploaded_file = st.file_uploader("Suba sua planilha de lojas (Excel)", type=['xlsx'])

if uploaded_file:
    # Lendo o Excel
    df = pd.read_excel(uploaded_file)
    
    st.subheader("👀 Visualização dos Dados")
    st.dataframe(df.head())

    # Nomes das colunas extraídos da sua imagem
    col_faturamento = "MÉDIA FATURAMENTO DE MAR'25 ATÉ FEV'26"
    
    if col_faturamento in df.columns:
        # 1. Definição da Régua de Sucesso
        min_f = float(df[col_faturamento].min())
        max_f = float(df[col_faturamento].max())
        
        st.sidebar.header("Configurações")
        meta = st.sidebar.slider("Meta de Faturamento (Alta Performance)", 
                                 min_value=min_f, 
                                 max_value=max_f, 
                                 value=df[col_faturamento].mean()) # Começa na média

        # Criando a classificação
        df['Performance'] = df[col_faturamento].apply(lambda x: '💎 Alta' if x >= meta else '📉 Comum')

        # 2. Seletor de Padrões para Análise
        # Usei os nomes das colunas que vi no seu print
        padrões = ['POSIÇÃO DA LOJA', 'ESTACIONAMENTO', 'TAMANHO DA CIDADE', 'UF', 'DISTRITAL', 'DIRETOR']
        
        col_escolhida = st.selectbox("Selecione um padrão para investigar:", padrões)

        # 3. Gráfico de Comparação
        st.subheader(f"🔍 Análise: {col_escolhida}")
        
        fig = px.histogram(
            df, 
            x=col_escolhida, 
            color="Performance", 
            barmode="group",
            text_auto=True,
            title=f"Distribuição de Lojas por {col_escolhida}",
            color_discrete_map={'💎 Alta': '#2ECC71', '📉 Comum': '#E74C3C'}
        )
        
        st.plotly_chart(fig, use_container_width=True)

        # 4. Insights Rápidos
        st.divider()
        st.subheader("💡 Insights Rápidos")
        
        top_padrao = df[df['Performance'] == '💎 Alta'][col_escolhida].mode()[0]
        st.write(f"Nas lojas de **Alta Performance**, o padrão que mais se repete em **{col_escolhida}** é: **{top_padrao}**.")

    else:
        st.error(f"Erro: A coluna '{col_faturamento}' não foi encontrada na planilha.")
else:
    st.info("Por favor, suba o arquivo 'Teste de lojas.xlsx' para começar.")
