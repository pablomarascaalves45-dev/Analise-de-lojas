import pandas as pd
import plotly.express as px
import streamlit as st

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Analytics Expansão - DNA de Sucesso", layout="wide")

# Estilização básica para melhorar a leitura
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 Inteligência de Performance: O que faz uma loja vender mais?")
st.markdown("---")

# 2. UPLOAD E TRATAMENTO DE DADOS
uploaded_file = st.file_uploader("📂 Suba a base de dados das lojas (Excel)", type=['xlsx'])

if uploaded_file:
    # Lendo o arquivo
    df = pd.read_excel(uploaded_file)
    
    # Mapeamento exato das colunas baseado na sua imagem
    col_fat = "MÉDIA FATURAMENTO DE MAR'25 ATÉ FEV'26"
    col_uf = "UF"
    col_porte = "TAMANHO DA CIDADE"
    col_posicao = "POSIÇÃO DA LOJA"
    col_estacionamento = "ESTACIONAMENTO"
    col_loja = "LOJAS"
    col_diretor = "DIRETOR"

    # Criar coluna de Região (ajuste conforme sua necessidade)
    mapa_regioes = {
        'RS': 'Sul', 'SC': 'Sul', 'PR': 'Sul',
        'SP': 'Sudeste', 'RJ': 'Sudeste', 'MG': 'Sudeste', 'ES': 'Sudeste',
        'MT': 'Centro-Oeste', 'MS': 'Centro-Oeste', 'GO': 'Centro-Oeste',
        'BA': 'Nordeste' # Adicione outros estados conforme sua base
    }
    df['Região'] = df[col_uf].map(mapa_regioes).fillna('Outros')

    # --- BARRA LATERAL (FILTROS E MÉTRICAS) ---
    st.sidebar.header("⚙️ Parâmetros de Análise")
    
    # Definir o que é "Vender Bem"
    media_faturamento = float(df[col_fat].mean())
    meta_sucesso = st.sidebar.slider(
        "Régua de Alta Performance", 
        min_value=float(df[col_fat].min()), 
        max_value=float(df[col_fat].max()), 
        value=media_faturamento,
        help="Lojas acima deste valor serão consideradas 'Top Performance'"
    )

    # Criar classificação de Performance
    df['Performance'] = df[col_fat].apply(lambda x: '💎 Alta' if x >= meta_sucesso else '📉 Comum')

    # Filtro de UF
    ufs_selecionadas = st.sidebar.multiselect("Filtrar por Estado (UF):", options=df[col_uf].unique(), default=df[col_uf].unique())
    df_filtrado = df[df[col_uf].isin(ufs_selecionadas)]

    # --- INDICADORES RÁPIDOS (KPIs) ---
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total de Lojas", len(df_filtrado))
    with c2:
        qtd_alta = len(df_filtrado[df_filtrado['Performance'] == '💎 Alta'])
        st.metric("Lojas Alta Performance", qtd_alta)
    with c3:
        st.metric("Faturamento Médio", f"R$ {df_filtrado[col_fat].mean():,.2f}")
    with c4:
        %_sucesso = (qtd_alta / len(df_filtrado)) * 100 if len(df_filtrado) > 0 else 0
        st.metric("% de Sucesso na Região", f"{%_sucesso:.1f}%")

    # --- ABAS DE ANÁLISE ---
    tab_geo, tab_dna, tab_listagem = st.tabs(["🌎 Onde estão?", "🧬 DNA do Sucesso", "📋 Lista de Lojas"])

    with tab_geo:
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.subheader("Lojas por Estado e Performance")
            fig_uf = px.histogram(df_filtrado, x=col_uf, color="Performance", barmode="group",
                                  color_discrete_map={'💎 Alta': '#27ae60', '📉 Comum': '#e74c3c'},
                                  text_auto=True)
            st.plotly_chart(fig_uf, use_container_width=True)

        with col_g2:
            st.subheader("Performance por Tamanho de Cidade")
            fig_porte = px.histogram(df_filtrado, x=col_porte, color="Performance", barmode="percent",
                                     title="Probabilidade de sucesso por porte de cidade",
                                     color_discrete_map={'💎 Alta': '#27ae60', '📉 Comum': '#e74c3c'})
            st.plotly_chart(fig_porte, use_container_width=True)

    with tab_dna:
        st.subheader("Cruzamento de Características")
        st.write("Selecione uma característica para ver o que as lojas que vendem bem têm em comum:")
        
        analise_alvo = st.selectbox("Analisar impacto de:", [col_posicao, col_estacionamento, "Região", col_diretor])
        
        c_dna1, c_dna2 = st.columns([2, 1])
        
        with c_dna1:
            fig_dna = px.box(df_filtrado, x=analise_alvo, y=col_fat, color="Performance",
                            title=f"Distribuição de faturamento por {analise_alvo}",
                            color_discrete_map={'💎 Alta': '#27ae60', '📉 Comum': '#e74c3c'})
            st.plotly_chart(fig_dna, use_container_width=True)
            
        with c_dna2:
            st.info("### 💡 Insight Automático")
            tops = df_filtrado[df_filtrado['Performance'] == '💎 Alta']
            if not tops.empty:
                melhor_valor = tops[analise_alvo].mode()[0]
                total_na_caract = len(tops[tops[analise_alvo] == melhor_valor])
                st.write(f"O padrão mais forte entre as lojas de maior faturamento em relação a **{analise_alvo}** é: **{melhor_valor}**.")
                st.write(f"Das lojas TOP, {total_na_caract} seguem esse padrão.")
            else:
                st.write("Ajuste a régua de performance para identificar padrões.")

    with tab_listagem:
        st.subheader("Detalhamento das Lojas")
        # Mostrar apenas colunas principais para não poluir
        colunas_ver = [col_loja, col_uf, col_fat, 'Performance', col_posicao, col_porte]
        st.dataframe(df_filtrado[colunas_ver].sort_values(by=col_fat, ascending=False), use_container_width=True)

else:
    st.info("👋 Bem-vindo! Por favor, faça o upload do arquivo 'Teste de lojas.xlsx' para iniciar a análise.")

# 5. SUGESTÕES DE MELHORIA (Aparecem no final da página)
with st.expander("🚀 Como aperfeiçoar este sistema?"):
    st.write("""
    1. **Adicionar Coluna de 'Renda':** Incluir o PIB ou Renda per Capita da cidade para ver se o faturamento acompanha o poder de compra.
    2. **Pólos Geradores:** Criar colunas para 'Distância de Supermercados' ou 'Farmácias próximas'.
    3. **Tempo de Casa:** Lojas novas performam diferente de lojas maduras. Incluir data de abertura ajuda a não penalizar lojas recentes.
    4. **Fluxo de Pedestres:** Uma nota de 1 a 5 para o movimento na porta da loja.
    """)
