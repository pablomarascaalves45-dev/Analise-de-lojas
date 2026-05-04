import pandas as pd
import plotly.express as px
import streamlit as st
from datetime import datetime

# 1. CONFIGURAÇÃO DO AMBIENTE
st.set_page_config(page_title="Dashboard de Expansão | Business Intelligence", layout="wide")

st.title("📊 Monitoramento Estratégico: Performance de Rede")
st.markdown("---")

# 2. GESTÃO DE DADOS
uploaded_file = st.file_uploader("📂 Importar Base Consolidada de Unidades (.xlsx)", type=['xlsx'])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df.columns = [str(c).strip() for c in df.columns]
    
    # --- MAPEAMENTO DINÂMICO DE ATRIBUTOS ---
    def localizar_coluna(lista_termos, nome_padrao):
        for col in df.columns:
            if any(termo.upper() in col.upper() for termo in lista_termos):
                return col
        return nome_padrao

    col_id = localizar_coluna(["ID_LOJA", "COD_LOJA", "ID"], "ID_LOJA")
    col_loja = localizar_coluna(["LOJAS", "NOME DA LOJA", "NOME_LOJA"], "LOJAS")
    col_fat = localizar_coluna(["FATURAMENTO", "MAR'25", "MÉDIA FATURAMENTO", "SOMA DAS VENDAS"], "MÉDIA FATURAMENTO")
    col_dre = localizar_coluna(["DRE_AC", "FEV/26", "DRE FEV", "DRE ACUMULADO"], "DRE_AC FEV/26")
    col_uf = localizar_coluna(["UF", "ESTADO"], "UF")
    col_porte = localizar_coluna(["TAMANHO DA CIDADE", "PORTE", "TAMANHO"], "TAMANHO DA CIDADE")
    col_posicao = localizar_coluna(["POSIÇÃO", "POSICAO"], "POSIÇÃO DA LOJA")
    col_estacionamento = localizar_coluna(["ESTACIONAMENTO"], "ESTACIONAMENTO")
    col_abertura = localizar_coluna(["DATA DE ABERTURA", "ABERTURA"], "DATA DE ABERTURA")
    col_localizacao = localizar_coluna(["BAIRRO OU CENTRO", "LOCALIZACAO", "CENTRO"], "BAIRRO OU CENTRO")
    col_demanda = localizar_coluna(["DEMANDA FSJ", "DEMANDA"], "DEMANDA FSJ RAIO DE 1 KM")
    col_populacao = localizar_coluna(["POPULAÇÃO RAIO", "POPULACAO"], "POPULAÇÃO RAIO DE 1KM")

    # --- NORMALIZAÇÃO DE VARIÁVEIS ---
    for c in [col_demanda, col_populacao]:
        if c in df.columns:
            df[c] = df[c].astype(str).str.replace(r'[R$\.\s]', '', regex=True).str.replace(',', '.')
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

    if col_localizacao in df.columns:
        df[col_localizacao] = df[col_localizacao].astype(str).str.upper().str.strip()
        df[col_localizacao] = df[col_localizacao].apply(lambda x: "CENTRO" if "CENTRO" in x else "BAIRRO")

    if col_abertura in df.columns:
        df[col_abertura] = pd.to_datetime(df[col_abertura], errors='coerce')
        hoje = datetime.now()
        df['MATURIDADE'] = df[col_abertura].apply(lambda x: hoje.year - x.year if pd.notnull(x) else 0)
        df['FAIXA_IDADE'] = df['MATURIDADE'].apply(lambda x: f"{x} anos")

    # --- PARÂMETROS DE FILTRAGEM (SIDEBAR) ---
    st.sidebar.header("⚙️ Parâmetros de Filtro")
    ufs = sorted(df[col_uf].dropna().unique().tolist())
    opcao_uf = st.sidebar.selectbox("Região (UF):", ["Todas as Regiões"] + ufs)
    df_filtrado_uf = df.copy() if opcao_uf == "Todas as Regiões" else df[df[col_uf] == opcao_uf].copy()

    df_filtrado_uf[col_fat] = pd.to_numeric(df_filtrado_uf[col_fat], errors='coerce').fillna(0)
    df_filtrado_uf[col_dre] = pd.to_numeric(df_filtrado_uf[col_dre], errors='coerce').fillna(0)
    
    fat_min, fat_max = float(df_filtrado_uf[col_fat].min()), float(df_filtrado_uf[col_fat].max())
    faixa_fat = st.sidebar.slider("Target de Faturamento:", fat_min, fat_max, (fat_min, fat_max), format="R$ {:,.0f}")
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("📌 Régua de Classificação de PDV")
    st.sidebar.markdown("""
    * **🔵 Tier 1 (Alta):** Faturamento ≥ R$ 1MM
    * **💎 Tier 2 (Eficiente):** Fat. ≥ R$ 400k e Margem (+)
    * **🟠 Tier 3 (Oportunidade):** Fat. ≥ R$ 400k e Margem (-)
    * **🟡 Tier 4 (Estável):** Fat. < R$ 400k e Margem (+)
    * **🔴 Tier 5 (Crítica):** Fat. < R$ 400k e Margem (-)
    """)

    df_view = df_filtrado_uf[
        (df_filtrado_uf[col_fat] >= faixa_fat[0]) & (df_filtrado_uf[col_fat] <= faixa_fat[1])
    ].copy()

    # --- LÓGICA DE CLASSIFICAÇÃO DE PERFORMANCE ---
    def classificar(row):
        f = row[col_fat]
        d = row[col_dre]
        if f >= 1000000: 
            return '🔵 Tier 1'
        elif f >= 400000:
            return '💎 Tier 2' if d >= 0 else '🟠 Tier 3'
        else:
            return '🟡 Tier 4' if d >= 0 else '🔴 Tier 5'

    df_view['Performance_Base'] = df_view.apply(classificar, axis=1)
    contagem_perf = df_view['Performance_Base'].value_counts()
    
    def formatar_legenda(perf_base):
        qtd = contagem_perf.get(perf_base, 0)
        return f"{perf_base} ({qtd} unid.)"

    df_view['Performance'] = df_view['Performance_Base'].apply(formatar_legenda)
    ordem_base = ['🔵 Tier 1', '💎 Tier 2', '🟠 Tier 3', '🟡 Tier 4', '🔴 Tier 5']
    ordem_legenda = [formatar_legenda(p) for p in ordem_base if p in df_view['Performance_Base'].values]

    cores_map = {
        formatar_legenda('🔵 Tier 1'): '#1f77b4', # Azul Corporativo
        formatar_legenda('💎 Tier 2'): '#2ca02c', # Verde Sucesso
        formatar_legenda('🟠 Tier 3'): '#ff7f0e', # Laranja Alerta
        formatar_legenda('🟡 Tier 4'): '#bcbd22', # Amarelo Estável
        formatar_legenda('🔴 Tier 5'): '#d62728'  # Vermelho Crítico
    }

    # --- PAINÉIS DE ANÁLISE ---
    tab_geo, tab_dna, tab_listagem, tab_analise = st.tabs([
        "🌎 Panorama Geográfico", 
        "🧬 Matriz de Atributos", 
        "📋 Relatório Detalhado", 
        "🧠 Sumário Executivo"
    ])

    with tab_geo:
        st.subheader(f"Visão Consolidada de Performance - {opcao_uf}")
        k1, k2, k3 = st.columns(3)
        k1.metric("Total de Unidades", len(df_view))
        k2.metric("Unidades Alta Tração (T1/T2)", len(df_view[df_view['Performance_Base'].isin(['🔵 Tier 1', '💎 Tier 2'])]))
        dre_medio = df_view[col_dre].mean()
        k3.metric("Margem Média (DRE)", f"{dre_medio*100:.2f}%")

        fig_scat = px.scatter(df_view, x=col_fat, y=col_dre, color="Performance", 
                             hover_name=col_loja,
                             category_orders={"Performance": ordem_legenda},
                             color_discrete_map=cores_map, height=500)
        fig_scat.add_hline(y=0, line_dash="dash", line_color="#333")
        st.plotly_chart(fig_scat, use_container_width=True)

    with tab_dna:
        st.subheader("Análise de Variáveis e Drivers de Performance")
        opcoes_dna = [c for c in [col_localizacao, 'FAIXA_IDADE', col_porte, col_posicao, col_estacionamento] if c in df_view.columns]
        analise_alvo = st.selectbox("Selecionar Driver de Performance:", opcoes_dna)
        
        if not df_view.empty and analise_alvo:
            temp_df = df_view.copy()
            stats = temp_df.groupby([analise_alvo, 'Performance']).size().reset_index(name='contagem')

            fig_dna = px.bar(stats, x=analise_alvo, y='contagem', color='Performance',
                             barmode='group', text='contagem',
                             category_orders={"Performance": ordem_legenda},
                             color_discrete_map=cores_map, height=500)
            st.plotly_chart(fig_dna, use_container_width=True)

    with tab_listagem:
        st.subheader("Listagem Analítica de Unidades")
        cols_final = [col_id, col_loja, col_uf, 'MATURIDADE', col_localizacao, col_porte, col_fat, col_dre, 'Performance_Base']
        df_tabela = df_view[[c for c in cols_final if c in df_view.columns]].copy()
        df_tabela = df_tabela.sort_values(by=col_fat, ascending=False)
        
        st.dataframe(
            df_tabela.style.format({
                col_fat: "R$ {:,.2f}",
                col_dre: "{:.2%}",
                'MATURIDADE': "{:.0f} anos"
            }), 
            use_container_width=True,
            hide_index=True
        )

    with tab_analise:
        st.subheader("Insights Operacionais: Benchmarks de Unidades Tier 1 (+R$ 1MM)")
        
        df_alta = df_view[df_view['Performance_Base'] == '🔵 Tier 1']
        
        if len(df_alta) > 0:
            c1, c2 = st.columns([1, 1])
            
            with c1:
                st.markdown("### 🎯 Atributos Dominantes")
                
                loc_pref = df_alta[col_localizacao].mode()[0] if col_localizacao in df_alta.columns else "N/A"
                st.write(f"**📍 Localização Estratégica:** As unidades de alta performance concentram-se em áreas de **{loc_pref}**.")
                
                porte_pref = df_alta[col_porte].mode()[0] if col_porte in df_alta.columns else "N/A"
                st.write(f"**🏙️ Cluster de Mercado:** O perfil de cidade predominante para este volume é **{porte_pref}**.")
                
                if col_estacionamento in df_alta.columns:
                    est_pref = df_alta[col_estacionamento].mode()[0]
                    st.write(f"**🚗 Infraestrutura:** O padrão recorrente para suporte ao fluxo é **{est_pref}**.")

                idade_media = df_alta['MATURIDADE'].mean()
                st.write(f"**⏳ Ciclo de Maturidade:** A média de operação para este patamar é de **{idade_media:.1f} anos**.")

            with c2:
                st.markdown("### 🚀 Recomendações para Expansão")
                st.info(f"""
                Com base nos indicadores das **{len(df_alta)} unidades de maior faturamento**, o modelo ideal para replicação considera:
                
                1.  **Prioridade em {loc_pref}:** Este cluster geográfico apresenta a maior conversão de vendas.
                2.  **Seleção de Praças {porte_pref}:** Municípios onde a densidade demográfica otimiza o ticket médio.
                3.  **Eficiência Operacional:** A margem média deste grupo é de **{df_alta[col_dre].mean()*100:.1f}%**, o benchmark para novos projetos.
                4.  **Curva de Maturação:** O break-even de alta performance tende a ocorrer após o **{int(idade_media)}º ano**.
                """)
                
            st.markdown("---")
            st.subheader("Comparativo de Indicadores: Tier 1 vs Mercado")
            
            comp_data = {
                'Indicador KPI': ['Margem Média (DRE)', 'Demanda Estimada (Média)', 'Densidade Populacional (1km)'],
                'Benchmark Tier 1': [
                    df_alta[col_dre].mean(), 
                    df_alta[col_demanda].mean(), 
                    df_alta[col_populacao].mean()
                ],
                'Média Demais Unidades': [
                    df_view[df_view['Performance_Base'] != '🔵 Tier 1'][col_dre].mean(),
                    df_view[df_view['Performance_Base'] != '🔵 Tier 1'][col_demanda].mean(),
                    df_view[df_view['Performance_Base'] != '🔵 Tier 1'][col_populacao].mean()
                ]
            }
            df_comp = pd.DataFrame(comp_data)
            st.table(df_comp.set_index('Indicador KPI'))
        else:
            st.warning("A seleção atual não contém unidades classificadas como Tier 1 para a geração de benchmarks.")

else:
    st.info("Aguardando importação da base de dados para iniciar o processamento analítico.")
