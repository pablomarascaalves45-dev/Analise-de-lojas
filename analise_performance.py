import pandas as pd
import plotly.express as px
import streamlit as st

# CONFIG
st.set_page_config(page_title="Analytics Expansão - DNA de Sucesso", layout="wide")

st.title("🎯 Inteligência de Performance: DNA de Sucesso")
st.markdown("---")

uploaded_file = st.file_uploader("📂 Suba a base de dados das lojas (Excel)", type=['xlsx'])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df.columns = [str(c).strip() for c in df.columns]

    # MAPEAR COLUNAS
    def localizar_coluna(lista_termos, nome_padrao):
        for col in df.columns:
            if any(termo.upper() in col.upper() for termo in lista_termos):
                return col
        return nome_padrao

    col_fat = localizar_coluna(["FATURAMENTO", "MAR'25"], "FATURAMENTO")
    col_dre = localizar_coluna(["DRE"], "DRE")
    col_uf = localizar_coluna(["UF"], "UF")
    col_porte = localizar_coluna(["TAMANHO"], "TAMANHO DA CIDADE")
    col_loja = localizar_coluna(["LOJA", "NOME"], "LOJA")
    col_cidade = localizar_coluna(["CIDADE"], "CIDADE")

    # FILTROS
    st.sidebar.header("⚙️ Filtros")
    ufs = sorted(df[col_uf].dropna().unique().tolist())
    opcao_uf = st.sidebar.selectbox("Estado:", ["Todos"] + ufs)

    df_filtrado = df if opcao_uf == "Todos" else df[df[col_uf] == opcao_uf]

    df_filtrado[col_fat] = pd.to_numeric(df_filtrado[col_fat], errors='coerce').fillna(0)

    df_view = df_filtrado.copy()

    # CLASSIFICAÇÃO
    def classificar(row):
        f = row[col_fat]
        d = row[col_dre] if col_dre in df.columns else 0
        if f >= 1000000:
            return 'Alta'
        elif f >= 400000:
            return 'Boa'
        else:
            return 'Ruim' if d < 0 else 'Baixa'

    df_view['Performance'] = df_view.apply(classificar, axis=1)

    cores = {
        'Alta': '#0000FF',
        'Boa': '#27ae60',
        'Baixa': '#f1c40f',
        'Ruim': '#e74c3c'
    }

    tab1, tab2 = st.tabs(["📊 Análise por Porte", "🧠 Melhor porte de cidades"])

    # =========================
    # 📊 GRÁFICO POR PORTE
    # =========================
    with tab1:
        st.subheader("Distribuição de Performance por Porte de Cidade")

        stats = df_view.groupby([col_porte, 'Performance']).size().reset_index(name='contagem')

        fig = px.bar(
            stats,
            x=col_porte,
            y='contagem',
            color='Performance',
            barmode='group',
            color_discrete_map=cores,
            height=600
        )

        fig.update_layout(
            xaxis_title="Porte da Cidade",
            yaxis_title="Quantidade de Lojas",
            legend_title="Performance",
            xaxis=dict(tickfont=dict(size=14)),
            yaxis=dict(tickfont=dict(size=14))
        )

        st.plotly_chart(fig, use_container_width=True)

        st.markdown("### 📌 Insight esperado:")
        st.write("""
        - Identificar qual porte tem mais lojas **Alta e Boa**
        - Evitar portes com concentração de **Ruim**
        """)

    # =========================
    # 🧠 RANKING
    # =========================
    with tab2:
        st.subheader("🧠 Melhor porte de cidades")

        # AGRUPAMENTO
        ranking = df_view.groupby([col_cidade, col_porte]).agg(
            total_lojas=(col_loja, 'count'),
            lojas_boas=('Performance', lambda x: (x.isin(['Alta', 'Boa'])).sum()),
            lojas_ruins=('Performance', lambda x: (x == 'Ruim').sum())
        ).reset_index()

        # SCORE
        ranking['score_expansao'] = ranking['lojas_boas'] - ranking['lojas_ruins']

        # EXPANSÃO
        st.markdown("### 🚀 Expandir")
        st.dataframe(
            ranking.sort_values(by='score_expansao', ascending=False).head(10),
            use_container_width=True
        )

        # RISCO
        st.markdown("### ⚠️ Risco")
        st.dataframe(
            ranking.sort_values(by='score_expansao').head(10),
            use_container_width=True
        )

else:
    st.info("👋 Suba um arquivo para análise.")
