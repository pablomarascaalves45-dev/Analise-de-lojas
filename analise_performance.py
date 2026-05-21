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
    "Anexe a planilha de lojas (.xlsx ou .xls)", 
    type=["xlsx", "xls"],
    help="Carregue o arquivo original em Excel para gerar o relatório dinâmico."
)

# Função para tratar e limpar os dados após o upload
def tratar_dados(df):
    # Forçar nomes de colunas como string e remover espaços extras
    df.columns = df.columns.astype(str).str.strip()
    
    # Tratamento de tipos numéricos
    df["MÉDIA FATURAMENTO DE MAI'25 ATÉ ABR'26"] = pd.to_numeric(df["MÉDIA FATURAMENTO DE MAI'25 ATÉ ABR'26"], errors='coerce')
    df["Aluguel ABRI'26"] = pd.to_numeric(df["Aluguel ABRI'26"], errors='coerce')
    df["M² Salão Venda"] = pd.to_numeric(df["M² Salão Venda"], errors='coerce')
    df["VENDA ABR'26"] = pd.to_numeric(df["VENDA ABR'26"], errors='coerce')
    df["DRE ABRI'26"] = pd.to_numeric(df["DRE ABRI'26"], errors='coerce')
    
    # Tratamento de datas e extração do Ano
    df['DATA DE ABERTURA'] = pd.to_datetime(df['DATA DE ABERTURA'], errors='coerce')
    df['ANO_ABERTURA'] = df['DATA DE ABERTURA'].dt.year
    
    # Classificação padronizada de Estacionamento
    if 'ESTACIONAMENTO' in df.columns:
        df['TEM_ESTACIONAMENTO'] = df['ESTACIONAMENTO'].apply(lambda x: 'Não' if str(x).strip() == 'Não' else 'Sim')
    else:
        df['TEM_ESTACIONAMENTO'] = 'Não'
        
    return df

# Fluxo de verificação: Se o usuário anexou o arquivo, roda o dashboard.
if arquivo_carregado is not None:
    try:
        # Carrega o Excel procurando de forma inteligente pela aba 'Lojas'
        excel_file = pd.ExcelFile(arquivo_carregado)
        aba_alvo = 'Lojas' if 'Lojas' in excel_file.sheet_names else excel_file.sheet_names[0]
        
        df_bruto = pd.read_excel(arquivo_carregado, sheet_name=aba_alvo)
        df_lojas = tratar_dados(df_bruto)
        
        # ==========================================
        # 1° BLOCO: VISÃO GERAL (TOTAL DA REDE)
        # ==========================================
        st.header("🏢 1. Panorama Geral da Rede")

        total_lojas = int(df_lojas['ID_LOJA'].nunique())
        med_fat = df_lojas
