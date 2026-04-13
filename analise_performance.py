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
    
    # Limpeza profunda: remove espaços no início/fim e garante que tudo é string
    df.columns = [str(c).strip() for c in df.columns]
    
    # --- MAPEAMENTO AUTOMÁTICO PARA EVITAR KEYERROR ---
    # Tentamos encontrar as colunas por palavras-chave caso o nome exato falhe
    def encontrar_coluna(lista_keywords, default_name):
        for col in df.columns:
            if any(key.upper() in col.upper() for key in lista_keywords):
                return col
        return default_name

    col_fat = encontrar_coluna(["FATURAMENTO", "MAR'25", "FEV'26"], "MÉDIA FATURAMENTO DE MAR'25 ATÉ FEV'26")
    col_dre = encontrar_coluna(["DRE_AC", "FEV/26"], "DRE_AC FEV/26")
    col_uf = encontrar_coluna(["UF", "ESTADO"], "UF")
    col_porte = encontrar_coluna(["TAMANHO", "PORTE", "CIDADE"], "TAMANHO DA CIDADE")
    col_posicao = encontrar_coluna(["POSIÇÃO", "POSICAO"], "POSIÇÃO DA LOJA")
    col_estacionamento = encontrar_coluna(["ESTACIONAMENTO"], "ESTACIONAMENTO")
    col_loja = encontrar_coluna(["LOJAS", "NOME"], "LOJAS")

    # Verificação de segurança: Se a coluna de faturamento não existir mesmo após a busca
    if col_fat not in df.columns:
        st.error(f"❌ Não encontrei a coluna de Faturamento. Verifique se o nome no Excel é parecido com: {col_fat}")
        st.stop()

    # --- BARRA LATERAL (FILTROS) ---
    st.sidebar.header("⚙️ Filtros de Visualização")
    
    lista_ufs = sorted(df[col_uf].dropna().unique().tolist())
    opcao_uf = st.sidebar.selectbox("Selecione o Estado:", ["Todos os Estados"] + lista_ufs)
    
    df_filtrado_uf = df.copy() if opcao_uf == "Todos os Estados" else df[df[col_uf] == opcao_uf].copy()

    # Filtro de Faturamento com tratamento para valores nulos
    df_filtrado_uf[col_fat] = pd.to_numeric(df_filtrado_uf[col_fat], errors='coerce').fillna(0)
    
    fat_min_data = float(df_filtrado_uf[col_fat].min())
    fat_max_data = float(df_filtrado_uf[col_fat].max())
    
    faixa_faturamento = st.sidebar.slider(
        "Filtrar por Faixa de Faturamento:",
        min_value=fat_min_data,
        max_value=fat_max_data,
        value=(fat_min_data, fat_max_data),
        format="R$ {:,.0f}"
    )
    
    st.sidebar.info(f"📍 **Filtrado:** R$ {faixa_faturamento[0]:,.0f} a R$ {faixa_faturamento[1]:,.0f}")
    
    df_view = df_filtrado_uf[
        (df_filtrado_uf[col_fat] >= faixa_faturamento[0]) & 
        (df_filtrado_uf[col_fat] <= faixa_faturamento[1])
    ].copy()

    # --- LÓGICA DE CLASSIFICAÇÃO ---
    def classificar_performance(row):
        faturamento = row[col_fat]
        dre = row[col_dre] if col_dre in df.columns else 0
        if faturamento < 400000:
            return '🔴 Ruim' if dre < 0 else '🟡 Baixa'
        return '💎 Alta'

    df_view['Performance'] = df_view.apply(classificar_performance, axis=1)

    # --- ABAS ---
    tab_geo, tab_dna, tab_diagnostico, tab_listagem = st.tabs(["🌎 Visão Geográfica", "🧬 DNA do Sucesso", "🧠 Diagnóstico", "📋 Tabela"])

    with tab_dna:
        st.subheader("Análise Detalhada por Perfil")
        analise_alvo = st.selectbox("Escolha o critério:", [col_porte, col_posicao, col_estacionamento])
        
        # Cálculo de estatísticas para os rótulos
        stats = df_view.groupby([analise_alvo, 'Performance']).size().reset_index(name='contagem')
        totais = df_view.groupby(analise_alvo).size().reset_index(name='total_grupo')
        stats = stats.merge(totais, on=analise_alvo)
        stats['porcentagem'] = (stats['contagem'] / stats['total_grupo'] * 100).round(1)
        
        stats['texto_rotulo'] = (
            "Total: " + stats['total_grupo'].astype(str) + "<br>" +
            stats['Performance'].str.extract(r'(\w+)', expand=False) + ": " + stats['porcentagem'].astype(str) + "%"
        )

        fig_dna = px.bar(stats, x=analise_alvo, y='contagem', color='Performance',
                         barmode='group', text='texto_rotulo',
                         color_discrete_map={'💎 Alta': '#27ae60', '🟡 Baixa': '#f1c40f', '🔴 Ruim': '#e74c3c'})
        
        fig_dna.update_traces(textposition='outside')
        st.plotly_chart(fig_dna, use_container_width=True)

    # ... (Restante das abas mantendo a estrutura anterior)
    with tab_listagem:
        st.dataframe(df_view[[col_loja, col_uf, col_fat, 'Performance']].sort_values(by=col_fat, ascending=False))

else:
    st.info("👋 Por favor, carregue o arquivo Excel para começar.")
