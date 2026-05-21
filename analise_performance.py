import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configurações da Página do Streamlit
st.set_page_config(
    page_title="Dashboard Executivo - Análise de Lojas",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS customizada para apresentação à Diretoria
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    div[data-testid="stMetricValue"] { font-size: 24px; font-weight: bold; color: #1E3A8A; }
    div[data-testid="stMetricLabel"] { font-size: 14px; font-weight: 500; color: #4B5563; }
    h1, h2, h3 { color: #1E3A8A; font-family: 'Segoe UI', sans-serif; }
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    </style>
    """, unsafe_allow_html=True)

# Título do Painel Executivo
st.title("📊 Painel de Desempenho e Expansão Comercial")
st.markdown("Análise estratégica de faturamento, custos de ocupação, infraestrutura e safras de abertura.")
st.markdown("---")

# ==========================================
# SEÇÃO PARA ANEXAR A PLANILHA EM EXCEL
# ==========================================
st.sidebar.header("📁 Carregar Base de Dados")
arquivo_carregado = st.sidebar.file_uploader(
    "Anexe a planilha original de lojas (.xlsx)", 
    type=["xlsx", "xls"],
    help="Carregue o arquivo original em Excel para gerar o relatório dinâmico."
)

# Função robusta para tratar e limpar os dados após o upload
def tratar_dados(df):
    # Forçar nomes de colunas como string e remover espaços extras nas pontas
    df.columns = df.columns.astype(str).str.strip()
    
    # Lista das colunas críticas que precisam ser puramente numéricas para os cálculos
    colunas_numericas = [
        "MÉDIA FATURAMENTO DE MAI'25 ATÉ ABR'26", 
        "Aluguel ABRI'26", 
        "M² Salão Venda", 
        "VENDA ABR'26", 
        "DRE ABRI'26"
    ]
    
    # Limpa e converte cada coluna para numérico (corrige textos errados transformando em nulo)
    for col in colunas_numericas:
        if col in df.columns:
            if df[col].dtype == 'object':
                # Converte para string, remove pontos de milhar e troca vírgula por ponto decimal
                df[col] = df[col].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Tratamento rigoroso de datas para evitar o KeyError
    if 'DATA DE ABERTURA' in df.columns:
        df['DATA DE ABERTURA'] = pd.to_datetime(df['DATA DE ABERTURA'], errors='coerce')
        # Extrai o ano convertendo para numérico e preenche nulos com 0 para não quebrar filtros
        df['ANO_ABERTURA'] = df['DATA DE ABERTURA'].dt.year.fillna(0).astype(int)
    else:
        df['ANO_ABERTURA'] = 0
    
    # Classificação padronizada de Estacionamento (Trata "Não", "1 à 5", "Maior que 10", etc)
    if 'ESTACIONAMENTO' in df.columns:
        df['TEM_ESTACIONAMENTO'] = df['ESTACIONAMENTO'].apply(lambda x: 'Não' if str(x).strip() == 'Não' else 'Sim')
    else:
        df['TEM_ESTACIONAMENTO'] = 'Não'
        
    return df

# Fluxo de verificação: Se o usuário
