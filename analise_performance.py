import pandas as pd
import plotly.express as px
import streamlit as st
from datetime import datetime

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Analytics Expansão - DNA de Sucesso", layout="wide")

st.title("🎯 Inteligência de Performance: DNA de Sucesso")
st.markdown("---")

# 2. UPLOAD E TRATAMENTO DE DADOS
uploaded_file = st.file_uploader("📂 Suba a base de dados das lojas (Excel)", type=['xlsx'])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df.columns = [str(c).strip() for c in df.columns]
    
    # --- MAPEAMENTO DINÂMICO DE COLUNAS ---
    def localizar_coluna(lista_termos, nome_padrao):
        for col in df.columns:
            if any(termo.upper() in col.upper() for termo in lista_termos):
                return col
        return nome_padrao

    col_id = localizar_coluna(["ID_LOJA", "COD_LOJA", "ID"], "ID_LOJA")
    col_loja = localizar_coluna(["LOJAS", "NOME DA LOJA", "NOME_LOJA"], "LOJAS")
    col_fat = localizar_coluna(["FATURAMENTO", "MAR'25", "MÉDIA FATURAMENTO", "SOMA DAS VENDAS"], "MÉDIA FATURAMENTO")
    col_dre = localizar_coluna(["DRE_AC", "FEV/26", "DRE FEV", "DRE ACUMULADO"], "DRE_AC FEV/26")
    col_uf = localizar_coluna(["UF", "ESTADO"], "UF")
    col_porte = localizar_coluna(["TAMANHO DA CIDADE", "PORTE", "TAMANHO"], "TAMANHO DA CIDADE")
    col_posicao = localizar_coluna(["POSIÇÃO", "POSICAO"], "POSIÇÃO DA LOJA")
    col_estacionamento = localizar_coluna(["ESTACIONAMENTO"], "ESTACIONAMENTO")
    col_abertura = localizar_coluna(["DATA DE ABERTURA", "ABERTURA"], "DATA DE ABERTURA")
    col_localizacao = localizar_coluna(["BAIRRO OU CENTRO", "LOCALIZACAO", "CENTRO"], "BAIRRO OU CENTRO")
    col_demanda = localizar_coluna(["DEMANDA FSJ", "DEMANDA"], "DEMANDA FSJ RAIO DE 1 KM")
    col_populacao = localizar_coluna(["POPULAÇÃO RAIO", "POPULACAO"], "POPULAÇÃO RAIO DE 1KM")

    # --- TRATAMENTO DE VARIÁVEIS ---
    for c in [col_demanda, col_populacao]:
        if c in df.columns:
            df[c] = df[c].astype(str).str.replace(r'[R$\.\s]', '', regex=True).str.replace(',', '.')
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

    if col_localizacao in df.columns:
        df[col_localizacao] = df[col_localizacao].astype(str).str.upper().str.strip()
        df[col_localizacao] = df[col_localizacao].apply(lambda x: "CENTRO" if "CENTRO" in x else "BAIRRO")

    if col_abertura in df.columns:
        df[col_abertura] = pd.to_datetime(df[col_abertura], errors='coerce')
        hoje = datetime.now()
        df['IDADE_LOJA'] = df[col_abertura].apply(lambda x: hoje.year - x.year if pd.notnull(x) else 0)
        df['FAIXA_IDADE'] = df['IDADE_LOJA'].apply(lambda x: f"{x} anos")

    # --- FILTROS (SIDEBAR) ---
    st.sidebar.header("⚙️ Filtros")
    ufs = sorted(df[col_uf].dropna().unique().tolist())
    opcao_uf = st.sidebar.selectbox("Estado:", ["Todos os Estados"] + ufs)
    df_filtrado_uf = df.copy() if opcao_uf == "Todos os Estados" else df[df[col_uf] == opcao_uf].copy()

    df_filtrado_uf[col_fat] = pd.to_numeric(df_filtrado_uf[col_fat], errors='coerce').fillna(0)
    df_filtrado_uf[col_dre] = pd.to_numeric(df_filtrado_uf[col_dre], errors='coerce').fillna(0)
    
    fat_min, fat_max = float(df_filtrado_uf[col_fat].min()), float(df_filtrado_uf[col_fat].max())
    faixa_fat = st.sidebar.slider("Faixa de Faturamento:", fat_min, fat_max, (fat_min, fat_max), format="R$ {:,.0f}")
    
    st.sidebar.write(f"📊 **Selecionado:** R$ {faixa_fat[0]:,.0f} a R$ {faixa_fat[1]:,.0f}")
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("📌 Critérios de Performance")
    st.sidebar.markdown("""
    * **🔵 Alta:** Fat. ≥ R$ 1.000.000
    * **💎 Boa:** Fat. ≥ R$ 400.000 e DRE Positivo
    * **🟠 Alto Custo:** Fat. ≥ R$ 400.000 e DRE Negativo
    * **🟡 Baixa:** Fat. < R$ 400.000 e DRE Positivo
    * **🔴 Ruim:** Fat. < R$ 400.000 e DRE Negativo
    """)

    df_view = df_filtrado_uf[
        (df_filtrado_uf[col_fat] >= faixa_fat[0]) & (df_filtrado_uf[col_fat] <= faixa_fat[1])
    ].copy()

    # --- LÓGICA DE PERFORMANCE AJUSTADA ---
    def classificar(row):
        f = row[col_fat]
        d = row[col_dre]
        if f >= 1000000: 
            return '🔵 Alta'
        elif f >= 400000:
            return '💎 Boa' if d >= 0 else '🟠 Alto Custo'
        else:
            return '🟡 Baixa' if d >= 0 else '🔴 Ruim'

    df_view['Performance_Base'] = df_view.apply(classificar, axis=1)
    contagem_perf = df_view['Performance_Base'].value_counts()
    
    def formatar_legenda(perf_base):
        qtd = contagem_perf.get(perf_base, 0)
        return f"{perf_base} = {qtd} lojas"

    df_view['Performance'] = df_view['Performance_Base'].apply(formatar_legenda)
    ordem_base = ['🔵 Alta', '💎 Boa', '🟠 Alto Custo', '🟡 Baixa', '🔴 Ruim']
    ordem_legenda = [formatar_legenda(p) for p in ordem_base if p in df_view['Performance_Base'].values]

    cores_map = {
        formatar_legenda('🔵 Alta'): '#0000FF',
        formatar_legenda('💎 Boa'): '#27ae60',
        formatar_legenda('🟠 Alto Custo'): '#e67e22',
        formatar_legenda('🟡 Baixa'): '#f1c40f',
        formatar_legenda('🔴 Ruim'): '#e74c3c'
    }

    # --- ABAS ---
    tab_geo, tab_dna, tab_listagem, tab_analise = st.tabs(["🌎 Visão Geográfica", "🧬 DNA do Sucesso", "📋 Detalhes", "🧠 Análise Estratégica"])

    with tab_geo:
        st.subheader(f"Resumo de Performance - {opcao_uf}")
        k1, k2, k3 = st.columns(3)
        k1.metric("Total Lojas", len(df_view))
        k2.metric("Lojas 'Vão Bem' (Boa/Alta)", len(df_view[df_view['Performance_Base'].isin(['🔵 Alta', '💎 Boa'])]))
        dre_medio = df_view[col_dre].mean()
        k3.metric("DRE Médio", f"{dre_medio*100:.2f}%")

        fig_scat = px.scatter(df_view, x=col_fat, y=col_dre, color="Performance", 
                             hover_name=col_loja,
                             category_orders={"Performance": ordem_legenda},
                             color_discrete_map=cores_map, height=500)
        fig_scat.add_hline(y=0, line_dash="dash", line_color="red")
        st.plotly_chart(fig_scat, use_container_width=True)

    with tab_dna:
        st.subheader("🧬 Análise de Variáveis de Sucesso")
        opcoes_dna = [c for c in [col_localizacao, 'FAIXA_IDADE', col_porte, col_posicao, col_estacionamento] if c in df_view.columns]
        analise_alvo = st.selectbox("Escolha a variável para análise de DNA:", opcoes_dna)
        
        if not df_view.empty and analise_alvo:
            temp_df = df_view.copy()
            stats = temp_df.groupby([analise_alvo, 'Performance', 'Performance_Base']).agg({
                col_loja: lambda x: "<br>".join(list(x)[:15]) + ("<br>..." if len(x) > 15 else ""),
                col_id: 'count'
            }).reset_index()
            stats.rename(columns={col_id: 'contagem', col_loja: 'lista_lojas'}, inplace=True)

            fig_dna = px.bar(stats, x=analise_alvo, y='contagem', color='Performance',
                             barmode='group', text='contagem',
                             category_orders={"Performance": ordem_legenda},
                             color_discrete_map=cores_map, height=500)
            st.plotly_chart(fig_dna, use_container_width=True)

            st.markdown("---")
            st.subheader("📊 Onde estão as lojas que 'Vão Bem'?")
            
            if col_localizacao in df_view.columns and col_porte in df_view.columns:
                df_deep = df_view.groupby([col_porte, col_localizacao, 'Performance']).size().reset_index(name='qtd')
                
                fig_deep = px.bar(
                    df_deep,
                    x=col_porte,
                    y='qtd',
                    color='Performance',
                    facet_col=col_localizacao,
                    barmode='group',
                    text='qtd',
                    category_orders={
                        "Performance": ordem_legenda,
                        col_localizacao: ["BAIRRO", "CENTRO"]
                    },
                    color_discrete_map=cores_map,
                    height=600
                )
                fig_deep.update_traces(textposition='outside')
                fig_deep.update_layout(xaxis_title="Tamanho da Cidade", yaxis_title="Qtd de Lojas", margin=dict(t=50))
                fig_deep.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
                st.plotly_chart(fig_deep, use_container_width=True)

    with tab_listagem:
        st.subheader("📋 Detalhamento das Lojas")
        cols_final = [col_id, col_loja, col_uf, 'IDADE_LOJA', col_localizacao, col_porte, col_fat, col_dre, 'Performance_Base']
        df_tabela = df_view[[c for c in cols_final if c in df_view.columns]].copy()
        df_tabela = df_tabela.sort_values(by=col_fat, ascending=False)
        
        st.dataframe(
            df_tabela.style.format({
                col_fat: "R$ {:,.2f}",
                col_dre: "{:.2%}",
                'IDADE_LOJA': "{:.0f} anos"
            }), 
            use_container_width=True,
            hide_index=True
        )

    with tab_analise:
        st.subheader("🧠 Relatório de Inteligência: O Perfil das Lojas +1MM")
        
        df_alta = df_view[df_view['Performance_Base'] == '🔵 Alta']
        
        if len(df_alta) > 0:
            c1, c2 = st.columns([1, 1])
            
            with c1:
                st.info(f"### 🎯 Fortalezas Identificadas ({len(df_alta)} lojas)")
                
                # Análise de Localização
                loc_pref = df_alta[col_localizacao].mode()[0] if col_localizacao in df_alta.columns else "N/A"
                st.write(f"**📍 Localização Dominante:** Lojas de alta performance estão majoritariamente em **{loc_pref}**.")
                
                # Análise de Porte de Cidade
                porte_pref = df_alta[col_porte].mode()[0] if col_porte in df_alta.columns else "N/A"
                st.write(f"**🏙️ Ambiente Ideal:** O porte de cidade mais comum para este faturamento é **{porte_pref}**.")
                
                # Análise de Estacionamento
                if col_estacionamento in df_alta.columns:
                    est_pref = df_alta[col_estacionamento].mode()[0]
                    st.write(f"**🚗 Infraestrutura:** O padrão de estacionamento recorrente é **{est_pref}**.")

                # Idade Média
                idade_media = df_alta['IDADE_LOJA'].mean()
                st.write(f"**⏳ Maturação:** A média de idade dessas lojas é de **{idade_media:.1f} anos**.")

            with c2:
                st.success("### 🚀 O que uma loja > 1MM precisa ter?")
                st.markdown(f"""
                Baseado nos dados reais das suas **{len(df_alta)} melhores unidades**, o "DNA" do sucesso exige:
                
                1.  **Foco em {loc_pref}:** Este ambiente concentra o maior volume de vendas.
                2.  **Presença em cidades {porte_pref}:** Onde a densidade demográfica sustenta o ticket médio.
                3.  **Eficiência de Margem:** O DRE médio deste grupo é de **{df_alta[col_dre].mean()*100:.1f}%**, garantindo que o faturamento vire lucro.
                4.  **Consolidação:** Lojas que atingem este patamar geralmente possuem mais de **{int(idade_media)} anos** de operação.
                """)
                
            st.markdown("---")
            st.subheader("📊 Comparativo Visual: Alta Performance vs Restante")
            
            # Gráfico de comparação de Médias
            comp_data = {
                'Métrica': ['DRE Médio', 'Demanda FSJ (Média)', 'População 1km (Média)'],
                'Lojas +1MM': [
                    df_alta[col_dre].mean(), 
                    df_alta[col_demanda].mean(), 
                    df_alta[col_populacao].mean()
                ],
                'Outras Lojas': [
                    df_view[df_view['Performance_Base'] != '🔵 Alta'][col_dre].mean(),
                    df_view[df_view['Performance_Base'] != '🔵 Alta'][col_demanda].mean(),
                    df_view[df_view['Performance_Base'] != '🔵 Alta'][col_populacao].mean()
                ]
            }
            df_comp = pd.DataFrame(comp_data)
            st.table(df_comp.set_index('Métrica'))
        else:
            st.warning("⚠️ Não há lojas com faturamento acima de R$ 1.000.000 na seleção atual para gerar o relatório.")

else:
    st.info("👋 Por favor, carregue o arquivo Excel para iniciar a análise.")
