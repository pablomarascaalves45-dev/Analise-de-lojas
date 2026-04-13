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
    col_id_cidade = localizar_coluna(["ID_CIDADE", "CIDADE_ID"], "ID_CIDADE")

    # --- FILTROS ---
    st.sidebar.header("⚙️ Filtros")
    ufs = sorted(df[col_uf].dropna().unique().tolist())
    opcao_uf = st.sidebar.selectbox("Estado:", ["Todos os Estados"] + ufs)
    df_filtrado_uf = df.copy() if opcao_uf == "Todos os Estados" else df[df[col_uf] == opcao_uf].copy()

    df_filtrado_uf[col_fat] = pd.to_numeric(df_filtrado_uf[col_fat], errors='coerce').fillna(0)
    fat_min, fat_max = float(df_filtrado_uf[col_fat].min()), float(df_filtrado_uf[col_fat].max())

    faixa_fat = st.sidebar.slider(
        "Faixa de Faturamento:",
        fat_min, fat_max, (fat_min, fat_max),
        format="R$ {:,.0f}"
    )

    df_view = df_filtrado_uf[
        (df_filtrado_uf[col_fat] >= faixa_fat[0]) &
        (df_filtrado_uf[col_fat] <= faixa_fat[1])
    ].copy()

    # --- CLASSIFICAÇÃO ---
    def classificar(row):
        f = row[col_fat]
        d = row[col_dre] if col_dre in df.columns else 0
        if f >= 1000000:
            return '🔵 Alta'
        elif f >= 400000:
            return '💎 Boa'
        else:
            return '🔴 Ruim' if d < 0 else '🟡 Baixa'

    df_view['Performance_Base'] = df_view.apply(classificar, axis=1)

    contagem_perf = df_view['Performance_Base'].value_counts()

    def formatar_legenda(perf_base):
        qtd = contagem_perf.get(perf_base, 0)
        return f"{perf_base} = {qtd} lojas"

    df_view['Performance'] = df_view['Performance_Base'].apply(formatar_legenda)

    cores_map = {
        formatar_legenda('🔵 Alta'): '#0000FF',
        formatar_legenda('💎 Boa'): '#27ae60',
        formatar_legenda('🟡 Baixa'): '#f1c40f',
        formatar_legenda('🔴 Ruim'): '#e74c3c'
    }

    ordem_legenda = [formatar_legenda(p) for p in ['🔵 Alta', '💎 Boa', '🟡 Baixa', '🔴 Ruim'] if p in df_view['Performance_Base'].values]

    tab_geo, tab_dna, tab_listagem = st.tabs(["🌎 Visão Geográfica", "🧬 DNA do Sucesso", "📋 Detalhes"])

    # ---------------- GEO ----------------
    with tab_geo:
        st.subheader("Indicadores de Resumo")
        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric("Qtd. Total de Lojas", len(df_view))
        kpi2.metric("Vendas > R$ 400k", len(df_view[df_view[col_fat] >= 400000]))
        kpi3.metric("Lojas com DRE Negativo", len(df_view[df_view[col_dre] < 0]))

        st.markdown("---")
        st.subheader("Dispersão: Faturamento vs DRE")

        fig_scat = px.scatter(
            df_view,
            x=col_fat,
            y=col_dre,
            color="Performance",
            hover_name=col_loja,
            category_orders={"Performance": ordem_legenda},
            color_discrete_map=cores_map,
            height=600
        )

        fig_scat.add_hline(y=0, line_dash="dash", line_color="red")

        fig_scat.update_layout(
            legend=dict(font=dict(size=16), title=dict(font=dict(size=18))),
            xaxis=dict(title=dict(font=dict(size=16)), tickfont=dict(size=14)),
            yaxis=dict(title=dict(font=dict(size=16)), tickfont=dict(size=14))
        )

        st.plotly_chart(fig_scat, use_container_width=True)

    # ---------------- DNA ----------------
    with tab_dna:
        st.subheader("Análise Detalhada por Perfil")

        analise_alvo = st.selectbox(
            "Analisar por:",
            [col_porte, col_posicao, col_estacionamento, col_id_cidade]
        )

        stats = df_view.groupby([analise_alvo, 'Performance', 'Performance_Base']).size().reset_index(name='contagem')
        totais = df_view.groupby(analise_alvo).size().reset_index(name='total_grupo')
        stats = stats.merge(totais, on=analise_alvo)

        stats['porcentagem'] = (stats['contagem'] / stats['total_grupo'] * 100).round(1)

        stats['texto_barra'] = (
            "<b>Total: " + stats['total_grupo'].astype(str) + "</b><br>" +
            stats['Performance_Base'].str.split(" ").str[1] +
            ": " + stats['porcentagem'].astype(str) + "%"
        )

        fig_dna = px.bar(
            stats,
            x=analise_alvo,
            y='contagem',
            color='Performance',
            barmode='group',
            text='texto_barra',
            category_orders={"Performance": ordem_legenda},
            color_discrete_map=cores_map,
            height=650
        )

        fig_dna.update_traces(
            textposition='outside',
            textfont=dict(size=14),
            cliponaxis=False
        )

        fig_dna.update_layout(
            legend=dict(font=dict(size=16), title=dict(font=dict(size=18))),
            xaxis=dict(title=dict(font=dict(size=16)), tickfont=dict(size=14)),
            yaxis=dict(title=dict(font=dict(size=16)), tickfont=dict(size=14)),
            margin=dict(t=50)
        )

        st.plotly_chart(fig_dna, use_container_width=True)

        # 🚀 NOVO INSIGHT (PORTE DE CIDADE)
        resumo = df_view.groupby(col_porte).agg(
            total_lojas=(col_loja, "count"),
            lojas_boas=('Performance_Base', lambda x: (x.isin(['💎 Boa', '🔵 Alta'])).sum()),
            lojas_ruins=('Performance_Base', lambda x: (x == '🔴 Ruim').sum())
        ).reset_index()

        resumo['score_expansao'] = (resumo['lojas_boas'] - resumo['lojas_ruins'])
        resumo = resumo.sort_values(by="score_expansao", ascending=False)

        st.markdown("### 🧠 Melhor porte de cidades")

        col1, col2 = st.columns(2)

        with col1:
            st.success("🚀 Melhor perfil para expandir")
            st.dataframe(resumo.head(5))

        with col2:
            st.error("⚠️ Piores perfis")
            st.dataframe(resumo.tail(5))

    # ---------------- LISTAGEM ----------------
    with tab_listagem:
        st.dataframe(
            df_view[[col_loja, col_uf, col_fat, col_dre, 'Performance']]
            .sort_values(by=col_fat, ascending=False),
            use_container_width=True
        )

else:
    st.info("👋 Por favor, carregue o arquivo.")
