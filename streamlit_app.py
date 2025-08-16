import streamlit as st
import pandas as pd
from psycopg2.extras import RealDictCursor
import altair as alt
import datetime
from create_club_chart import create_club_chart, create_ranking_chart
from get_club_data import get_club_data
from read_sales_items_report_by_user import read_sales_items_report_by_user
from create_sales_chart_by_user import create_sales_chart_by_user
from create_sale_items_chart import create_sale_items_chart
from read_sale_items_not_buffet import read_sale_items_not_buffet
# Configuração da página e título
#st.set_page_config(layout="wide")
st.title("📊 Ranking de Vendas e CPF Club")

# --- Lógica para definir as datas padrão ---
today = datetime.date.today()
start_of_month = today.replace(day=1)

col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Data inicial", value=start_of_month)
with col2:
    end_date = st.date_input("Data final", value=today)

# Criação das abas
tab_cpf_club, tab_vendas_atendente = st.tabs(["CPF Club", "Vendas por Atendente"])

with tab_cpf_club:
    if start_date and end_date:
        df = get_club_data(start_date, end_date)

        if not df.empty:
            st.subheader("Ranking Final por Vendedor")
            ranking_chart = create_ranking_chart(df)
            st.altair_chart(ranking_chart, use_container_width=True)

            st.subheader("% CPF Club (Acumulado) por Período")
            final_chart = create_club_chart(df)
            st.altair_chart(final_chart, use_container_width=True)
            
            st.subheader("Dados dia a dia")
            st.data_editor(
                df,
                column_config={
                    "Vendedor": st.column_config.Column(
                        label="Vendedor",
                        disabled=False, 
                        help="Selecione o vendedor para filtrar"
                    )
                },
                hide_index=True,
                disabled=True
            )
        else:
            st.warning("Nenhum dado de CPF Club encontrado para o período selecionado.")

with tab_vendas_atendente:
    if start_date and end_date:
        data, df_total = read_sales_items_report_by_user(start_date, end_date)

        if not data.empty:
            st.subheader("Ranking de Vendas de Itens por Atendente")
            
            
            
                        # Cria a camada de barras
            # Garantir que o campo é numérico e ajustar escala
            df_total['% Venda Itens Acumulado'] = pd.to_numeric(
                df_total['% Venda Itens Acumulado'], errors='coerce'
            ) / 100
            #print(df_total)
            max_val = df_total['% Venda Itens Acumulado'].max()* 1.1 

            base_chart = alt.Chart(df_total).encode(
                y=alt.Y('Atendente', sort='-x', title='Vendedor'),
                x=alt.X(
                    '% Venda Itens Acumulado',
                    scale=alt.Scale(domain=[0, max_val]),  # Sempre de 0 até 100%
                    axis=alt.Axis(format='.2%')
                ),
                tooltip=[
                    'Atendente',
                    alt.Tooltip('% Venda Itens Acumulado:Q', format='.2%', title='Percentual')
                ],
                color=alt.Color('Atendente', legend=None)
            )

            bar_chart = base_chart.mark_bar()

            text_chart = base_chart.mark_text(
                align='left',
                baseline='middle',
                dx=3
            ).encode(
                text=alt.Text('% Venda Itens Acumulado', format='.2%')
            )

            final_chart = (bar_chart + text_chart).interactive()

            st.altair_chart(final_chart, use_container_width=True)

            chart_tt = create_sales_chart_by_user(data)
            st.subheader("% Venda Itens Acumulado por periodo")

            st.altair_chart(chart_tt, use_container_width=True)
            
            st.subheader("Items por periodo")

            df_si =read_sale_items_not_buffet(start_date, end_date)
            chart_si = create_sale_items_chart(df_si)
            st.altair_chart(chart_si, use_container_width=True)

            st.subheader("Dados Detalhados por Atendente")
            st.dataframe(data)
        else:
            st.warning("Nenhum dado de vendas por atendente encontrado para o período selecionado.")