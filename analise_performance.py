import streamlit as st
import pandas as pd
import plotly.express as px
import re

# Configuração da página
st.set_page_config(page_title="Dashboard de Performance", layout="wide")

st.title("Laboratório de Performance de Lojas")

# --- COMPONENTE DE UPLOAD ---
st.sidebar.header("Upload de Arquivos")
uploaded_file = st.sidebar.file_uploader("Upload do arquivo 'Teste de lojas.xlsx'", type=["xlsx"])

# Novo input para receber os arquivos de safras / inaugurações passadas
uploaded_inauguracoes = st.sidebar.file_uploader(
    "Upload dos arquivos de Safras/Inaugurações (2021 a 2025)", 
    type=["xlsx", "csv"], 
    accept_multiple_files=True
)

def load_data(file):
    df = pd.read_excel(file)
    # Limpa espaços em branco nos nomes das colunas
    df.columns = [c.strip() for c in df.columns]
    
    # --- CORREÇÃO DO ERRO DE SOMA ---
    # Converte colunas financeiras para numérico, transformando erros (como "-") em 0
    colunas_financeiras = ["VENDA MAR'26", "DRE FEV'26", "DRE_AC FEV'26", "MÉDIA FATURAMENTO DE ABR'25 ATÉ MAR'26"]
    for col in colunas_financeiras:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Tratamento específico para o Ticket Médio (que vem com R$ e formatação brasileira)
    if "TICKET FSJ MAR'26" in df.columns:
        df["TICKET FSJ MAR'26"] = (
            df["TICKET FSJ MAR'26"]
            .astype(str)
            .str.replace('R\$ ', '', regex=True)
            .str.replace('.', '', regex=False)
            .str.replace(',', '.', regex=False)
            .str.strip()
        )
        df["TICKET FSJ MAR'26"] = pd.to_numeric(df["TICKET FSJ MAR'26"], errors='coerce').fillna(0)
    
    # Preenchimento de nulos em colunas categóricas
    colunas_texto = ["UF", "CIDADE", "MESORREGIÃO", "LOJAS", "TAMANHO DA CIDADE"]
    for col in colunas_texto:
        if col in df.columns:
            df[col] = df[col].astype(str).replace('nan', 'Não Informado')
            
    return df

# Função auxiliar para ler e processar os arquivos de Inaugurações consolidados
def processar_inauguracoes(arquivos):
    dfs_lista = []
    for f in arquivos:
        if f.name.endswith('.csv'):
            temp_df = pd.read_csv(f)
        else:
            temp_df = pd.read_excel(f)
            
        temp_df.columns = [c.strip() for c in temp_df.columns]
        
        # Filtra linhas de 'Total' caso existam
        if 'Desc. Loja' in temp_df.columns:
            temp_df = temp_df[~temp_df['Desc. Loja'].astype(str).str.contains('Total|TOTAL', na=False)]
            temp_df = temp_df.dropna(subset=['Desc. Loja'])
            dfs_lista.append(temp_df)
            
    if not dfs_lista:
        return pd.DataFrame()
        
    # Junta todas as safras em um dataframe mestre de histórico
    df_historico = pd.concat(dfs_lista, ignore_index=True)
    return df_historico


if uploaded_file is not None:
    df = load_data(uploaded_file)

    # Criação das Abas originais e uma nova aba para a Curva Histórica
    tab_dashboard, tab_expansao, tab_curva_faturamento = st.tabs([
        "Dashboard de Performance", 
        "Relatório de Expansão", 
        "Curva de Faturamento Histórica"
    ])

    with tab_dashboard:
        st.sidebar.header("Filtros de Localização")
        estados_lista = sorted([x for x in df["UF"].unique() if x != 'Não Informado'])
        estados_selecionados = st.sidebar.multiselect("Estado (UF):", options=estados_lista, default=estados_lista)

        df_uf = df[df["UF"].isin(estados_selecionados)]
        portes_disponiveis = sorted(df_uf["TAMANHO DA CIDADE"].unique())
        portes_selecionados = st.sidebar.multiselect("Porte da Cidade:", options=portes_disponiveis, default=portes_disponiveis)

        df_filtrado_base = df_uf[df_uf["TAMANHO DA CIDADE"].isin(portes_selecionados)]
        cidades = sorted([x for x in df_filtrado_base["CIDADE"].unique() if x != 'Não Informado'])
        cidades_selecionadas
