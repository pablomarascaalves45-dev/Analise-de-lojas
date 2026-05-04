import pandas as pd
import plotly.express as px
import streamlit as st
from datetime import datetime

# 1. CONFIGURAÇÃO DO AMBIENTE
st.set_page_config(page_title="Analytics Expansão - DNA de Sucesso", layout="wide")

st.title("🎯 Inteligência de Performance: DNA de Sucesso")
st.markdown("---")

# 2. UPLOAD E NORMALIZAÇÃO
uploaded_file = st.file_uploader("📂 Importar base de dados (Excel)", type=['xlsx'])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df.columns = [str(c).strip() for c in df.columns]
    
    # --- MAPEAMENTO DINÂMICO (Prevenção de erro de nome de coluna) ---
    def localizar(termos, padrao):
        for c in df.columns:
            if any(t.upper() in c.upper() for t in termos): return c
        return padrao

    col_fat = localizar(["FATURAMENTO", "MÉDIA FAT", "VENDAS"], "FATURAMENTO")
    col_dre = localizar(["DRE", "MARGEM", "LUCRO"], "DRE")
    col_uf = localizar(["UF", "ESTADO"], "UF")
    col_local = localizar(["LOCALIZACAO", "BAIRRO", "CENTRO"], "LOCALIZAÇÃO")
    col_abertura = localizar(["DATA", "ABERTURA"], "ABERTURA")
    col_porte = localizar(["PORTE", "TAMANHO"], "PORTE")

    # --- TRATAMENTO DE TIPOS (Garante que os cálculos funcionem) ---
    for c in [col_fat, col_dre]:
        if c in df.columns:
            df[c] = df[c].astype(str).str.replace(r'[R$\s]', '', regex=True).str.replace('.', '', regex=False).str.replace(',', '.')
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

    # Cálculo de Maturidade
    if col_abertura in df.columns:
        df[col_abertura] = pd.to_datetime(df[col_abertura], errors='coerce')
        df['IDADE_LOJA'] = df[col_abertura].apply(lambda x: datetime.now().year - x.year if pd.notnull(x) else 0)

    # --- SIDEBAR E FILTROS ---
    st.sidebar.header("⚙️ Parâmetros")
    ufs = sorted(df[col_uf].dropna().unique().tolist()) if col_uf in df.columns else []
    sel_uf = st.sidebar.selectbox("Filtrar Estado:", ["Todos"] + ufs)
    
    df_f = df.copy() if sel_uf == "Todos" else df[df[col_uf] == sel_uf].copy()

    # --- MÉTRICA DE CLASSIFICAÇÃO (A Fórmula do DNA) ---
    def classificar_loja(row):
        f, d = row[col_fat], row[col_dre]
        if f >= 1000000: return '🔵 Alta'
        elif f >= 400000: return '💎 Boa' if d >= 0 else '🟠 Alto Custo'
        else: return '🟡 Baixa' if d >= 0 else '🔴 Ruim'

    df_f['Performance'] = df_f.apply(classificar_loja, axis=1)

    # --- DASHBOARD VISUAL ---
    tab1, tab2, tab3 = st.tabs(["🌎 Visão Geral", "🧬 DNA de Sucesso", "📋 Listagem"])

    with tab1:
        st.subheader("Performance por Faturamento vs DRE")
        fig = px.scatter(df_f, x=col_fat, y=col_dre, color='Performance', 
                         hover_name=localizar(["NOME", "LOJA"], "LOJA"),
                         color_discrete_map={'🔵 Alta': '#0000FF', '💎 Boa': '#27ae60', 
                                            '🟠 Alto Custo': '#e67e22', '🟡 Baixa': '#f1c40f', '🔴 Ruim': '#e74c3c'})
        fig.add_hline(y=0, line_dash="dash", line_color="black")
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("Análise de Atributos Vencedores")
        col_analise = st.selectbox("Escolha o Driver:", [col_local, col_porte, 'IDADE_LOJA'])
        df_dna = df_f.groupby([col_analise, 'Performance']).size().reset_index(name='Qtd')
        st.plotly_chart(px.bar(df_dna, x=col_analise, y='Qtd', color='Performance', barmode='group'), use_container_width=True)

    with tab3:
        st.dataframe(df_f.sort_values(by=col_fat, ascending=False), use_container_width=True)

else:
    st.info("Aguardando upload do arquivo Excel para processar o DNA de Sucesso.")
