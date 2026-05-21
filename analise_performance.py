import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import re

# Configuração da página
st.set_page_config(page_title="Dashboard de Performance", layout="wide", initial_sidebar_state="expanded")

st.title("Laboratório de Performance de Lojas")

# --- COMPONENTE DE UPLOAD ---
st.sidebar.header("Upload de Arquivos")
uploaded_file = st.sidebar.file_uploader("Upload do arquivo 'Teste de lojas.xlsx'", type=["xlsx"])

# Input para receber os arquivos de safras / inaugurações passadas
uploaded_inauguracoes = st.sidebar.file_uploader(
    "Upload dos arquivos de Safras/Inaugurações (2021 a 2025)", 
    type=["xlsx", "csv"], 
    accept_multiple_files=True
)

def load_data(file):
    df = pd.read_excel(file)
    # Limpa espaços em branco nos nomes das colunas
    df.columns = [c.strip() for c in df.columns]
    
    # --- TRATAMENTO E CONVERSÃO DE COLUNAS FINANCEIRAS CRUTIAIS ---
    colunas_financeiras = [
        "VENDA MAR'26", "DRE FEV'26", "DRE_AC FEV'26", 
        "MÉDIA FATURAMENTO DE ABR'25 ATÉ MAR'26", "INVESTIMENTO ACUMULADO",
        "MARGEM CONTRIBUIÇÃO MAR'26", "EBITDA MAR'26", "LUCRO LÍQUIDO MAR'26"
    ]
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
    colunas_texto = ["UF", "CIDADE", "MESORREGIÃO", "LOJAS", "TAMANHO DA CIDADE", "PERFIL CONSUMO", "SAFRA INAUGURAÇÃO"]
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
        
        # Filtra linhas de 'Total' ou vazias caso existam
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

    # Criação das Abas Originais Expandidas
    tab_dashboard, tab_expansao, tab_curva_faturamento = st.tabs([
        "📊 Dashboard de Performance", 
        "🚀 Relatório de Expansão", 
        "📈 Curva de Faturamento Histórica"
    ])

    # ==========================================
    # --- ABA 1: DASHBOARD DE PERFORMANCE ------
    # ==========================================
    with tab_dashboard:
        st.sidebar.header("Filtros de Localização")
        estados_lista = sorted([x for x in df["UF"].unique() if x != 'Não Informado'])
        estados_selecionados = st.sidebar.multiselect("Estado (UF):", options=estados_lista, default=estados_lista)

        df_uf = df[df["UF"].isin(estados_selecionados)]
        portes_disponiveis = sorted(df_uf["TAMANHO DA CIDADE"].unique())
        portes_selecionados = st.sidebar.multiselect("Porte da Cidade:", options=portes_disponiveis, default=portes_disponiveis)

        df_filtrado_base = df_uf[df_uf["TAMANHO DA CIDADE"].isin(portes_selecionados)]
        cidades = sorted([x for x in df_filtrado_base["CIDADE"].unique() if x != 'Não Informado'])
        cidades_selecionadas = st.sidebar.multiselect("Cidade:", options=cidades, default=cidades)

        mesos_list = [x for x in df_filtrado_base["MESORREGIÃO"].unique() if x and x != 'Não Informado']
        mesos = sorted(mesos_list)
        mesos_selecionados = st.sidebar.multiselect("Mesorregião:", options=mesos, default=mesos)

        df_visualizacao = df_filtrado_base[
            (df_filtrado_base["CIDADE"].isin(cidades_selecionadas)) & 
            (df_filtrado_base["MESORREGIÃO"].isin(mesos_selecionados))
        ]

        if not df_visualizacao.empty:
            # Painel de Principais Indicadores (KPIs)
            m1, m2, m3, m4, m5, m6, m7 = st.columns(7)
            
            venda_total = df_visualizacao["VENDA MAR'26"].sum()
            qtd_lojas_total = df_visualizacao["LOJAS"].nunique()
            media_dre = df_visualizacao["DRE FEV'26"].mean() * 100 
            media_dre_ac = df_visualizacao["DRE_AC FEV'26"].mean() * 100
            ticket_medio = df_visualizacao["TICKET FSJ MAR'26"].mean()
            media_faturamento = df_visualizacao["MÉDIA FATURAMENTO DE ABR'25 ATÉ MAR'26"].mean()
            media_populacao = df_visualizacao["POPULAÇÃO RAIO DE 1KM"].mean()

            m1.metric("Qtd de Lojas", f"{qtd_lojas_total}")
            m2.metric("Venda Total", f"R$ {venda_total/1_000_000:.2f}M")
            m3.metric("Média DRE", f"{media_dre:.2f}%")
            m4.metric("DRE Acumulado", f"{media_dre_ac:.2f}%")
            m5.metric("Ticket Médio", f"R$ {ticket_medio:.2f}")
            m6.metric("Média Fat. Mensal", f"R$ {media_faturamento:,.0f}")
            m7.metric("Média População Raio", f"{int(media_populacao):,}")

            st.divider()
            
            # Gráficos Avançados de Performance Coletiva
            st.subheader("Análise de Eficiência e Hierarquia Operacional")
            foco_porte = st.selectbox("Filtrar detalhamento por Porte da Cidade:", 
                                     ["Ver Todos"] + sorted(list(df_visualizacao["TAMANHO DA CIDADE"].unique())))
            
            col_v1, col_v2 = st.columns(2)
            with col_v1:
                df_porte_med = df_visualizacao.groupby(["MESORREGIÃO", "TAMANHO DA CIDADE"])["VENDA MAR'26"].mean().reset_index()
                fig_porte_med = px.bar(
                    df_porte_med, x="MESORREGIÃO", y="VENDA MAR'26", color="TAMANHO DA CIDADE",
                    title="Faturamento Médio Comercial: Região vs Porte da Cidade", barmode="group",
                    color_discrete_sequence=px.colors.qualitative.Prism,
                    labels={"VENDA MAR'26": "Média Faturamento (R$)", "MESORREGIÃO": "Mesorregião"}
                )
                fig_porte_med.update_layout(yaxis_tickprefix="R$ ", yaxis_tickformat=",.")
                st.plotly_chart(fig_porte_med, use_container_width=True)

            with col_v2:
                fig_tree_med = px.treemap(
                    df_visualizacao, path=["MESORREGIÃO", "TAMANHO DA CIDADE", "CIDADE"], 
                    values="VENDA MAR'26", color="DRE FEV'26", color_continuous_scale="RdYlGn",
                    title="Estrutura Hierárquica de Lojas e Rentabilidade Base"
                )
                st.plotly_chart(fig_tree_med, use_container_width=True)

            # Nova Seção de Correlação Dispersiva Avançada
            st.subheader("Correlação Dinâmica: Faturamento vs Variáveis Demográficas")
            col_scat1, col_scat2 = st.columns([1, 3])
            with col_scat1:
                eixo_x_selecionado = st.selectbox("Selecione a Métrica do Eixo X:", 
                                                  ["POPULAÇÃO RAIO DE 1KM", "INVESTIMENTO ACUMULADO", "TICKET FSJ MAR'26"])
            with col_scat2:
                fig_scatter = px.scatter(
                    df_visualizacao, x=eixo_x_selecionado, y="VENDA MAR'26", 
                    color="TAMANHO DA CIDADE", size="LOJAS" if "LOJAS" in df_visualizacao.columns else None,
                    hover_name="CIDADE", title=f"Dispersão Avançada: VENDA MAR'26 por {eixo_x_selecionado}",
                    trendline="ols", color_discrete_sequence=px.colors.qualitative.Bold
                )
                fig_scatter.update_layout(yaxis_tickprefix="R$ ", yaxis_tickformat=",.")
                st.plotly_chart(fig_scatter, use_container_width=True)

            # Tabela Dinâmica Detalhada
            df_tabela_final = df_visualizacao if foco_porte == "Ver Todos" else df_visualizacao[df_visualizacao["TAMANHO DA CIDADE"] == foco_porte]
            st.subheader(f"Dados Consolidados Detalhados: {foco_porte}")
            st.dataframe(df_tabela_final, use_container_width=True)
        else:
            st.warning("Nenhum registro correspondente aos filtros foi localizado na base.")

    # ==========================================
    # --- ABA 2: RELATÓRIO DE EXPANSÃO ---------
    # ==========================================
    with tab_expansao:
        st.header("Análise Estratégica e Matriz de Oportunidade para Expansão")
        
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            fat_min = st.slider("Clas. Sucesso - Faturamento Mínimo Desejado (R$):", 0, 1500000, 500000, step=50000)
        with col_c2:
            dre_min = st.slider("Clas. Sucesso - Rentabilidade DRE Mínima (%):", -20.0, 40.0, 0.0, step=0.5) / 100

        # Regra de Filtragem Avançada das Lojas Modelo (Benchmark de Sucesso)
        df_sucesso = df[(df["VENDA MAR'26"] > fat_min) & (df["DRE FEV'26"] > dre_min)].copy()

        if not df_sucesso.empty:
            df_analise = df_sucesso.groupby(["UF", "TAMANHO DA CIDADE"]).agg({
                "VENDA MAR'26": "mean",
                "DRE FEV'26": "mean",
                "LOJAS": "count"
            }).reset_index()

            df_analise.columns = ["Estado", "Porte da Cidade", "Faturamento Médio", "Margem DRE Média", "Qtd Lojas"]
            df_analise["label_topo"] = df_analise["Qtd Lojas"].astype(str) + " Lojas"

            fig_exp = px.bar(
                df_analise, x="Estado", y="Faturamento Médio", color="Porte da Cidade",
                title="Performance Média por Estado e Regiões Promissoras (Amostragem no Topo)", barmode="group",
                text="label_topo", labels={"Faturamento Médio": "Faturamento Médio (R$)"}
            )
            
            fig_exp.update_traces(textposition='outside', textfont=dict(size=13, color="black"), cliponaxis=False)
            fig_exp.update_layout(xaxis_title="Estados Analisados", yaxis_tickprefix="R$ ", yaxis_tickformat=",.",
                                  legend=dict(title="Porte de Cidades", orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5))
            
            st.plotly_chart(fig_exp, use_container_width=True)
            
            # Adição do Gráfico de Quadrantes Estratégicos (Potencial vs Retorno)
            st.subheader("Matriz de Posicionamento Estratégico Regional")
            fig_quadrantes = px.scatter(
                df_analise, x="Margem DRE Média", y="Faturamento Médio", color="Porte da Cidade",
                text="Estado", size="Qtd Lojas", title="Mapeamento de Quadrantes (Tamanho da Bolha = Volumetria de Lojas)"
            )
            fig_quadrantes.add_hline(y=df_analise["Faturamento Médio"].mean(), line_dash="dash", line_color="gray", annotation_text="Faturamento Médio")
            fig_quadrantes.add_vline(x=df_analise["Margem DRE Média"].mean(), line_dash="dash", line_color="gray", annotation_text="DRE Médio")
            st.plotly_chart(fig_quadrantes, use_container_width=True)
            
            st.subheader("Matriz de Oportunidade Detalhada")
            st.dataframe(df_analise.sort_values(by=["Estado", "Faturamento Médio"], ascending=[True, False]), use_container_width=True)
        else:
            st.error("Não há registros que atinjam os parâmetros mínimos de Faturamento e DRE configurados acima.")

    # ==========================================
    # --- ABA 3: CURVA HISTÓRICA (SAFRAS) ------
    # ==========================================
    with tab_curva_faturamento:
        st.header("Análise de Curva de Faturamento Coletiva por Safras")
        
        if uploaded_inauguracoes:
            df_inauguracoes = processar_inauguracoes(uploaded_inauguracoes)
            
            if not df_inauguracoes.empty:
                # Mapeia dinamicamente colunas no formato 'Vendas MM/AAAA'
                col_vendas = [c for c in df_inauguracoes.columns if re.match(r'Vendas\s+\d{2}/\d{4}', c)]
                
                # Conversão das colunas de vendas para valores numéricos limpos
                for col in col_vendas:
                    df_inauguracoes[col] = pd.to_numeric(df_inauguracoes[col].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False), errors='coerce').fillna(0)
                
                # Procura associar o Estado (UF) às lojas baseado no primeiro arquivo (df principal)
                if "Desc. Loja" in df_inauguracoes.columns and "LOJAS" in df.columns and "UF" in df.columns:
                    depara_uf = df.set_index("LOJAS")["UF"].to_dict()
                    df_inauguracoes["UF"] = df_inauguracoes["Desc. Loja"].map(depara_uf).fillna("Não Informado")
                elif "UF" not in df_inauguracoes.columns:
                    df_inauguracoes["UF"] = "Não Informado"

                # --- FILTROS DE VISUALIZAÇÃO DA CURVA ---
                st.subheader("Configurações do Gráfico Dinâmico")
                c_filtro1, c_filtro2 = st.columns(2)
                
                with c_filtro1:
                    ufs_disponiveis = sorted(list(df_inauguracoes["UF"].unique()))
                    uf_selecionada =
