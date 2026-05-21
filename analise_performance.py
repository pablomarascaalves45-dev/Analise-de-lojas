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

            media_populacao = df_visualizacao["POPULAÇÃO RAIO DE 1KM"].mean()



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

            

            st.subheader("Matriz de Oportunidade Detalhada")

            st.dataframe(df_analise.sort_values(by=["Estado", "Faturamento Médio"], ascending=[True, False]), use_container_width=True)

        else:

            st.error("Nenhum dado atende aos critérios selecionados.")



    # --- NOVA ABA 3: CURVA DE FATURAMENTO HISTÓRICA (SAFRAS) ---

    with tab_curva_faturamento:

        st.header("Análise de Curva de Faturamento com o Passar dos Anos")

        

        if uploaded_inauguracoes:

            df_inauguracoes = processar_inauguracoes(uploaded_inauguracoes)

            

            if not df_inauguracoes.empty:

                # Mapeia colunas no formato 'Vendas MM/AAAA'

                col_vendas = [c for c in df_inauguracoes.columns if re.match(r'Vendas\s+\d{2}/\d{4}', c)]

                

                # Conversão das colunas de vendas mapeadas para valores numéricos limpos

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

                    uf_selecionada = st.selectbox("Selecione o Estado para Análise de Curva Média:", ["Todos"] + ufs_disponiveis)

                    

                with c_filtro2:

                    # Filtra a listagem de lojas pelo estado previamente selecionado para facilitar a busca

                    if uf_selecionada != "Todos":

                        lojas_disponiveis = sorted(list(df_inauguracoes[df_inauguracoes["UF"] == uf_selecionada]["Desc. Loja"].unique()))

                    else:

                        lojas_disponiveis = sorted(list(df_inauguracoes["Desc. Loja"].unique()))

                    loja_selecionada = st.selectbox("Selecione uma Loja Específica para detalhar:", ["Desconsiderar Loja (Apenas Estado)"] + lojas_disponiveis)



                # --- PROCESSAMENTO DOS DADOS PARA O GRÁFICO (MELT) ---

                # Extrai a evolução cronológica pura do faturamento

                df_melted = df_inauguracoes.melt(

                    id_vars=["Desc. Loja", "UF"], 

                    value_vars=col_vendas, 

                    var_name="Periodo", 

                    value_name="Faturamento"

                )

                # Limpa a string "Vendas " para ordenar por data real no eixo X

                df_melted["Data_Eixo"] = df_melted["Periodo"].str.replace(r'Vendas\s+', '', regex=True)

                df_melted["Data_Eixo"] = pd.to_datetime(df_melted["Data_Eixo"], format='%m/%Y', errors='coerce')

                df_melted = df_melted.sort_values("Data_Eixo")

                df_melted["Mês/Ano"] = df_melted["Data_Eixo"].dt.strftime('%m/%Y')



                # Geração de visões baseadas nos filtros

                if uf_selecionada != "Todos":

                    df_estado_curva = df_melted[df_melted["UF"] == uf_selecionada].groupby("Mês/Ano", sort=False)["Faturamento"].mean().reset_index()

                    label_estado = f"Média do Estado ({uf_selecionada})"

                else:

                    df_estado_curva = df_melted.groupby("Mês/Ano", sort=False)["Faturamento"].mean().reset_index()

                    label_estado = "Média Geral de Todos Estados"



                df_estado_curva["Tipo"] = label_estado



                # Ajuste para evitar NameError definindo df_loja_especifica de forma segura

                if loja_selecionada != "Desconsiderar Loja (Apenas Estado)":

                    df_loja_especifica = df_melted[df_melted["Desc. Loja"] == loja_selecionada]

                    titulo_grafico = f"Evolução Temporal: Loja {loja_selecionada} vs {label_estado}"

                    

                    df_loja_especifica_plot = df_loja_especifica[["Mês/Ano", "Faturamento"]].copy()

                    df_loja_especifica_plot["Tipo"] = f"Loja: {loja_selecionada}"

                    df_plot_final = pd.concat([df_loja_especifica_plot, df_estado_curva], ignore_index=True)

                else:

                    df_loja_especifica = pd.DataFrame()

                    titulo_grafico = f"Evolução Temporal: {label_estado}"

                    df_plot_final = df_estado_curva



                fig_curva = px.line(

                    df_plot_final, x="Mês/Ano", y="Faturamento", color="Tipo",

                    title=titulo_grafico, markers=True,

                    labels={"Faturamento": "Faturamento (R$)", "Mês/Ano": "Período Analisado"}

                )

                fig_curva.update_layout(yaxis_tickprefix="R$ ", yaxis_tickformat=",.")

                st.plotly_chart(fig_curva, use_container_width=True)



                # --- CÁLCULO DE MÉTRICA DE TEMPO ATÉ ATINGIR 500K ---

                st.divider()

                st.subheader("Tempo de Maturação (Rampa de Faturamento > R$ 500k)")

                

                # Se uma loja específica estiver selecionada, renderiza duas colunas normalmente

                if loja_selecionada != "Desconsiderar Loja (Apenas Estado)":

                    col_m1, col_m2 = st.columns(2)

                    

                    with col_m1:

                        df_loja_cronologico = df_loja_especifica.dropna(subset=["Faturamento"]).reset_index()

                        meses_ate_500k_loja = "Não atingiu faturamento > 500k no período"

                        

                        contador = 1

                        for index, row in df_loja_cronologico.iterrows():

                            if row["Faturamento"] >= 500000:

                                meses_ate_500k_loja = f"{contador} mês(es) após início do histórico registrado"

                                break

                            contador += 1

                            

                        st.metric(label=f"Tempo para a loja '{loja_selecionada}' faturar > 500k", value=meses_ate_500k_loja)



                    with col_m2:

                        df_uf_contexto = df_melted if uf_selecionada == "Todos" else df_melted[df_melted["UF"] == uf_selecionada]

                        df_uf_cronologico = df_uf_contexto.groupby("Mês/Ano", sort=False)["Faturamento"].mean().reset_index()

                        meses_ate_500k_uf = "Média do Estado não atingiu > 500k"

                        

                        contador_uf = 1

                        for index, row in df_uf_cronologico.iterrows():

                            if row["Faturamento"] >= 500000:

                                meses_ate_500k_uf = f"Em média {contador_uf} mês(es)"

                                break

                            contador_uf += 1

                            

                        st.metric(label=f"Tempo médio do Estado ({uf_selecionada}) para faturar > 500k", value=meses_ate_500k_uf)

                else:

                    # Se não houver loja selecionada, exibe apenas a métrica regional consolidada em largura total

                    df_uf_context = df_melted if uf_selecionada == "Todos" else df_melted[df_melted["UF"] == uf_selecionada]

                    df_uf_cronologico = df_uf_context.groupby("Mês/Ano", sort=False)["Faturamento"].mean().reset_index()

                    meses_ate_500k_uf = "Média regional não atingiu > 500k"

                    

                    contador_uf = 1

                    for index, row in df_uf_cronologico.iterrows():

                        if row["Faturamento"] >= 500000:

                            meses_ate_500k_uf = f"Em média {contador_uf} mês(es)"

                            break

                        contador_uf += 1

                        

                    st.metric(label=f"Tempo médio regional ({uf_selecionada}) para faturar > 500k (Visão Consolidada)", value=meses_ate_500k_uf)



            else:

                st.error("Não foi possível processar os dados das planilhas de safras anexadas.")

        else:

            st.info("💡 Para visualizar as curvas de faturamento dos anos passados e o indicador de 500k, realize o upload de um ou mais arquivos de 'Inaugurações' na barra lateral.")



else:

    st.info("Por favor, faça o upload do arquivo Excel principal na barra lateral para começar.")
