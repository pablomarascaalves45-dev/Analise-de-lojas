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
# SEÇÃO PARA ANEXAR A PLANILHA (CSV OU EXCEL)
# ==========================================
st.sidebar.header("📁 Carregar Base de Dados")
arquivo_carregado = st.sidebar.file_uploader(
    "Anexe a planilha de lojas (.csv ou .xlsx)", 
    type=["csv", "xlsx", "xls"],
    help="Carregue o arquivo extraído para gerar o relatório dinâmico automaticamente."
)

# Função robusta para tratar e limpar os dados após o upload
def tratar_dados(df):
    df.columns = df.columns.astype(str).str.strip()
    
    colunas_numericas = [
        "MÉDIA FATURAMENTO DE MAI'25 ATÉ ABR'26", 
        "Aluguel ABRI'26", 
        "M² Salão Venda", 
        "VENDA ABR'26", 
        "DRE ABRI'26"
    ]
    
    for col in colunas_numericas:
        if col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str).str.strip()
                df[col] = df[col].str.replace('R$', '', regex=False).str.strip()
                df[col] = df[col].str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
            
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    if 'DATA DE ABERTURA' in df.columns:
        df['DATA DE ABERTURA'] = pd.to_datetime(df['DATA DE ABERTURA'], errors='coerce')
        df['ANO_ABERTURA'] = df['DATA DE ABERTURA'].dt.year.fillna(0).astype(int)
    else:
        df['ANO_ABERTURA'] = 0
    
    if 'ESTACIONAMENTO' in df.columns:
        df['TEM_ESTACIONAMENTO'] = df['ESTACIONAMENTO'].apply(lambda x: 'Não' if str(x).strip() == 'Não' else 'Sim')
    else:
        df['TEM_ESTACIONAMENTO'] = 'Não'
        
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
        
        # ==========================================
        # 1° BLOCO: VISÃO GERAL (TOTAL DA REDE)
        # ==========================================
        st.header("🏢 1° Bloco: Panorama Geral da Rede")

        total_lojas = int(df_lojas['ID_LOJA'].nunique()) if 'ID_LOJA' in df_lojas.columns else len(df_lojas)
        
        med_aluguel = df_lojas["Aluguel ABRI'26"].mean()
        med_m2 = df_lojas["M² Salão Venda"].mean()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de Lojas", f"{total_lojas} PDVs")
        with col2:
            st.metric("Aluguel Médio (Abril/26)", f"R$ {med_aluguel:,.2f}" if not pd.isna(med_aluguel) else "N/A")
        with col3:
            st.metric("Metragem Média (Salão)", f"{med_m2:,.1f} m²" if not pd.isna(med_m2) else "N/A")

        st.markdown("---")

        # ==========================================
        # 2° E 3° BLOCO: COM VS SEM ESTACIONAMENTO
        # ==========================================
        st.header("🚗 Impacto de Vagas de Estacionamento no Resultado")

        df_com_vagas = df_lojas[df_lojas['TEM_ESTACIONAMENTO'] == 'Sim']
        df_sem_vagas = df_lojas[df_lojas['TEM_ESTACIONAMENTO'] == 'Não']

        col_com, col_sem = st.columns(2)

        with col_com:
            st.subheader("✅ 2° Bloco: Lojas COM Estacionamento")
            c1, c2, c3 = st.columns(3)
            c1.metric("Qtd Lojas com Vagas", f"{len(df_com_vagas)} PDVs")
            c2.metric("Aluguel Médio", f"R$ {df_com_vagas['Aluguel ABRI\'26'].mean():,.2f}")
            c3.metric("Metragem Média", f"{df_com_vagas['M² Salão Venda'].mean():,.1f} m²")

        with col_sem:
            st.subheader("❌ 3° Bloco: Lojas SEM Estacionamento")
            s1, s2, s3 = st.columns(3)
            s1.metric("Qtd Lojas sem Vagas", f"{len(df_sem_vagas)} PDVs")
            s2.metric("Aluguel Médio", f"R$ {df_sem_vagas['Aluguel ABRI\'26'].mean():,.2f}")
            s3.metric("Metragem Média", f"{df_sem_vagas['M² Salão Venda'].mean():,.1f} m²")

        st.markdown("---")

        # ==========================================
        # 4° BLOCO: EXPANSÃO / SAFRAS (2020 A 2025)
        # ==========================================
        st.header("📈 4° Bloco: Análise de Expansão e Safras de Abertura (2020 - 2025)")

        st.sidebar.markdown("---")
        st.sidebar.header("🎯 Filtros de Expansão")

        anos_solicitados = [2020, 2021, 2022, 2023, 2024, 2025]
        df_safras_all = df_lojas[df_lojas['ANO_ABERTURA'].isin(anos_solicitados)].copy()

        lista_anos = sorted([int(x) for x in df_safras_all['ANO_ABERTURA'].unique() if x in anos_solicitados])
        
        if not lista_anos:
            st.warning("Nota: Nenhum dado de abertura correspondente aos anos de 2020 a 2025 foi encontrado.")
            ano_selecionado = []
        else:
            ano_selecionado = st.sidebar.multiselect("Filtrar por Ano de Abertura", options=lista_anos, default=lista_anos)

        lista_ufs = sorted([str(x) for x in df_safras_all['UF'].dropna().unique()])
        uf_selecionada = st.sidebar.multiselect("Filtrar por Estado (UF)", options=lista_ufs, default=lista_ufs)

        df_filtrado = df_safras_all[
            (df_safras_all['ANO_ABERTURA'].isin(ano_selecionado)) & 
            (df_safras_all['UF'].isin(uf_selecionada))
        ].copy()

        if df_filtrado.empty:
            st.warning("Selecione os Anos e Estados desejados na barra lateral.")
        else:
            safra_total_lojas = len(df_filtrado)
            safra_med_aluguel = df_filtrado["Aluguel ABRI'26"].mean()
            safra_med_m2 = df_filtrado["M² Salão Venda"].mean()
            
            safra_negativas = (df_filtrado["DRE ABRI'26"] < 0).sum()
            safra_com_vagas = (df_filtrado['TEM_ESTACIONAMENTO'] == 'Sim').sum()
            safra_sem_vagas = (df_filtrado['TEM_ESTACIONAMENTO'] == 'Não').sum()

            m1, m2, m3 = st.columns(3)
            m1.metric("Total de Aberturas", f"{safra_total_lojas} PDVs")
            m2.metric("Aluguel Médio (Safra)", f"R$ {safra_med_aluguel:,.2f}" if not pd.isna(safra_med_aluguel) else "N/A")
            m3.metric("Metragem Média (Safra)", f"{safra_med_m2:,.1f} m²" if not pd.isna(safra_med_m2) else "N/A")

            m4, m5, m6 = st.columns(3)
            m4.metric("Lojas com DRE Negativo", f"{safra_negativas} PDVs", delta=f"{safra_negativas} operando no vermelho", delta_color="inverse")
            m5.metric("Safra Com Vagas", f"{safra_com_vagas} PDVs")
            m6.metric("Safra Sem Vagas", f"{safra_sem_vagas} PDVs")

            # ----------------------------------------------------
            # GRÁFICO 1: GRÁFICO DE BARRAS POR UF COM RÓTULOS NO TOPO
            # ----------------------------------------------------
            st.markdown("### 🗺️ Volume de Aberturas por Estado (UF)")
            df_uf_group = df_filtrado.groupby(['UF', 'ANO_ABERTURA']).size().reset_index(name='Quantidade de Aberturas')
            df_uf_group['ANO_ABERTURA'] = df_uf_group['ANO_ABERTURA'].astype(str)
            
            fig_uf = px.bar(
                df_uf_group, 
                x='UF', 
                y='Quantidade de Aberturas', 
                color='ANO_ABERTURA',
                title="Histórico de Expansão (Aberturas por Estado)",
                labels={'UF': 'Estado', 'ANO_ABERTURA': 'Ano de Abertura'},
                barmode='stack',
                color_continuous_scale=px.colors.sequential.Blues,
                text_auto=True 
            )
            fig_uf.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_uf, use_container_width=True)

            # ----------------------------------------------------
            # GRÁFICO 2: GRÁFICO DE LINHA HISTÓRICA DE ANOS
            # ----------------------------------------------------
            st.markdown("### 📉 Evolução Temporal de Aberturas (2020 - 2025)")
            
            df_ano_group = df_filtrado.groupby('ANO_ABERTURA').size().reset_index(name='Quantidade de Lojas')
            
            df_base_anos = pd.DataFrame({'ANO_ABERTURA': ano_selecionado})
            df_ano_group = pd.merge(df_base_anos, df_ano_group, on='ANO_ABERTURA', how='left').fillna(0)
            df_ano_group['Quantidade de Lojas'] = df_ano_group['Quantidade de Lojas'].astype(int)
            df_ano_group = df_ano_group.sort_values('ANO_ABERTURA')
            
            df_ano_group['Rotulo'] = df_ano_group['Quantidade de Lojas'].apply(lambda x: f"{x} lojas")

            fig_linha = px.line(
                df_ano_group,
                x='ANO_ABERTURA',
                y='Quantidade de Lojas',
                title="Evolução de Aberturas por Ano (Visão Crítica de Volume)",
                labels={'ANO_ABERTURA': 'Ano de Abertura', 'Quantidade de Lojas': 'Lojas Abertas'},
                markers=True,
                text='Rotulo'
            )
            fig_linha.update_traces(textposition="top center", line=dict(color='#1E3A8A', width=3))
            fig_linha.update_layout(
                plot_bgcolor='rgba(0,0,0,0)', 
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(tickmode='linear')
            )
            st.plotly_chart(fig_linha, use_container_width=True)

            # Tabela Executiva Detalhada
            st.markdown("### 📋 Listagem de Lojas da Janela de Expansão")
            colunas_exibicao = ['ID_LOJA', 'LOJAS', 'UF', 'ANO_ABERTURA', 
                                "MÉDIA FATURAMENTO DE MAI'25 ATÉ ABR'26", "Aluguel ABRI'26", 
                                'M² Salão Venda', "VENDA ABR'26", "DRE ABRI'26", 'TEM_ESTACIONAMENTO']
            
            colunas_existentes = [c for c in colunas_exibicao if c in df_filtrado.columns]
            
            st.dataframe(
                df_filtrado[colunas_existentes].style.format({
                    "MÉDIA FATURAMENTO DE MAI'25 ATÉ ABR'26": "R$ {:,.2f}",
                    "Aluguel ABRI'26": "R$ {:,.2f}",
                    "M² Salão Venda": "{:,.1f} m²",
                    "VENDA ABR'26": "R$ {:,.2f}",
                    "DRE ABRI'26": "{:,.2%}"
                }, na_rep="N/A"), 
                use_container_width=True
            )
    except Exception as e:
        st.error(f"Erro inesperado ao processar o arquivo estrutural. Detalhes técnicos: {e}")
else:
    st.info("👋 Tudo pronto! Basta arrastar ou anexar o seu arquivo de lojas (`.csv` ou `.xlsx`) no campo à esquerda para carregar o painel da diretoria.")
