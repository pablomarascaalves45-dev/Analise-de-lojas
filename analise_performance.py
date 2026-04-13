import pandas as pd
import plotly.express as px
import streamlit as st

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Analytics Expansão - DNA de Sucesso", layout="wide")

st.title("🎯 Inteligência de Performance: DNA de Sucesso")
st.markdown("---")

# 2. UPLOAD E TRATAMENTO DE DADOS
uploaded_file = st.file_uploader("📂 Suba a base de dados das lojas (Excel)", type=['xlsx'])

if uploaded_file:
    # Lendo o arquivo (suporta o formato enviado)
    df = pd.read_excel(uploaded_file)
    
    # Limpeza de nomes de colunas para evitar erros de espaços
    df.columns = [str(c).strip() for c in df.columns]
    
    # --- MAPEAMENTO DINÂMICO DE COLUNAS ---
    def localizar_coluna(lista_termos, nome_padrao):
        for col in df.columns:
            if any(termo.upper() in col.upper() for termo in lista_termos):
                return col
        return nome_padrao

    col_fat = localizar_coluna(["FATURAMENTO", "MAR'25"], "MÉDIA FATURAMENTO DE MAR'25 ATÉ FEV'26")
    col_dre = localizar_coluna(["DRE_AC", "FEV/26"], "DRE_AC FEV/26")
    col_uf = localizar_coluna(["UF"], "UF")
    col_porte = localizar_coluna(["TAMANHO", "CIDADE"], "TAMANHO DA CIDADE")
    col_posicao = localizar_coluna(["POSIÇÃO", "POSICAO"], "POSIÇÃO DA LOJA")
    col_estacionamento = localizar_coluna(["ESTACIONAMENTO"], "ESTACIONAMENTO")
    col_loja = localizar_coluna(["LOJAS", "NOME"], "LOJAS")

    # --- BARRA LATERAL (FILTROS) ---
    st.sidebar.header("⚙️ Filtros")
    
    # Filtro de Estado
    ufs = sorted(df[col_uf].dropna().unique().tolist())
    opcao_uf = st.sidebar.selectbox("Estado:", ["Todos os Estados"] + ufs)
    df_filtrado_uf = df.copy() if opcao_uf == "Todos os Estados" else df[df[col_uf] == opcao_uf].copy()

    # Filtro de Faturamento
    df_filtrado_uf[col_fat] = pd.to_numeric(df_filtrado_uf[col_fat], errors='coerce').fillna(0)
    fat_min, fat_max = float(df_filtrado_uf[col_fat].min()), float(df_filtrado_uf[col_fat].max())
    
    faixa_fat = st.sidebar.slider("Faixa de Faturamento:", fat_min, fat_max, (fat_min, fat_max), format="R$ {:,.0f}")
    
    df_view = df_filtrado_uf[
        (df_filtrado_uf[col_fat] >= faixa_fat[0]) & (df_filtrado_uf[col_fat] <= faixa_fat[1])
    ].copy()

    # --- LÓGICA DE PERFORMANCE ---
    def classificar(row):
        f = row[col_fat]
        d = row[col_dre] if col_dre in df.columns else 0
        if f < 400000:
            return '🔴 Ruim' if d < 0 else '🟡 Baixa'
        return '💎 Alta'

    df_view['Performance'] = df_view.apply(classificar, axis=1)

    # --- ABAS ---
    tab_geo, tab_dna, tab_listagem = st.tabs(["🌎 Visão Geográfica", "🧬 DNA do Sucesso", "📋 Detalhes"])

    with tab_geo:
        st.subheader("Dispersão: Faturamento vs DRE")
        fig_scat = px.scatter(df_view, x=col_fat, y=col_dre, color="Performance", 
                             hover_name=col_loja,
                             color_discrete_map={'💎 Alta': '#27ae60', '🟡 Baixa': '#f1c40f', '🔴 Ruim': '#e74c3c'})
        fig_scat.add_hline(y=0, line_dash="dash", line_color="red")
        st.plotly_chart(fig_scat, use_container_width=True)

    with tab_dna:
        st.subheader("Análise Detalhada por Perfil")
        analise_alvo = st.selectbox("Analisar por:", [col_porte, col_posicao, col_estacionamento])
        
        # --- CÁLCULO DOS RÓTULOS (TOTAL + PERCENTUAL) ---
        stats = df_view.groupby([analise_alvo, 'Performance']).size().reset_index(name='contagem')
        totais = df_view.groupby(analise_alvo).size().reset_index(name='total_grupo')
        stats = stats.merge(totais, on=analise_alvo)
        stats['porcentagem'] = (stats['contagem'] / stats['total_grupo'] * 100).round(1)
        
        # Formatação do texto conforme solicitado
        stats['texto_barra'] = (
            "Total: " + stats['total_grupo'].astype(str) + "<br>" +
            stats['Performance'].str.replace("💎 ", "").str.replace("🔴 ", "").str.replace("🟡 ", "") + 
            ": " + stats['porcentagem'].astype(str) + "%"
        )

        fig_dna = px.bar(stats, x=analise_alvo, y='contagem', color='Performance',
                         barmode='group', text='texto_barra',
                         color_discrete_map={'💎 Alta': '#27ae60', '🟡 Baixa': '#f1c40f', '🔴 Ruim': '#e74c3c'})
        
        fig_dna.update_traces(textposition='outside', textfont_size=10)
        fig_dna.update_layout(yaxis_title="Qtd de Lojas", xaxis_title=analise_alvo)
        st.plotly_chart(fig_dna, use_container_width=True)

    with tab_listagem:
        st.dataframe(df_view[[col_loja, col_uf, col_fat, col_dre, 'Performance']].sort_values(by=col_fat, ascending=False))

else:
    st.info("👋 Por favor, carregue o arquivo 'Teste de lojas.xlsx'.")
