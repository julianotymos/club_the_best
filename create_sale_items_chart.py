import altair as alt
import pandas as pd

def create_sale_items_chart(df: pd.DataFrame):
    """
    Gera um gráfico de barras interativo que exibe vendas por atendente e o total do item.

    Args:
        df (pd.DataFrame): DataFrame com colunas ['item', 'atendente', 'vendas_totais'].
    """
    # 1. Calcula o total de vendas por item
    df_total = df.groupby('item', as_index=False)['vendas_totais'].sum().rename(columns={'vendas_totais': 'total_item'})
    
    # 2. Faz merge para ter a coluna 'total_item' no DataFrame original
    df = df.merge(df_total, on='item', how='left')

    # 3. Seleção interativa pelo atendente
    atendente_select = alt.selection_point(fields=['atendente'], bind='legend')

    # 4. Base cinza com total do item
    base_chart = alt.Chart(df_total).mark_bar(color='lightgray').encode(
        y=alt.Y("item:N", sort='-x', title="Item"),
        x=alt.X("total_item:Q", title="Vendas Totais", sort='-y'),
        tooltip=[
            alt.Tooltip("item", title="Item"),
            alt.Tooltip("total_item:Q", title="Total do Item", format=",")
        ]
    )

    # 5. Barras coloridas por atendente
    selected_chart = alt.Chart(df).mark_bar().encode(
        y=alt.Y("item:N", sort='-x', title=None),
        x=alt.X("vendas_totais:Q", title=None , sort='-y'),
        color=alt.Color("atendente:N", legend=alt.Legend(title="Atendente")),
        opacity=alt.condition(atendente_select, alt.value(1), alt.value(0.2)),
        tooltip=[
            alt.Tooltip("item", title="Item"),
            alt.Tooltip("atendente", title="Atendente"),
            alt.Tooltip("vendas_totais:Q", title="Vendas do Atendente", format=","),
            alt.Tooltip("total_item:Q", title="Total do Item", format=",")
        ]
    ).add_params(atendente_select)

    # 6. Gráfico final
    final_chart = (base_chart + selected_chart).properties(
        title="Vendas de Itens por Atendente"
    ).interactive()

    return final_chart
