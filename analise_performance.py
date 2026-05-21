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
    
    # Tratamento de datas e extração do Ano de Abertura
    if 'DATA DE ABERTURA' in df.columns:
        df['DATA DE ABERTURA'] = pd.to_datetime(df['DATA DE ABERTURA'], errors='coerce')
        df['ANO_ABERTURA'] = df['DATA DE ABERTURA'].dt.year
    else:
        df['ANO_ABERTURA'] = None
    
    # Classificação padronizada de Estacionamento (Trata "Não", "1 à 5", "Maior que 10", etc)
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

        total_lojas = int(df_lojas['ID_LOJA'].nunique()) if 'ID_LOJA' in df_lojas.columns else len(df_lojas)
        med_fat = df_lojas["MÉDIA FATURAMENTO DE MAI'25 ATÉ ABR'26"].mean()
        med_aluguel = df_lojas["Aluguel ABRI'26"].mean()
        med_m2 = df_lojas["M² Salão Venda"].mean()

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total de Lojas", f"{total_lojas} PDVs")
        with col2:
            st.metric("Faturamento Médio Mensal (12m)", f"R$ {med_fat:,.2f}" if not pd.isna(med_fat) else "N/A")
        with col3:
            st.metric("Aluguel Médio (Abril/26)", f"R$ {med_aluguel:,.2f}" if not pd.isna(med_aluguel) else "N/A")
        with col4:
            st.metric("Metragem Média (Salão)", f"{med_m2:,.1f} m²" if not pd.isna(med_m2) else "N/A")

        st.markdown("---")

        # ==========================================
        # 2° E 3° BLOCO: COM VS SEM ESTACIONAMENTO
        # ==========================================
        st.header("🚗 2 & 3. Impacto de Vagas de Estacionamento no Resultado")

        df_com_vagas = df_lojas[df_lojas['TEM_ESTACIONAMENTO'] == 'Sim']
        df_sem_vagas = df_lojas[df_lojas['TEM_ESTACIONAMENTO'] == 'Não']

        col_com, col_sem = st.columns(2)

        with col_com:
            st.subheader("✅ 2° Bloco: Lojas COM Estacionamento")
            c1, c2 = st.columns(2)
            c1.metric("Qtd Lojas", f"{len(df_com_vagas)} PDVs")
            c2.metric("Fat. Médio Mensal", f"R$ {df_com_vagas['MÉDIA FATURAMENTO DE MAI\'25 ATÉ ABR\'26'].mean():,.2f}")
            
            c3, c4 = st.columns(2)
            c3.metric("Aluguel Médio", f"R$ {df_com_vagas['Aluguel ABRI\'26'].mean():,.2f}")
            c4.metric("Metragem Média", f"{df_com_vagas['M² Salão Venda'].mean():,.1f} m²")

        with col_sem:
            st.subheader("❌ 3° Bloco: Lojas SEM Estacionamento")
            s1, s2 = st.columns(2)
            s1.metric("Qtd Lojas", f"{len(df_sem_vagas)} PDVs")
            s2.metric("Fat. Médio Mensal", f"R$ {df_sem_vagas['MÉDIA FATURAMENTO DE MAI\'25 ATÉ ABR\'26'].mean():,.2f}")
            
            s3, s4 = st.columns(2)
            s3.metric("Aluguel Médio", f"R$ {df_sem_vagas['Aluguel ABRI\'26'].mean():,.2f}")
            s4.metric("Metragem Média", f"{df_sem_vagas['M² Salão Venda'].mean():,.1f} m²")

        st.markdown("---")

        # ==========================================
        # 4° BLOCO: EXPANSÃO / SAFRAS (2020 A 2025)
        # ==========================================
        st.header("📈 4. Análise de Expansão e Safras de Abertura (2020 - 2025)")

        st.sidebar.markdown("---")
        st.sidebar.header("🎯 Filtros de Expansão")

        # Restringe estritamente aos anos solicitados pela diretoria
        anos_solicitados = [2020, 2021, 2022, 2023, 2024, 2025]
        df_safras_all = df_lojas[df_lojas['ANO_ABERTURA'].isin(anos_solicitados)]

        lista_anos = sorted(df_safras_all['ANO_ABERTURA'].dropna().unique().astype(int))
        ano_selecionado = st.sidebar.multiselect("Filtrar por Ano de Abertura", options=lista_anos, default=lista_anos)

        lista_ufs = sorted(df_safras_all['UF'].dropna().unique())
        uf_selecionada = st.sidebar.multiselect("Filtrar por Estado (UF)", options=lista_ufs, default=lista_ufs)

        # Aplicação dos filtros dinâmicos
        df_filtrado = df_safras_all[
            (df_safras_all['ANO_ABERTURA'].isin(ano_selecionado)) & 
            (df_safras_all['UF'].isin(uf_selecionada))
        ]

        if df_filtrado.empty:
            st.warning("Nenhuma loja encontrada para os filtros selecionados na barra lateral.")
        else:
            # Métricas solicitadas para a safra de lojas selecionadas
            safra_total_lojas = len(df_filtrado)
            safra_med_fat = df_filtrado["MÉDIA FATURAMENTO DE MAI'25 ATÉ ABR'26"].mean()
            safra_med_aluguel = df_filtrado["Aluguel ABRI'26"].mean()
            safra_med_m2 = df_filtrado["M² Salão Venda"].mean()
            safra_venda_abr = df_filtrado["VENDA ABR'26"].sum()
            
            # Lojas negativas no mês (DRE menor que 0)
            safra_negativas = (df_filtrado
