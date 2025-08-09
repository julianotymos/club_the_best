import streamlit as st
import psycopg2
import pandas as pd
from psycopg2.extras import RealDictCursor
import altair as alt
import datetime
from create_club_chart import create_club_chart , create_ranking_chart
from get_club_data import get_club_data
# Configuração de conexão



# Interface no Streamlit
st.title("📊  Ranking Clube The Best")
#st.markdown("Selecione o intervalo de datas:")
# --- Lógica para definir as datas padrão ---
today = datetime.date.today()
start_of_month = today.replace(day=1)

col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Data inicial", value=start_of_month)
with col2:
    end_date = st.date_input("Data final", value=today)

if start_date and end_date:
    df = get_club_data(start_date, end_date)

    if not df.empty:
        

        st.subheader("Ranking Final por Vendedor")
        ranking_chart = create_ranking_chart(df)
        st.altair_chart(ranking_chart, use_container_width=True)

        #st.subheader("Gráfico - % CPF Clube por Dia")
        #st.line_chart(df.set_index("Data da Venda")["% CPF Clube (Dia)"])

        st.subheader("% CPF Clube (Acumulado) por Periodo")

        final_chart = create_club_chart(df)


        st.altair_chart(final_chart, use_container_width=True)
        

        st.subheader("Dados dia a dia")
        st.dataframe(df)
    else:
        st.warning("Nenhum dado encontrado para o período selecionado.")