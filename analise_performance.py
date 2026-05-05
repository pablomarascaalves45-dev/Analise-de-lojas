with tab_expansao:
        st.header("Análise Estratégica para Expansão")
        
        # --- CONTROLES DE PARÂMETROS ---
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            fat_min = st.slider("Faturamento Mínimo Desejado (R$):", 0, 1500000, 500000, step=50000)
        with col_c2:
            dre_min = st.slider("Rentabilidade DRE Mínima (%):", -20.0, 40.0, 0.0, step=0.5) / 100

        # Filtro dinâmico baseado nos sliders
        df_sucesso = df[(df["VENDA MAR'26"] > fat_min) & (df["DRE FEV'26"] > dre_min)].copy()

        if not df_sucesso.empty:
            df_analise = df_sucesso.groupby(["UF", "TAMANHO DA CIDADE"]).agg({
                "VENDA MAR'26": "mean",
                "DRE FEV'26": "mean",
                "LOJAS": "count"
            }).reset_index()

            df_analise.columns = ["Estado", "Porte da Cidade", "Faturamento Médio", "Margem DRE Média", "Qtd Lojas Sucesso"]
            
            # Rótulo customizado: Apenas a Qtd de Lojas em destaque
            df_analise["label_topo"] = df_analise["Qtd Lojas Sucesso"].astype(str) + " Lojas"

            # Gráfico com Eixo Y sendo Faturamento
            fig_exp = px.bar(
                df_analise, 
                x="Estado", 
                y="Faturamento Médio", # Alterado para faturamento no eixo lateral
                color="Porte da Cidade",
                title=f"Performance por Estado (Faturamento Médio)",
                barmode="group",
                text="label_topo", # Texto de amostragem no topo
                labels={"Faturamento Médio": "Faturamento Médio (R$)"}
            )
            
            # Ajuste estético dos rótulos (texto maior e posição)
            fig_exp.update_traces(
                textposition='outside',
                textfont=dict(size=14, color="black") # Texto maior como solicitado
            )
            
            # Formatação do eixo Y para Moeda
            fig_exp.update_layout(yaxis_tickprefix="R$ ", yaxis_tickformat=",.")
            
            st.plotly_chart(fig_exp, use_container_width=True)

            st.subheader("Matriz de Oportunidade por Estado")
            st.dataframe(
                df_analise.sort_values(by=["Estado", "Faturamento Médio"], ascending=[True, False]).style.format({
                    "Faturamento Médio": "R$ {:,.2f}",
                    "Margem DRE Média": "{:.2%}"
                }), 
                use_container_width=True
            )
        else:
            st.error("Não foram encontradas cidades que atendam aos critérios selecionados.")
