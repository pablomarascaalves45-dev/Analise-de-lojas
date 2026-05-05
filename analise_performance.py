import pandas as pd
import plotly.express as px
import streamlit as st
from datetime import datetime

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Analytics Expansão - DNA de Sucesso", layout="wide")

st.title("🎯 Inteligência de Performance: DNA de Sucesso")
st.markdown("---")

# 2. UPLOAD E TRATAMENTO DE DADOS
# Nota: Você pode subir o arquivo "Teste de lojas.xlsx" aqui.
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

    # --- TRATAMENTO DE VARIÁVEIS NUMÉRICAS ---
    # Função para limpar strings monetárias e converter para float
    def limpar_numero(serie):
        return pd.to_numeric(
            serie.astype(str)
            .str.replace(r'[R$\s\.]', '', regex=True)
            .str.replace(',', '.'),
            errors='coerce'
        ).fillna(0)

    for c in [col_fat, col_dre, col_demanda, col_populacao]:
        if c in df.columns:
            df[c] = limpar_numero(df[c])

    if col_localizacao in df.columns:
        df[col_localizacao] = df[col_localizacao].astype(str).str.upper().str.strip()
        df[col_localizacao] = df[col_localizacao].apply(lambda x: "CENTRO" if "CENTRO" in x else "BAIRRO")

    if col_abertura in df.columns:
        df[col_abertura] = pd.to_datetime(df[col_abertura], errors='coerce')
        hoje = datetime.now()
        df['IDADE_LOJA'] = df[col_abertura].apply(lambda x: hoje.year - x.year if pd.notnull(x) else 0)
        df['FAIXA_IDADE'] = df['IDADE_LOJA'].apply(lambda x: f"{int(x)} anos")

    # --- FILTROS (SIDEBAR) ---
    st.sidebar.header("⚙️ Filtros")
    ufs = sorted(df[col_uf].dropna().unique().tolist()) if col_uf in df.columns else []
    opcao_uf = st.sidebar.selectbox("Estado:", ["Todos os Estados"] + ufs)
    
    df_filtrado = df.copy() if opcao_uf == "Todos os Estados" else df[df[col_uf] == opcao_uf].copy()
    
    fat_min = float(df_filtrado[col_fat].min())
    fat_max = float(df_filtrado[col_fat].max())
    faixa_fat = st.sidebar.slider("Faixa de Faturamento:", fat_min, fat_max, (fat_min, fat_max), format="R$ {:,.0f}")

    # --- CLASSIFICAÇÃO DE PERFORMANCE ---
    def classificar(row):
        f, d = row[col_fat], row[col_dre]
        if f >= 1000000: return '🔵 Alta'
        elif f >= 400000: return '💎 Boa' if d >= 0 else '🟠 Alto Custo'
        else: return '🟡 Baixa' if d >= 0 else '🔴 Ruim'

    df_view = df_filtrado[
        (df_filtrado[col_fat] >= faixa_fat[0]) & (df_filtrado[col_fat] <= faixa_fat[1])
    ].copy()

    df_view['Performance_Base'] = df_view.apply(classificar, axis=1)
    
    # Ajuste de Legendas com contagem
    contagem = df_view['Performance_Base'].value_counts()
    def fmt_legenda(p): return f"{p} = {contagem.get(p, 0)} lojas"
    
    df_view['Performance'] = df_view['Performance_Base'].apply(fmt_legenda)
    ordem_legenda = [fmt_legenda(p) for p in ['🔵 Alta', '💎 Boa', '🟠 Alto Custo', '🟡 Baixa', '🔴 Ruim']]
    
    cores_map = {
        fmt_legenda('🔵 Alta'): '#0000FF', fmt_legenda('💎 Boa'): '#27ae60',
        fmt_legenda('🟠 Alto Custo'): '#e67e22', fmt_legenda('🟡 Baixa'): '#f1c40f',
        fmt_legenda('🔴 Ruim'): '#e74c3c'
    }

    # --- INTERFACE ---
    tab_geo, tab_dna, tab_listagem, tab_analise = st.tabs(["🌎 Visão Geográfica", "🧬 DNA do Sucesso", "📋 Detalhes", "🧠 Análise Estratégica"])

    with tab_geo:
        k1, k2, k3 = st.columns(3)
        k1.metric("Total Lojas", len(df_view))
        k2.metric("Alta Performance", len(df_view[df_view['Performance_Base'].isin(['🔵 Alta', '💎 Boa'])]))
        k3.metric("Margem Média", f"{df_view[col_dre].mean():.1f}%")

        fig = px.scatter(df_view, x=col_fat, y=col_dre, color="Performance", 
                         hover_name=col_loja, category_orders={"Performance": ordem_legenda},
                         color_discrete_map=cores_map, height=500)
        fig.add_hline(y=0, line_dash="dash", line_color="red")
        st.plotly_chart(fig, use_container_width=True)

    with tab_dna:
        opcoes = [c for c in [col_localizacao, 'FAIXA_IDADE', col_porte] if c in df_view.columns]
        analise_alvo = st.selectbox("Escolha o Driver de DNA:", opcoes)
        stats = df_view.groupby([analise_alvo, 'Performance']).size().reset_index(name='contagem')
        st.plotly_chart(px.bar(stats, x=analise_alvo, y='contagem', color='Performance', 
                               color_discrete_map=cores_map, barmode='group'), use_container_width=True)

    with tab_listagem:
        st.dataframe(df_view.sort_values(by=col_fat, ascending=False), use_container_width=True)

    with tab_analise:
        df_alta = df_view[df_view['Performance_Base'] == '🔵 Alta']
        if not df_alta.empty:
            c1, c2 = st.columns(2)
            loc_pref = df_alta[col_localizacao].mode()[0]
            porte_pref = df_alta[col_porte].mode()[0]
            
            with c1:
                st.info(f"### 🎯 DNA Identificado ({len(df_alta)} lojas)")
                st.write(f"**Localização Dominante:** {loc_pref}")
                st.write(f"**Ambiente Ideal:** Cidades {porte_pref}")
            
            with c2:
                st.success("### 🚀 Benchmarks")
                st.write(f"**DRE Médio:** {df_alta[col_dre].mean():.1f}%")
                st.write(f"**População Média (1km):** {df_alta[col_populacao].mean():,.0f}")
        else:
            st.warning("⚠️ Nenhuma loja de Alta Performance (>= R$ 1MM) encontrada para gerar o relatório.")

else:
    st.info("👋 Por favor, carregue o arquivo Excel (ex: Teste de lojas.xlsx) para iniciar.")
