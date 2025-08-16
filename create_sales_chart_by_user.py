import streamlit as st
import pandas as pd
import altair as alt
import datetime

def create_sales_chart_by_user(df: pd.DataFrame):
    """
    Cria e retorna um gráfico de linha e pontos com Altair para o 
    percentual de Venda de Itens acumulado (% Venda Itens Acumulado).

    Args:
        df (pd.DataFrame): DataFrame com as colunas exigidas.

    Returns:
        alt.Chart: O gráfico combinado do Altair.
    """
    # Garante que o campo percentual está em formato numérico
    df['% Venda Itens Acumulado'] = pd.to_numeric(df['% Venda Itens Acumulado'], errors='coerce')

    # Obtém valores mínimo e máximo para definir o eixo Y
    min_pct = df['% Venda Itens Acumulado'].min()
    max_pct = df['% Venda Itens Acumulado'].max()

    # Gera ticks de 5 em 5 (ajuste conforme necessário)
    y_ticks = list(range(int(min_pct), int(max_pct) + 5, 5))

    # Gráfico de linha
    line_chart = alt.Chart(df).mark_line().encode(
        x=alt.X(
            'Data:T',
            title=None,
            axis=alt.Axis(format="%d/%m/%Y")
        ),
        y=alt.Y(
            '% Venda Itens Acumulado',
            title='% Venda Itens Acumulado',
            scale=alt.Scale(domain=[min_pct - 2, max_pct + 2]),
            axis=alt.Axis(values=y_ticks)
        ),
        color=alt.Color(
            'Atendente',
            title=None,
            legend=alt.Legend(
                orient="bottom",
                direction="horizontal",
                columns=4
            )
        ),
        tooltip=[
            alt.Tooltip('Data', title='Data', format="%d/%m/%Y"),
            'Atendente',
            alt.Tooltip('% Venda Itens Acumulado:Q', format='.2f')
        ]
    )

    # Gráfico de pontos
    circle_chart = alt.Chart(df).mark_circle(size=60).encode(
        x=alt.X(
            'Data:T',
            title='Data',
            axis=alt.Axis(format="%d/%m/%Y")
        ),
        y=alt.Y(
            '% Venda Itens Acumulado',
            title='% Venda Itens Acumulado',
            scale=alt.Scale(domain=[min_pct - 2, max_pct + 2]),
            axis=alt.Axis(values=y_ticks)
        ),
        color=alt.Color(
            'Atendente',
            title=None,
            legend=alt.Legend(
                orient="bottom",
                direction="horizontal",
                columns=4
            )
        ),
        tooltip=[
            alt.Tooltip('Data', title='Data', format="%d/%m/%Y"),
            'Atendente',
            alt.Tooltip('% Venda Itens Acumulado:Q', format='.2f')
        ]
    )

    # Combina os dois gráficos
    final_chart = alt.layer(line_chart, circle_chart).interactive()

    return final_chart