import altair as alt
import pandas as pd

def create_club_chart(df: pd.DataFrame):
    """
    Cria e retorna um gráfico de linha e pontos com Altair para a taxa de CPF Clube acumulada.

    Args:
        df (pd.DataFrame): DataFrame com os dados de vendas, já processado e renomeado.

    Returns:
        alt.Chart: O gráfico combinado do Altair.
    """
    # Obtém os valores mínimo e máximo do percentual para definir o domínio do eixo Y
    min_pct = df['% CPF Clube (Acumulado)'].min()
    max_pct = df['% CPF Clube (Acumulado)'].max()

    # Adiciona o valor máximo à lista de ticks que o Altair irá exibir
    # Criamos uma lista de ticks para ser mais explícito
    # Aumentamos o valor máximo um pouco para garantir que ele seja exibido
    y_ticks = list(range(int(min_pct), int(max_pct) + 5, 5)) # Exemplo: [50, 55, 60]

    # Cria o gráfico de linhas com Altair
    line_chart = alt.Chart(df).mark_line().encode(
        x=alt.X(
            'Data da Venda:T',
            title='Data da Venda',
            axis=alt.Axis(format="%d/%m/%Y")
        ),
        y=alt.Y(
            '% CPF Clube (Acumulado)',
            title='% CPF Clube (Acumulado)',
            scale=alt.Scale(domain=[min_pct - 2, max_pct + 2]), # Adiciona uma margem
            axis=alt.Axis(values=y_ticks) # Define os ticks manualmente
        ),
        color=alt.Color('Vendedor', title='Vendedor'),
        tooltip=[
            alt.Tooltip('Data da Venda', title='Data da Venda', format="%d/%m/%Y"),
            'Vendedor',
            '% CPF Clube (Acumulado)'
        ]
    )

    # Adiciona as bolinhas nos pontos de dados
    circle_chart = alt.Chart(df).mark_circle(size=60).encode(
        x=alt.X(
            'Data da Venda:T',
            title='Data da Venda',
            axis=alt.Axis(format="%d/%m/%Y")
        ),
        y=alt.Y(
            '% CPF Clube (Acumulado)',
            title='% CPF Clube (Acumulado)',
            scale=alt.Scale(domain=[min_pct - 2, max_pct + 2]),
            axis=alt.Axis(values=y_ticks)
        ),
        color=alt.Color('Vendedor', title='Vendedor'),
        tooltip=[
            alt.Tooltip('Data da Venda', title='Data da Venda', format="%d/%m/%Y"),
            'Vendedor',
            '% CPF Clube (Acumulado)'
        ]
    )

    # Combina os dois gráficos (linhas e círculos)
    final_chart = alt.layer(line_chart, circle_chart).interactive()

    return final_chart


def create_ranking_chart(df: pd.DataFrame):
    """
    Cria e retorna um gráfico de ranking com Altair para a taxa de CPF Clube acumulada final.

    Args:
        df (pd.DataFrame): DataFrame com os dados de vendas, já processado e renomeado.

    Returns:
        alt.Chart: O gráfico combinado de ranking do Altair.
    """
    # 1. Processar os dados: Encontrar a última entrada (maior data) para cada vendedor
    df_ranking = df.loc[df.groupby('Vendedor')['Data da Venda'].idxmax()]

    # 2. Criar o gráfico de barras para o ranking
    base_chart = alt.Chart(df_ranking).encode(
        # Ordena os vendedores pelo percentual de forma descendente (ranking)
        y=alt.Y('Vendedor', sort='-x', title='Vendedor'),
        x=alt.X('% CPF Clube (Acumulado)', title='% CPF Clube (Acumulado) '),
        tooltip=[
            'Vendedor',
            alt.Tooltip('% CPF Clube (Acumulado)', format='.2f', title='Percentual')
        ],
        color=alt.Color('Vendedor', legend=None) # A cor ajuda a identificar o vendedor
    )

    # Cria a camada de barras
    bar_chart = base_chart.mark_bar()

    # Adiciona a camada de texto para mostrar o valor exato em cima de cada barra
    text_chart = base_chart.mark_text(
        align='left',
        baseline='middle',
        dx=3  # Desloca o texto para a direita da barra
    ).encode(
        text=alt.Text('% CPF Clube (Acumulado)', format='.2f')
    )

    # Combina o gráfico de barras e a camada de texto
    final_chart = (bar_chart + text_chart).interactive()

    return final_chart