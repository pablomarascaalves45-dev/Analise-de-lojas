import pandas as pd
import plotly.express as px
import streamlit as st
from datetime import datetime

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

    col_fat = localizar_coluna(["FATURAMENTO", "MAR'25", "MÉDIA FATURAMENTO", "SOMA DAS VENDAS"], "MÉDIA FATURAMENTO")
    col_dre = localizar_coluna(["DRE_AC", "FEV/26", "DRE FEV", "DRE ACUMULADO"], "DRE_AC FEV/26")
    col_uf = localizar_coluna(["UF", "ESTADO"], "UF")
    col_porte = localizar_coluna(["TAMANHO DA CIDADE", "PORTE", "TAMANHO"], "TAMANHO DA CIDADE")
    col_posicao = localizar_coluna(["POSIÇÃO", "POSICAO"], "POSIÇÃO DA LOJA")
    col_estacionamento = localizar_coluna(["ESTACIONAMENTO"], "ESTACIONAMENTO")
    col_loja = localizar_coluna(["LOJAS", "NOME", "ID_LOJA"], "LOJAS")
    col_abertura = localizar_coluna(["DATA DE ABERTURA", "ABERTURA"], "DATA DE ABERTURA")
    col_localizacao = localizar_coluna(["BAIRRO OU CENTRO", "LOCALIZACAO", "CENTRO"], "BAIRRO OU CENTRO")

    # --- TRATAMENTO DE VARIÁVEIS ESPECÍFICAS ---
    
    # 1. Ajuste Bairro vs Centro: Tudo que não for CENTRO vira BAIRRO
    if col_localizacao in df.columns:
        df[col_localizacao] = df[col_localizacao].astype(str).str.upper().str.strip()
        df[col_localizacao] = df[col_localizacao].apply(lambda x: "CENTRO" if "CENTRO" in x else "BAIRRO")

    # 2. Cálculo da Idade em Anos
    if col_abertura in df.columns:
        df[col_abertura] = pd.to_datetime(df[col_abertura], errors='coerce')
        hoje = datetime.now()
        df['IDADE_LOJA'] = df[col_abertura].apply(lambda x: hoje.year - x.year if pd.notnull(x) else 0)
        # Criar faixas de idade para o gráfico de DNA
        df['FAIXA_IDADE'] = df['IDADE_LOJA'].apply(lambda x: f"{x} anos")

    # --- BARRA LATERAL (FILTROS) ---
    st.sidebar.header("⚙️ Filtros")
    ufs = sorted(df[col_uf].dropna().unique().tolist())
    opcao_uf = st.sidebar.selectbox("Estado:", ["Todos os Estados"] + ufs)
    df_filtrado_uf = df.copy() if opcao_uf == "Todos os Estados" else df[df[col_uf] == opcao_uf].copy()

    # Tratamento numérico
    df_filtrado_uf[col_fat] = pd.to_numeric(df_filtrado_uf[col_fat], errors='coerce').fillna(0)
    df_filtrado_uf[col_dre] = pd.to_numeric(df_filtrado_uf[col_dre], errors='coerce').fillna(0)
    
    fat_min, fat_max = float(df_filtrado_uf[col_fat].min()), float(df_filtrado_uf[col_fat].max())
    faixa_fat = st.sidebar.slider("Faixa de Faturamento:", fat_min, fat_max, (fat_min, fat_max), format="R$ {:,.0f}")
    
    df_view = df_filtrado_uf[
        (df_filtrado_uf[col_fat] >= faixa_fat[0]) & (df_filtrado_uf[col_fat] <= faixa_fat[1])
    ].copy()

    # --- LÓGICA DE PERFORMANCE ---
    def classificar(row):
        f = row[col_fat]
        d = row[col_dre]
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
    ordem_legenda = [formatar_legenda(p) for p in ['🔵 Alta', '💎 Boa', '🟡 Baixa', '🔴 Ruim'] if p in df_view['Performance_Base'].values]

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
        dre_medio = df_view[col_dre].mean()
        k3.metric("DRE Médio", f"{dre_medio*100:.2f}%")

        fig_scat = px.scatter(df_view, x=col_fat, y=col_dre, color="Performance", 
                             hover_name=col_loja, category_orders={"Performance": ordem_legenda},
                             color_discrete_map=cores_map, height=500,
                             labels={col_fat: "Faturamento Médio", col_dre: "DRE Acumulado %"})
        fig_scat.add_hline(y=0, line_dash="dash", line_color="red")
        st.plotly_chart(fig_scat, use_container_width=True)

    with tab_dna:
        st.subheader("🧬 Análise de Variáveis de Sucesso")
        
        # Opções de análise incluindo Localização e Faixa de Idade
        opcoes_dna = [c for c in [col_localizacao, 'FAIXA_IDADE', col_porte, col_posicao, col_estacionamento] if c in df_view.columns]
        analise_alvo = st.selectbox("Escolha a variável para análise de DNA:", opcoes_dna)
        
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

            sucesso = stats[stats['Performance_Base'].isin(['🔵 Alta', '💎 Boa'])]
            if not sucesso.empty:
                melhor = sucesso.groupby(analise_alvo)['contagem'].sum().idxmax()
                st.info(f"💡 Em **{opcao_uf}**, o melhor DNA para **{analise_alvo}** é: **{melhor}**")

    with tab_listagem:
        st.subheader("📋 Detalhamento das Lojas")
        cols_final = [col_loja, col_uf, 'IDADE_LOJA', col_localizacao, col_porte, col_posicao, col_fat, col_dre, 'Performance_Base']
        df_tabela = df_view[[c for c in cols_final if c in df_view.columns]].copy()
        df_tabela = df_tabela.sort_values(by=col_fat, ascending=False)
        
        st.dataframe(
            df_tabela.style.format({
                col_fat: "R$ {:,.2f}",
                col_dre: "{:.2%}",
                'IDADE_LOJA': "{:.0f} anos"
            }), 
            use_container_width=True
        )

else:
    st.info("👋 Por favor, carregue o arquivo Excel para iniciar a análise.")
