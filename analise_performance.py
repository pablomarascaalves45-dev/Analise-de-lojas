import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# Configuração da página
st.set_page_config(page_title="Dashboard de Performance", layout="wide")

st.title("Laboratório de Performance de Lojas")

# --- COMPONENTE DE UPLOAD ---
st.sidebar.header("Carga de Dados")
uploaded_file = st.sidebar.file_uploader("Upload do arquivo 'Teste de lojas.xlsx'", type=["xlsx"])

@st.cache_data
def load_data(file):
    # Carrega todas as abas caso o histórico esteja dividido por abas/anos, ou apenas a primeira
    excel_file = pd.ExcelFile(file)
    
    # Se houver múltiplas abas que parecem anos, podemos consolidar, 
    # mas para manter compatibilidade com seu script original, leremos a aba principal
    # e buscaremos colunas que contenham o histórico de faturamento.
    df = pd.read_excel(file, sheet_name=excel_file.sheet_names[0])
    
    # Limpa espaços em branco nos nomes das colunas
    df.columns = [c.strip() for c in df.columns]
    
    # --- CORREÇÃO DO ERRO DE SOMA E TRATAMENTO DE COLUNAS ---
    colunas_financeiras = ["VENDA MAR'26", "DRE FEV'26", "DRE_AC FEV'26", "MÉDIA FATURAMENTO DE ABR'25 ATÉ MAR'26"]
    
    # Identificar dinamicamente outras colunas de faturamento histórico (ex: FATURAMENTO 2024, VENDAS 2025, etc.)
    # Vamos tratar todas as colunas que possuem "FATURAMENTO", "VENDA" ou anos no nome como potenciais numéricos
    for col in df.columns:
        if any(keyword in col.upper() for keyword in ["VENDA", "DRE", "FATURAMENTO", "TICKET", "202", "ANO"]):
            if col != "TICKET FSJ MAR'26": # Tratado separadamente abaixo
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                
    for col in colunas_financeiras:
        if col in df.columns and df[col].dtype == object:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Tratamento específico para o Ticket Médio
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
    colunas_texto = ["UF", "CIDADE", "MESORREGIÃO", "LOJAS", "TAMANHO DA CIDADE", "NOME DA LOJA"]
    # Caso sua coluna de identificação da loja tenha outro nome (ex: "LOJAS" já armazena o nome), contornamos:
    if "NOME DA LOJA" not in df.columns and "LOJAS" in df.columns:
        df["NOME DA LOJA"] = df["LOJAS"]
        
    for col in colunas_texto:
        if col in df.columns:
            df[col] = df[col].astype(str).replace('nan', 'Não Informado')
            
    return df

def calcular_tempo_ate_500k(df_linha, colunas_anos):
    """Calcula quantos anos demorou para o faturamento passar de 500k"""
    anos_ordenados = sorted(colunas_anos)
    tempo = 0
    atingiu = False
    
    for i, col_ano in enumerate(anos_ordenados):
        faturamento = df_linha[col_ano].values[0] if hasattr(df_linha[col_ano], 'values') else df_linha[col_ano]
        if faturamento > 500000:
            tempo = i + 1  # Ano 1, Ano 2... ou baseado no ano de abertura se houver essa coluna
            atingiu = True
            break
            
    if atingiu:
        return f"{tempo}º Ano"
    return "Ainda não atingiu"

if uploaded_file is not None:
    df = load_data(uploaded_file)

    # Criação das Abas (Adicionada a Aba de Evolução Temporal sem destruir as anteriores)
    tab_dashboard, tab_expansao, tab_evolucao = st.tabs([
        "Dashboard de Performance", 
        "Relatório de Expansão", 
        "Curva de Evolução Histórica"
    ])

    # ==========================================
    # --- ABA 1: DASHBOARD DE PERFORMANCE ---
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
            m1, m2, m3, m4, m5, m6, m7 = st.columns(7)
            
            venda_total = df_visualizacao["VENDA MAR'26"].sum()
            qtd_lojas_total = df_visualizacao["LOJAS"].nunique()
            media_dre = df_visualizacao["DRE FEV'26"].mean() * 100 
            media_dre_ac = df_visualizacao["DRE_AC FEV'26"].mean() * 100
            
            ticket_medio = df_visualizacao["TICKET FSJ MAR'26"].mean()
            media_faturamento = df_visualizacao["MÉDIA FATURAMENTO DE ABR'25 ATÉ MAR'26"].mean()
            
            # Tratamento caso a coluna de população não exista em bases modificadas
            media_populacao = df_visualizacao["POPULAÇÃO RAIO DE 1KM"].mean() if "POPULAÇÃO RAIO DE 1KM" in df_visualizacao.columns else 0

            m1.metric("Qtd de Lojas", f"{qtd_lojas_total}")
            m2.metric("Venda Total", f"R$ {venda_total/1_000_000:.1f}M")
            m3.metric("Média DRE", f"{media_dre:.2f}%")
            m4.metric("DRE Acumulado", f"{media_dre_ac:.2f}%")
            m5.metric("Ticket Médio", f"R$ {ticket_medio:.2f}")
            m6.metric("Média Fat. Mensal", f"R$ {media_faturamento:,.0f}")
            m7.metric("Média População", f"{int(media_populacao):,}")

            st.divider()
            st.subheader("Eficiência e Hierarquia")
            foco_porte = st.selectbox("Filtrar detalhamento por Porte:", 
                                     ["Ver Todos"] + sorted(list(df_visualizacao["TAMANHO DA CIDADE"].unique())))
            
            col_v1, col_v2 = st.columns(2)
            with col_v1:
                df_porte_med = df_visualizacao.groupby(["MESORREGIÃO", "TAMANHO DA CIDADE"])["VENDA MAR'26"].mean().reset_index()
                fig_porte_med = px.bar(
                    df_porte_med, x="MESORREGIÃO", y="VENDA MAR'26", color="TAMANHO DA CIDADE",
                    title="Faturamento Médio: Região vs Porte", barmode="group",
                    color_discrete_sequence=px.colors.qualitative.Prism,
                    labels={"VENDA MAR'26": "Média (R$)"}
                )
                st.plotly_chart(fig_porte_med, use_container_width=True)

            with col_v2:
                fig_tree_med = px.treemap(
                    df_visualizacao, path=["MESORREGIÃO", "TAMANHO DA CIDADE", "CIDADE"], 
                    values="VENDA MAR'26", color="DRE FEV'26", color_continuous_scale="RdYlGn",
                    title="Hierarquia de Lojas e Rentabilidade"
                )
                st.plotly_chart(fig_tree_med, use_container_width=True)

            df_tabela_final = df_visualizacao if foco_porte == "Ver Todos" else df_visualizacao[df_visualizacao["TAMANHO DA CIDADE"] == foco_porte]
            st.subheader(f"Dados Detalhados: {foco_porte}")
            st.dataframe(df_tabela_final, use_container_width=True)
        else:
            st.warning("Nenhum dado encontrado para os filtros selecionados.")

    # ==========================================
    # --- ABA 2: RELATÓRIO DE EXPANSÃO ---
    # ==========================================
    with tab_expansao:
        st.header("Análise Estratégica para Expansão")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            fat_min = st.slider("Faturamento Mínimo Desejado (R$):", 0, 1500000, 500000, step=50000)
        with col_c2:
            dre_min = st.slider("Rentabilidade DRE Mínima (%):", -20.0, 40.0, 0.0, step=0.5) / 100

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
                title="Performance Média por Estado (Amostragem no Topo)", barmode="group",
                text="label_topo", labels={"Faturamento Médio": "Faturamento Médio (R$)", "Estado": "", "Porte da Cidade": ""}
            )
            
            fig_exp.update_traces(textposition='outside', textfont=dict(size=14, color="black"), cliponaxis=False)
            fig_exp.update_layout(xaxis_title=None, yaxis_tickprefix="R$ ", yaxis_tickformat=",.",
                                  legend=dict(title=None, orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5))
            
            st.plotly_chart(fig_exp, use_container_width=True)
            
            st.subheader("Matriz de Oportunidade Detalhada")
            st.dataframe(df_analise.sort_values(by=["Estado", "Faturamento Médio"], ascending=[True, False]), use_container_width=True)
        else:
            st.error("Nenhum dado atende aos critérios selecionados.")

    # =========================================================
    # --- NOVA ABA 3: CURVA DE EVOLUÇÃO HISTÓRICA (AJUSTE) ---
    # =========================================================
    with tab_evolucao:
        st.header("Análise Temporal e Curva de Crescimento")
        
        # Mapeamento Dinâmico de colunas de anos para construir a curva temporal
        # O script identifica dinamicamente colunas que representem anos ou faturamentos passados
        colunas_historicas_padrao = {
            "2023": "FATURAMENTO 2023", 
            "2024": "FATURAMENTO 2024", 
            "2025": "MÉDIA FATURAMENTO DE ABR'25 ATÉ MAR'26", 
            "2026": "VENDA MAR'26"
        }
        
        # Verificação se as colunas existem na planilha, senão busca correspondências aproximadas
        colunas_curva = {}
        for ano, nome_padrao in colunas_historicas_padrao.items():
            if nome_padrao in df.columns:
                colunas_curva[ano] = nome_padrao
            else:
                # Fallback: Procura qualquer coluna que tenha o Ano no nome
                for col in df.columns:
                    if ano in col and "DRE" not in col.upper():
                        colunas_curva[ano] = col
                        break
        
        if len(colunas_curva) < 2:
            # Caso não encontre colunas nomeadas por ano, cria uma simulação pedagógica estrutural com base nos dados reais atuais
            st.warning("Colunas explícitas de anos anteriores (ex: 2023, 2024) não foram mapeadas na aba principal. Gerando curva com base nos indicadores atuais para fins de projeção/análise.")
            df["FATURAMENTO 2024"] = df["MÉDIA FATURAMENTO DE ABR'25 ATÉ MAR'26"] * 0.85
            df["FATURAMENTO 2025"] = df["MÉDIA FATURAMENTO DE ABR'25 ATÉ MAR'26"]
            df["FATURAMENTO 2026"] = df["VENDA MAR'26"]
            colunas_curva = {"2024": "FATURAMENTO 2024", "2025": "FATURAMENTO 2025", "2026": "FATURAMENTO 2026"}

        # Filtros e Seletores Exclusivos da Curva Temporal
        c1, c2 = st.columns(2)
        with c1:
            estado_alvo = st.selectbox("1. Selecione o Estado para Análise da Curva Média:", sorted(df["UF"].unique()))
        with c2:
            df_lojas_estado = df[df["UF"] == estado_alvo]
            loja_alvo = st.selectbox("2. Selecione uma Loja específica deste Estado:", sorted(df_lojas_estado["NOME DA LOJA"].unique()))

        st.divider()
        
        # Processamento dos Dados para o Gráfico de Linha
        anos_eixo = sorted(list(colunas_curva.keys()))
        colunas_eixo = [colunas_curva[ano] for ano in anos_eixo]
        
        # Dados da Loja Selecionada
        dados_loja = df[df["NOME DA LOJA"] == loja_alvo]
        valores_loja = [dados_loja[colunas_curva[ano]].values[0] for ano in anos_eixo]
        
        # Dados da Média do Estado Selecionado
        dados_estado = df[df["UF"] == estado_alvo]
        valores_estado = [dados_estado[colunas_curva[ano]].mean() for ano in anos_eixo]
        
        # Montando DataFrame estruturado para o Plotly Express
        df_plot_loja = pd.DataFrame({"Ano": anos_eixo, "Faturamento": valores_loja, "Tipo": f"Loja: {loja_alvo}"})
        df_plot_estado = pd.DataFrame({"Ano": anos_eixo, "Faturamento": valores_estado, "Tipo": f"Média do Estado ({estado_alvo})"})
        df_plot_total = pd.concat([df_plot_loja, df_plot_estado])
        
        # Gráfico de Linhas - Curva de Faturamento
        fig_curva = px.line(
            df_plot_total, x="Ano", y="Faturamento", color="Tipo", markers=True,
            title=f"Curva de Evolução do Faturamento: {loja_alvo} vs Média de {estado_alvo}",
            labels={"Faturamento": "Faturamento (R$)", "Ano": "Linha do Tempo (Anos)"},
            color_discrete_sequence=["#1f77b4", "#ff7f0e"]
        )
        fig_curva.update_layout(yaxis_tickprefix="R$ ", yaxis_tickformat=",.", legend=dict(orientation="h", y=-0.2))
        st.plotly_chart(fig_curva, use_container_width=True)
        
        # --- CÁLCULO DE SUCESSO (> 500K) ---
        st.subheader("⏱️ Indicador Quinquenal / Tempo de Tração")
        
        col_m1, col_m2 = st.columns(2)
        
        with col_m1:
            # Tempo para a Loja específica
            tempo_loja = calcular_tempo_ate_500k(dados_loja, colunas_eixo)
            st.metric(
                label=f"Tempo para a loja '{loja_alvo}' faturar > R$ 500k", 
                value=tempo_loja
            )
            # Detalhe visual de auxílio
            st.caption("Cálculo realizado ano a ano varrendo a linha histórica da unidade de negócio selecionada.")
            
        with col_m2:
            # Tempo para a Média do Estado (Criação de um ponto sintético médio)
            dict_estado_medio = {col: dados_estado[col].mean() for col in colunas_eixo}
            tempo_estado = calcular_tempo_ate_500k(dict_estado_medio, colunas_eixo)
            st.metric(
                label=f"Tempo médio para o Estado ({estado_alvo}) faturar > R$ 500k", 
                value=tempo_estado
            )
            st.caption(f"Reflete a performance combinada e maturidade das praças situadas em {estado_alvo}.")

else:
    st.info("Por favor, faça o upload do arquivo Excel na barra lateral para começar.")
