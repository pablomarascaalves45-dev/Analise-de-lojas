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

# Estilização CSS corporativa
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    /* Estilo para os nossos cartões customizados */
    .metric-card {
        background-color: transparent;
        padding: 5px;
    }
    .metric-label {
        font-size: 14px;
        font-weight: 500;
        color: #4B5563;
        margin-bottom: 2px;
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #1E3A8A;
    }
    .metric-pct {
        font-size: 16px;
        color: #6B7280; /* Cor cinza para contraste */
        font-weight: normal;
        margin-left: 4px;
    }
    .metric-delta {
        font-size: 13px;
        color: #dc2626;
        background-color: #fee2e2;
        padding: 2px 8px;
        border-radius: 10px;
        display: inline-block;
        margin-top: 4px;
    }
    h1, h2, h3 { color: #1E3A8A; font-family: 'Segoe UI', sans-serif; }
    </style>
    """, unsafe_allow_html=True)

# Título do Painel Executivo
st.title("📊 Painel de Desempenho e Expansão Comercial")
st.markdown("Análise estratégica de faturamento, custos de ocupação, infraestrutura e safras de abertura.")
st.markdown("---")

# ==========================================
# SEÇÃO PARA ANEXAR A PLANILHA (CSV OU EXCEL)
# ==========================================
st.sidebar.header("📁 Carregar Base de Dados")
arquivo_carregado = st.sidebar.file_uploader(
    "Anexe a planilha de lojas (.csv ou .xlsx)", 
    type=["csv", "xlsx", "xls"]
)

def tratar_dados(df):
    df.columns = df.columns.astype(str).str.strip()
    colunas_numericas = ["MÉDIA FATURAMENTO DE MAI'25 ATÉ ABR'26", "Aluguel ABRI'26", "M² Salão Venda", "VENDA ABR'26", "DRE ABRI'26"]
    for col in colunas_numericas:
        if col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str).str.replace('R$', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip()
            df[col] = pd.to_numeric(df[col], errors='coerce')
    if 'DATA DE ABERTURA' in df.columns:
        df['DATA DE ABERTURA'] = pd.to_datetime(df['DATA DE ABERTURA'], errors='coerce')
        df['ANO_ABERTURA'] = df['DATA DE ABERTURA'].dt.year.fillna(0).astype(int)
    if 'ESTACIONAMENTO' in df.columns:
        df['TEM_ESTACIONAMENTO'] = df['ESTACIONAMENTO'].apply(lambda x: 'Não' if str(x).strip() == 'Não' else 'Sim')
    return df

if arquivo_carregado is not None:
    try:
        nome_arquivo = arquivo_carregado.name.lower()
        if nome_arquivo.endswith('.csv'):
            df_bruto = pd.read_csv(arquivo_carregado)
        else:
            excel_file = pd.ExcelFile(arquivo_carregado)
            aba_alvo = 'Lojas' if 'Lojas' in excel_file.sheet_names else excel_file.sheet_names[0]
            df_bruto = pd.read_excel(arquivo_carregado, sheet_name=aba_alvo)
            
        df_lojas = tratar_dados(df_bruto)
        
        # 1° BLOCO: VISÃO GERAL
        st.header("🏢 1° Bloco: Panorama Geral da Rede")
        total_lojas = int(df_lojas['ID_LOJA'].nunique()) if 'ID_LOJA' in df_lojas.columns else len(df_lojas)
        med_fat_abr = df_lojas["VENDA ABR'26"].mean()
        med_aluguel = df_lojas["Aluguel ABRI'26"].mean()
        med_m2 = df_lojas["M² Salão Venda"].mean()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total de Lojas", f"{total_lojas} PDVs")
        col2.metric("Fat. Médio (Abril/26)", f"R$ {med_fat_abr:,.2f}" if not pd.isna(med_fat_abr) else "N/A")
        col3.metric("Aluguel Médio (Abril/26)", f"R$ {med_aluguel:,.2f}" if not pd.isna(med_aluguel) else "N/A")
        col4.metric("Metragem Média (Salão)", f"{med_m2:,.1f} m²" if not pd.isna(med_m2) else "N/A")

        st.markdown("---")

        # 2° E 3° BLOCO: ESTACIONAMENTO
        st.header("🚗 Impacto de Vagas de Estacionamento no Resultado")
        df_com_vagas = df_lojas[df_lojas['TEM_ESTACIONAMENTO'] == 'Sim']
        df_sem_vagas = df_lojas[df_lojas['TEM_ESTACIONAMENTO'] == 'Não']

        col_com, col_sem = st.columns(2)
        with col_com:
            st.subheader("✅ 2° Bloco: Lojas COM Estacionamento")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Qtd Lojas com Vagas", f"{len(df_com_vagas)} PDVs")
            c2.metric("Fat. Médio (Abril/26)", f"R$ {df_com_vagas['VENDA ABR\'26'].mean():,.2f}")
            c3.metric("Aluguel Médio", f"R$ {df_com_vagas['Aluguel ABRI\'26'].mean():,.2f}")
            c4.metric("Metragem Média", f"{df_com_vagas['M² Salão Venda'].mean():,.1f} m²")

        with col_sem:
            st.subheader("❌ 3° Bloco: Lojas SEM Estacionamento")
            s1, s2, s3, s4 = st.columns(4)
            s1.metric("Qtd Lojas sem Vagas", f"{len(df_sem_vagas)} PDVs")
            s2.metric("Fat. Médio (Abril/26)", f"R$ {df_sem_vagas['VENDA ABR\'26'].mean():,.2f}")
            s3.metric("Aluguel Médio", f"R$ {df_sem_vagas['Aluguel ABRI\'26'].mean():,.2f}")
            s4.metric("Metragem Média", f"{df_sem_vagas['M² Salão Venda'].mean():,.1f} m²")

        st.markdown("---")

        # 4° BLOCO: EXPANSÃO / SAFRAS
        st.header("📈 4° Bloco: Análise de Expansão e Safras de Abertura (2020 - 2025)")
        anos_solicitados = [2020, 2021, 2022, 2023, 2024, 2025]
        df_safras_all = df_lojas[df_lojas['ANO_ABERTURA'].isin(anos_solicitados)].copy()
        
        lista_anos = sorted([int(x) for x in df_safras_all['ANO_ABERTURA'].unique() if x in anos_solicitados])
        ano_selecionado = st.sidebar.multiselect("Filtrar por Ano de Abertura", options=lista_anos, default=lista_anos)
        lista_ufs = sorted([str(x) for x in df_safras_all['UF'].dropna().unique()])
        uf_selecionada = st.sidebar.multiselect("Filtrar por Estado (UF)", options=lista_ufs, default=lista_ufs)

        df_filtrado = df_safras_all[(df_safras_all['ANO_ABERTURA'].isin(ano_selecionado)) & (df_safras_all['UF'].isin(uf_selecionada))].copy()

        if not df_filtrado.empty:
            safra_total_lojas = len(df_filtrado)
            safra_med_fat_abr = df_filtrado["VENDA ABR'26"].mean()
            safra_med_aluguel = df_filtrado["Aluguel ABRI'26"].mean()
            safra_med_m2 = df_filtrado["M² Salão Venda"].mean()
            
            safra_negativas = (df_filtrado["DRE ABRI'26"] < 0).sum()
            safra_com_vagas = (df_filtrado['TEM_ESTACIONAMENTO'] == 'Sim').sum()
            safra_sem_vagas = (df_filtrado['TEM_ESTACIONAMENTO'] == 'Não').sum()

            # Cálculos de Percentual
            pct_negativas = (safra_negativas / safra_total_lojas * 100) if safra_total_lojas > 0 else 0
            pct_com_vagas = (safra_com_vagas / safra_total_lojas * 100) if safra_total_lojas > 0 else 0
            pct_sem_vagas = (safra_sem_vagas / safra_total_lojas * 100) if safra_total_lojas > 0 else 0

            # Linha superior de métricas
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total de Aberturas", f"{safra_total_lojas} PDVs")
            m2.metric("Fat. Médio (Safra Abr/26)", f"R$ {safra_med_fat_abr:,.2f}")
            m3.metric("Aluguel Médio (Safra)", f"R$ {safra_med_aluguel:,.2f}")
            m4.metric("Metragem Média (Safra)", f"{safra_med_m2:,.1f} m²")

            # Linha inferior com CSS personalizado para as porcentagens menores e em outra cor
            st.write("") # Espaçador
            m5, m6, m7 = st.columns(3)

            with m5:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Lojas com DRE Negativo mês (ABRI'26)</div>
                    <div class="metric-value">{safra_negativas} PDVs <span class="metric-pct">({pct_negativas:.1f}%)</span></div>
                    <div class="metric-delta">↑ {safra_negativas} operando no vermelho</div>
                </div>
                """, unsafe_allow_html=True)

            with m6:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Safra Com Vagas</div>
                    <div class="metric-value">{safra_com_vagas} PDVs <span class="metric-pct">({pct_com_vagas:.1f}%)</span></div>
                </div>
                """, unsafe_allow_html=True)

            with m7:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Safra Sem Vagas</div>
                    <div class="metric-value">{safra_sem_vagas} PDVs <span class="metric-pct">({pct_sem_vagas:.1f}%)</span></div>
                </div>
                """, unsafe_allow_html=True)

            # Gráficos...
            st.markdown("### 🗺️ Volume de Aberturas por Estado (UF)")
            df_uf_group = df_filtrado.groupby(['UF', 'ANO_ABERTURA']).size().reset_index(name='Quantidade de Aberturas')
            df_uf_group['ANO_ABERTURA'] = df_uf_group['ANO_ABERTURA'].astype(str)
            fig_uf = px.bar(df_uf_group, x='UF', y='Quantidade de Aberturas', color='ANO_ABERTURA', barmode='stack', text_auto=True)
            st.plotly_chart(fig_uf, use_container_width=True)

            st.markdown("### 📉 Evolução Temporal de Aberturas")
            df_ano_group = df_filtrado.groupby('ANO_ABERTURA').size().reset_index(name='Quantidade de Lojas')
            fig_linha = px.line(df_ano_group, x='ANO_ABERTURA', y='Quantidade de Lojas', markers=True, text='Quantidade de Lojas')
            st.plotly_chart(fig_linha, use_container_width=True)

    except Exception as e:
        st.error(f"Erro ao processar: {e}")
