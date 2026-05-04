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

    # --- TRATAMENTO DE VARIÁVEIS (Garantindo que não haja erro de tipo) ---
    for c in [col_demanda, col_populacao, col_fat, col_dre]:
        if c in df.columns:
            # Remove símbolos monetários e ajusta pontuação antes de converter
            df[c] = df[c].astype(str).str.replace(r'[R$\s]', '', regex=True).str.replace('.', '', regex=False).str.replace(',', '.')
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

    if col_localizacao in df.columns:
        df[col_localizacao] = df[col_localizacao].astype(str).str.upper().str.strip()
        df[col_localizacao] = df[col_localizacao].apply(lambda x: "CENTRO" if "CENTRO" in x else "BAIRRO")

    if col_abertura in df.columns:
        df[col_abertura] = pd.to_datetime(df[col_abertura], errors='coerce')
        hoje = datetime.now()
        df['IDADE_LOJA'] = df[col_abertura].apply(lambda x: hoje.year - x.year if pd.notnull(x) else 0)
        df['FAIXA_IDADE'] = df['IDADE_LOJA'].apply(lambda x: f"{x} anos")

    # --- FILTROS (SIDEBAR) ---
    st.sidebar.header("⚙️ Filtros")
    
    # Prevenção de erro caso a coluna UF não exista
    ufs = sorted(df[col_uf].dropna().unique().tolist()) if col_uf in df.columns else []
    opcao_uf = st.sidebar.selectbox("Estado:", ["Todos os Estados"] + ufs)
    
    df_filtrado_uf = df.copy()
    if opcao_uf != "Todos os Estados":
        df_filtrado_uf = df[df[col_uf] == opcao_uf].copy()

    fat_min = float(df_filtrado_uf[col_fat].min()) if not df_filtrado_uf.empty else 0.0
    fat_max = float(df_filtrado_uf[col_fat].max()) if not df_filtrado_uf.empty else 1000000.0
    
    faixa_fat = st.sidebar.slider("Faixa de Faturamento:", fat_min, fat_max, (fat_min, fat_max), format="R$ {:,.0f}")
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("📌 Critérios de Performance")
    st.sidebar.markdown("""
    * **🔵 Alta:** Fat. ≥ R$ 1.000.000
    * **💎 Boa:** Fat. ≥ R$ 400.000 e DRE Positivo
    * **🟠 Alto Custo:** Fat. ≥ R$ 400.000 e DRE Negativo
    * **🟡 Baixa:** Fat. < R$ 400.000 e DRE Positivo
    * **🔴 Ruim:** Fat. < R$ 400.000 e DRE Negativo
    """)

    df_view = df_filtrado_uf[
        (df_filtrado_uf[col_fat] >= faixa_fat[0]) & (df_filtrado_uf[col_fat] <= faixa_fat[1])
    ].copy()

    # --- LÓGICA DE PERFORMANCE ---
    def classificar(row):
        f = row[col_fat]
        d = row[col_dre]
        if f >= 1000000: return '🔵 Alta'
        elif f >= 400000: return '💎 Boa' if d >= 0 else '🟠 Alto Custo'
        else: return '🟡 Baixa' if d >= 0 else '🔴 Ruim'

    if not df_view.empty:
        df_view['Performance_Base'] = df_view.apply(classificar, axis=1)
        contagem_perf = df_view['Performance_Base'].value_counts()
        
        def formatar_legenda(perf_base):
            qtd = contagem_perf.get(perf_base, 0)
            return f"{perf_base} = {qtd} lojas"

        df_view['Performance'] = df_view['Performance_Base'].apply(formatar_legenda)
        ordem_base = ['🔵 Alta', '💎 Boa', '🟠 Alto Custo', '🟡 Baixa', '🔴 Ruim']
        ordem_legenda = [formatar_legenda(p) for p in ordem_base if p in df_view['Performance_Base'].values]

        cores_map = {
            formatar_legenda('🔵 Alta'): '#0000FF',
            formatar_legenda('💎 Boa'): '#27ae60',
            formatar_legenda('🟠 Alto Custo'): '#e67e22',
            formatar_legenda('🟡 Baixa'): '#f1c40f',
            formatar_legenda('🔴 Ruim'): '#e74c3c'
        }

        # --- ABAS ---
        tab_geo, tab_dna, tab_listagem, tab_analise = st.tabs(["🌎 Visão Geográfica", "🧬 DNA do Sucesso", "📋 Detalhes", "🧠 Análise Estratégica"])

        with tab_geo:
            st.subheader(f"Resumo de Performance - {opcao_uf}")
            k1, k2, k3 = st.columns(3)
            k1.metric("Total Lojas", len(df_view))
            k2.metric("Lojas 'Vão Bem' (Boa/Alta)", len(df_view[df_view['Performance_Base'].isin(['🔵 Alta', '💎 Boa'])]))
            dre_medio = df_view[col_dre].mean()
            k3.metric("DRE Médio", f"{dre_medio*100:.2f}%")

            fig_scat = px.scatter(df_view, x=col_fat, y=col_dre, color="Performance",
                                 hover_name=col_loja,
                                 category_orders={"Performance": ordem_legenda},
                                 color_discrete_map=cores_map, height=500)
            fig_scat.add_hline(y=0, line_dash="dash", line_color="red")
            st.plotly_chart(fig_scat, use_container_width=True)

        with tab_dna:
            st.subheader("🧬 Análise de Variáveis de Sucesso")
            opcoes_dna = [c for c in [col_localizacao, 'FAIXA_IDADE', col_porte, col_posicao, col_estacionamento] if c in df_view.columns]
            analise_alvo = st.selectbox("Escolha a variável para análise de DNA:", opcoes_dna)
            
            if analise_alvo:
                stats = df_view.groupby([analise_alvo, 'Performance']).size().reset_index(name='contagem')
                fig_dna = px.bar(stats, x=analise_alvo, y='contagem', color='Performance',
                                 barmode='group', text='contagem',
                                 category_orders={"Performance": ordem_legenda},
                                 color_discrete_map=cores_map, height=500)
                st.plotly_chart(fig_dna, use_container_width=True)

        with tab_listagem:
            st.subheader("📋 Detalhamento das Lojas")
            cols_final = [col_id, col_loja, col_uf, 'IDADE_LOJA', col_localizacao, col_porte, col_fat, col_dre, 'Performance_Base']
            df_tabela = df_view[[c for c in cols_final if c in df_view.columns]].copy()
            st.dataframe(df_tabela.sort_values(by=col_fat, ascending=False), use_container_width=True, hide_index=True)

        with tab_analise:
            st.subheader("🧠 Relatório de Inteligência: O Perfil das Lojas +1MM")
            df_alta = df_view[df_view['Performance_Base'] == '🔵 Alta']
            
            if not df_alta.empty:
                c1, c2 = st.columns(2)
                with c1:
                    st.info(f"### 🎯 Fortalezas ({len(df_alta)} lojas)")
                    loc_pref = df_alta[col_localizacao].mode()[0] if col_localizacao in df_alta.columns else "N/A"
                    st.write(f"**📍 Localização Dominante:** {loc_pref}")
                    idade_media = df_alta['IDADE_LOJA'].mean()
                    st.write(f"**⏳ Maturação Média:** {idade_media:.1f} anos")
                
                with c2:
                    st.success("### 🚀 Benchmarks")
                    st.write(f"**Margem Média:** {df_alta[col_dre].mean()*100:.1f}%")
                    st.write(f"**Demanda Média:** {df_alta[col_demanda].mean():,.0f}")
            else:
                st.warning("⚠️ Sem dados suficientes para lojas +1MM nesta seleção.")
    else:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")
else:
    st.info("👋 Por favor, carregue o arquivo Excel para iniciar.")
