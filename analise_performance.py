import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da página
st.set_page_config(page_title="Dashboard de Performance", layout="wide")

st.title("Laboratório de Performance de Lojas")

# --- COMPONENTE DE UPLOAD ---
uploaded_file = st.sidebar.file_uploader("Upload do arquivo 'Teste de lojas.xlsx'", type=["xlsx"])

def load_data(file):
    df = pd.read_excel(file)
    # Limpa espaços em branco nos nomes das colunas
    df.columns = [c.strip() for c in df.columns]
    
    # Tratamento de valores monetários (Ticket Médio)
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

# Só executa o restante se o arquivo for carregado
if uploaded_file is not None:
    df = load_data(uploaded_file)

    # Criação das Abas
    tab_dashboard, tab_expansao = st.tabs(["Dashboard de Performance", "Relatório de Expansão"])

    # --- ABA 1: DASHBOARD ---
    with tab_dashboard:
        st.sidebar.header("Filtros de Localização")
        estados_lista = sorted([x for x in df["UF"].unique() if x])
        estados_selecionados = st.sidebar.multiselect("Estado (UF):", options=estados_lista, default=estados_lista)

        df_uf = df[df["UF"].isin(estados_selecionados)]
        portes_disponiveis = sorted(df_uf["TAMANHO DA CIDADE"].unique())
        portes_selecionados = st.sidebar.multiselect("Porte da Cidade:", options=portes_disponiveis, default=portes_disponiveis)

        df_filtrado_base = df_uf[df_uf["TAMANHO DA CIDADE"].isin(portes_selecionados)]
        cidades = sorted([x for x in df_filtrado_base["CIDADE"].unique() if x])
        cidades_selecionadas = st.sidebar.multiselect("Cidade:", options=cidades, default=cidades)

        mesos_list = [x for x in df_filtrado_base["MESORREGIÃO"].unique() if x and x != 'Não Informado']
        mesos = sorted(mesos_list)
        mesos_selecionados = st.sidebar.multiselect("Mesorregião:", options=mesos, default=mesos)

        df_visualizacao = df_filtrado_base[
            (df_filtrado_base["CIDADE"].isin(cidades_selecionadas)) & 
            (df_filtrado_base["MESORREGIÃO"].isin(mesos_selecionados))
        ]

        if not df_visualizacao.empty:
            m1, m2, m3, m4, m5, m6 = st.columns(6)
            
            venda_total = df_visualizacao["VENDA MAR'26"].sum()
            qtd_lojas_total = df_visualizacao["LOJAS"].nunique()
            media_dre = df_visualizacao["DRE FEV'26"].mean() * 100 
            ticket_medio = df_visualizacao["TICKET FSJ MAR'26"].mean()
            media_faturamento = df_visualizacao["MÉDIA FATURAMENTO DE ABR'25 ATÉ MAR'26"].mean()
            media_populacao = df_visualizacao["POPULAÇÃO RAIO DE 1KM"].mean()

            m1.metric("Qtd de Lojas", f"{qtd_lojas_total}")
            m2.metric("Venda Total", f"R$ {venda_total/1_000_000:.1f}M")
            m3.metric("Média DRE", f"{media_dre:.2f}%")
            m4.metric("Ticket Médio", f"R$ {ticket_medio:.2f}")
            m5.metric("Média Fat. Anual", f"R$ {media_faturamento:,.0f}")
            m6.metric("Média População (1km)", f"{int(media_populacao):,}")

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

    # --- ABA 2: EXPANSÃO ---
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

            # --- NOVA LÓGICA DE RECOMENDAÇÃO INDIVIDUALIZADA POR ESTADO ---
            st.subheader("Observações Estratégicas por Estado")
            
            # Pegamos os estados que aparecem no filtro de sucesso
            estados_sucesso = sorted(df_sucesso["UF"].unique())
            
            for estado in estados_sucesso:
                # Dados específicos do estado dentro das lojas de sucesso
                df_estado_sucesso = df_sucesso[df_sucesso["UF"] == estado]
                total_lojas_estado = len(df_estado_sucesso)
                
                # Agrupar por porte para achar o melhor
                resumo_porte = df_estado_sucesso.groupby("TAMANHO DA CIDADE").agg({
                    "VENDA MAR'26": "mean",
                    "LOJAS": "count"
                }).reset_index()
                
                # Critério: Maior faturamento médio
                melhor_porte_row = resumo_porte.sort_values(by="VENDA MAR'26", ascending=False).iloc[0]
                
                nome_porte = melhor_porte_row["TAMANHO DA CIDADE"]
                fat_medio = melhor_porte_row["VENDA MAR'26"]
                qtd_no_porte = melhor_porte_row["LOJAS"]
                representatividade = (qtd_no_porte / total_lojas_estado) * 100
                
                # Exibição do Insight por Estado
                st.success(f"📍 **Estado: {estado}** | O melhor porte para expandir é **{nome_porte}**. "
                           f"Ele possui o maior faturamento médio (**R$ {fat_medio:,.2f}**) e representa "
                           f"**{representatividade:.1f}%** das unidades de sucesso mapeadas neste estado.")

            st.divider()
            st.subheader("Matriz de Oportunidade Detalhada")
            st.dataframe(
                df_analise.sort_values(by=["Estado", "Faturamento Médio"], ascending=[True, False]).style.format({
                    "Faturamento Médio": "R$ {:,.2f}",
                    "Margem DRE Média": "{:.2%}"
                }), 
                use_container_width=True
            )
        else:
            st.error("Nenhum dado atende aos critérios de faturamento e DRE selecionados.")

else:
    st.info("Por favor, faça o upload do arquivo Excel na barra lateral para começar.")
