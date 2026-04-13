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
    df = pd.read_excel(uploaded_file)
    # Limpa espaços em branco nos nomes das colunas
    df.columns = [str(c).strip() for c in df.columns]
    
    # --- MAPEAMENTO DINÂMICO DE COLUNAS ---
    def localizar_coluna(lista_termos, nome_padrao):
        for col in df.columns:
            if any(termo.upper() in col.upper() for termo in lista_termos):
                return col
        return nome_padrao

    # Mapeamento com termos de busca ampliados para evitar o KeyError
    col_fat = localizar_coluna(["FATURAMENTO", "MAR'25", "MÉDIA FATURAMENTO", "SOMA DAS VENDAS"], "MÉDIA FATURAMENTO")
    col_dre = localizar_coluna(["DRE_AC", "FEV/26", "DRE FEV"], "DRE_AC FEV/26")
    col_uf = localizar_coluna(["UF", "ESTADO"], "UF")
    col_porte = localizar_coluna(["TAMANHO DA CIDADE", "PORTE", "TAMANHO"], "TAMANHO DA CIDADE")
    col_posicao = localizar_coluna(["POSIÇÃO", "POSICAO"], "POSIÇÃO DA LOJA")
    col_estacionamento = localizar_coluna(["ESTACIONAMENTO"], "ESTACIONAMENTO")
    col_loja = localizar_coluna(["LOJAS", "NOME", "ID_LOJA"], "LOJAS")

    # --- BARRA LATERAL (FILTROS) ---
    st.sidebar.header("⚙️ Filtros")
    ufs = sorted(df[col_uf].dropna().unique().tolist())
    opcao_uf = st.sidebar.selectbox("Estado:", ["Todos os Estados"] + ufs)
    df_filtrado_uf = df.copy() if opcao_uf == "Todos os Estados" else df[df[col_uf] == opcao_uf].copy()

    # Tratamento numérico para cálculos
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
        if f >= 1000000: return '🔵 Alta'
        elif f >= 400000: return '💎 Boa'
        else: return '🔴 Ruim' if d < 0 else '🟡 Baixa'

    df_view['Performance_Base'] = df_view.apply(classificar, axis=1)

    # Legenda Dinâmica
    contagem_perf = df_view['Performance_Base'].value_counts()
    def formatar_legenda(perf_base):
        qtd = contagem_perf.get(perf_base, 0)
        return f"{perf_base} = {qtd} lojas"

    df_view['Performance'] = df_view['Performance_Base'].apply(formatar_legenda)
    categorias_ordem = ['🔵 Alta', '💎 Boa', '🟡 Baixa', '🔴 Ruim']
    ordem_legenda = [formatar_legenda(p) for p in categorias_ordem if p in df_view['Performance_Base'].values]

    cores_map = {
        formatar_legenda('🔵 Alta'): '#0000FF',
        formatar_legenda('💎 Boa'): '#27ae60',
        formatar_legenda('🟡 Baixa'): '#f1c40f',
        formatar_legenda('🔴 Ruim'): '#e74c3c'
    }

    # --- ABAS ---
    tab_geo, tab_dna, tab_listagem = st.tabs(["🌎 Visão Geográfica", "🧬 DNA do Sucesso", "📋 Detalhes"])

    with tab_geo:
        st.subheader(f"Resumo de Performance - {opcao_uf}")
        k1, k2, k3 = st.columns(3)
        k1.metric("Total Lojas", len(df_view))
        k2.metric("Faturamento > 400k", len(df_view[df_view[col_fat] >= 400000]))
        k3.metric("DRE Negativo", len(df_view[df_view[col_dre] < 0]) if col_dre in df.columns else "N/A")

        fig_scat = px.scatter(df_view, x=col_fat, y=col_dre, color="Performance", 
                             hover_name=col_loja, category_orders={"Performance": ordem_legenda},
                             color_discrete_map=cores_map, height=500)
        st.plotly_chart(fig_scat, use_container_width=True)

    with tab_dna:
        st.subheader("🧬 Análise de Variáveis")
        
        # SELETOR DE VARIÁVEL (Tamanho, Posição ou Estacionamento)
        opcoes_dna = []
        for c in [col_porte, col_posicao, col_estacionamento]:
            if c in df.columns: opcoes_dna.append(c)
        
        analise_alvo = st.selectbox("Escolha o que analisar:", opcoes_dna)
        
        if not df_view.empty and analise_alvo:
            stats = df_view.groupby([analise_alvo, 'Performance', 'Performance_Base']).size().reset_index(name='contagem')
            totais = df_view.groupby(analise_alvo).size().reset_index(name='total_grupo')
            stats = stats.merge(totais, on=analise_alvo)
            stats['porcentagem'] = (stats['contagem'] / stats['total_grupo'] * 100).round(1)
            
            stats['texto'] = "<b>Total: " + stats['total_grupo'].astype(str) + "</b><br>" + \
                             stats['Performance_Base'].str.split(" ").str[1] + ": " + stats['porcentagem'].astype(str) + "%"

            fig_dna = px.bar(stats, x=analise_alvo, y='contagem', color='Performance',
                             barmode='group', text='texto',
                             category_orders={"Performance": ordem_legenda},
                             color_discrete_map=cores_map, height=600)
            
            fig_dna.update_traces(textposition='outside', textfont=dict(size=12, color="black"))
            st.plotly_chart(fig_dna, use_container_width=True)

            # Insight automático
            sucesso = stats[stats['Performance_Base'].isin(['🔵 Alta', '💎 Boa'])]
            if not sucesso.empty:
                melhor = sucesso.groupby(analise_alvo)['contagem'].sum().idxmax()
                st.info(f"💡 Em **{opcao_uf}**, o melhor DNA para **{analise_alvo}** é: **{melhor}**")

    with tab_listagem:
        # Mostra as colunas que você quer analisar na tabela final
        cols_mostrar = [col_loja, col_uf, col_porte, col_posicao, col_estacionamento, col_fat, 'Performance_Base']
        st.dataframe(df_view[[c for c in cols_mostrar if c in df_view.columns]], use_container_width=True)

else:
    st.info("Aguardando upload do arquivo Excel...")
