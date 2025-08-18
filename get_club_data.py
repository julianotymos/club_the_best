import streamlit as st
import psycopg2
import pandas as pd
from psycopg2.extras import RealDictCursor
import datetime 
from get_connection import get_connection


# Função para buscar dados
def get_club_data(start_date, end_date):
    query = """
    WITH vendas_agrupadas AS (
        SELECT 
            DATE(S.CREATED_AT) AS data_venda,
            ---CAST(SUM(CASE WHEN S.CPF_USED_CLUB = TRUE THEN 1 ELSE 0 END) AS NUMERIC) AS qty_cpf_club,
            CAST(SUM(CASE WHEN COALESCE(S.client_cpf, '') <> '' THEN 1 ELSE 0 END) AS NUMERIC) AS qty_cpf_club,

            CAST(COUNT(1) AS NUMERIC) AS vendas_totais,
            CH.OPENED_BY,
            MAX(U.NAME) AS nome_usuario
        FROM CASH_HISTORY CH  
        LEFT JOIN USER_THE_BEST U ON U.ID = CH.OPENED_BY 
        INNER JOIN SALES S ON S.CASH_HISTORY_ID = CH.ID 
        WHERE CH.STORE_ID = 467
            AND DATE(S.CREATED_AT) >= %s
            AND DATE(S.CREATED_AT) <= %s
            AND S.TYPE = 0
            AND U.NAME NOT IN ('juliano')
            AND S.abstract_sale = false
        GROUP BY CH.OPENED_BY, DATE(S.CREATED_AT)
    )
    SELECT 
        data_venda,
        nome_usuario,
        qty_cpf_club, 
        vendas_totais,
        ROUND((qty_cpf_club / vendas_totais) * 100, 2) AS pct_cpf_club,
        COALESCE(SUM(qty_cpf_club) OVER (PARTITION BY OPENED_BY ORDER BY data_venda ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS qty_cpf_club_acumulado,
        COALESCE(SUM(vendas_totais) OVER (PARTITION BY OPENED_BY ORDER BY data_venda ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS vendas_totais_acumulado,
        ROUND(
            (COALESCE(SUM(qty_cpf_club) OVER (PARTITION BY OPENED_BY ORDER BY data_venda ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) 
            / NULLIF(COALESCE(SUM(vendas_totais) OVER (PARTITION BY OPENED_BY ORDER BY data_venda ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0), 0)) * 100, 
            2
        ) AS pct_cpf_club_acumulado
    FROM vendas_agrupadas
    ORDER BY data_venda DESC , nome_usuario ASC;
    """

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (start_date, end_date))
            data = cursor.fetchall()
            df = pd.DataFrame(data)
            if not df.empty:
                df['pct_cpf_club'] = pd.to_numeric(df['pct_cpf_club'], errors='coerce')
                df['pct_cpf_club_acumulado'] = pd.to_numeric(df['pct_cpf_club_acumulado'], errors='coerce')
                df['qty_cpf_club'] = pd.to_numeric(df['qty_cpf_club'], errors='coerce')
                df['vendas_totais'] = pd.to_numeric(df['vendas_totais'], errors='coerce')
                df['vendas_totais_acumulado'] = pd.to_numeric(df['vendas_totais_acumulado'], errors='coerce')
                df['qty_cpf_club_acumulado'] = pd.to_numeric(df['qty_cpf_club_acumulado'], errors='coerce')

                # 1. Renomeia as colunas
                column_mapping = {
                    'data_venda': 'Data da Venda',
                    'nome_usuario': 'Vendedor',
                    'qty_cpf_club': 'Qtd. CPF Clube (Dia)',
                    'vendas_totais': 'Vendas Totais (Dia)',
                    'pct_cpf_club': '% CPF Clube (Dia)',
                    'qty_cpf_club_acumulado': 'Qtd. CPF Clube (Acumulado)',
                    'vendas_totais_acumulado': 'Vendas Totais (Acumulado)',
                    'pct_cpf_club_acumulado': '% CPF Clube (Acumulado)',
                }
                df = df.rename(columns=column_mapping)
                
                # 2. Formata os percentuais para usar vírgula e os converte para string
                #df['% CPF Clube (Dia)'] = df['% CPF Clube (Dia)'].apply(lambda x: f'{x:.2f}'.replace('.', ','))
                #df['% CPF Clube (Acumulado)'] = df['% CPF Clube (Acumulado)'].apply(lambda x: f'{x:.2f}'.replace('.', ','))
            return df
        
import pandas as pd

def generate_weekly_df(df_daily: pd.DataFrame) -> pd.DataFrame:
    """
    Agrupa os dados diários em uma base semanal, calculando a soma das vendas
    e a porcentagem de vendas com CPF do clube.

    Args:
        df_daily (pd.DataFrame): O DataFrame diário retornado pela função get_club_data.

    Returns:
        pd.DataFrame: Um novo DataFrame agrupado por semana e atendente.
    """
    if df_daily.empty:
        return pd.DataFrame()

    # Garantir que a coluna de data esteja em formato datetime
    df_daily['Data da Venda'] = pd.to_datetime(df_daily['Data da Venda'])

    # Criar colunas auxiliares para início e fim da semana
    df_daily['Início da Semana (Segunda-feira)'] = df_daily['Data da Venda'] - pd.to_timedelta(df_daily['Data da Venda'].dt.weekday, unit='d')
    df_daily['Último Dia da Semana (Domingo)'] = df_daily['Início da Semana (Segunda-feira)'] + pd.Timedelta(days=6)

    # Agrupar por atendente e intervalo da semana
    df_weekly = df_daily.groupby(
        ['Vendedor', 'Início da Semana (Segunda-feira)', 'Último Dia da Semana (Domingo)'],
        as_index=False
    ).agg(
        Vendas_Totais_Semana=('Vendas Totais (Dia)', 'sum'),
        Qtd_CPF_Clube_Semana=('Qtd. CPF Clube (Dia)', 'sum')
    )

    # Calcular a porcentagem semanal
    df_weekly['% CPF Clube (Semana)'] = round(
        (df_weekly['Qtd_CPF_Clube_Semana'] / df_weekly['Vendas_Totais_Semana']) * 100, 2
    )

    # Converter colunas de datas para formato apenas de data
    df_weekly['Início da Semana (Segunda-feira)'] = df_weekly['Início da Semana (Segunda-feira)'].dt.date
    df_weekly['Último Dia da Semana (Domingo)'] = df_weekly['Último Dia da Semana (Domingo)'].dt.date

    # Reordenar as colunas
    new_column_order = [
        'Início da Semana (Segunda-feira)',
        'Último Dia da Semana (Domingo)',
        'Vendedor',
        'Vendas_Totais_Semana',
        'Qtd_CPF_Clube_Semana',
        '% CPF Clube (Semana)'
    ]
    df_weekly = df_weekly[new_column_order]

    return df_weekly

def generate_total_weekly_df(df_weekly):
    """
    Consolida o DataFrame semanal por vendedor em um DataFrame com os totais da loja por semana.

    Args:
        df_weekly (pd.DataFrame): O DataFrame semanal por vendedor retornado pela função generate_weekly_df.

    Returns:
        pd.DataFrame: Um novo DataFrame com os totais da loja por semana.
    """
    if df_weekly.empty:
        return pd.DataFrame()

    # Agrupar por semana (sem considerar vendedor) e somar as colunas de vendas
    df_total = df_weekly.groupby(
        ['Início da Semana (Segunda-feira)', 'Último Dia da Semana (Domingo)'],
        as_index=False
    ).agg(
        Vendas_Totais_Semana=('Vendas_Totais_Semana', 'sum'),
        Qtd_CPF_Clube_Semana=('Qtd_CPF_Clube_Semana', 'sum')
    )

    # Calcular a porcentagem de CPF Clube para o total da loja
    df_total['% CPF Clube (Semana)'] = round(
        (df_total['Qtd_CPF_Clube_Semana'] / df_total['Vendas_Totais_Semana']) * 100, 2
    )

    # Converter colunas de datas para formato apenas de data (garantia)
    df_total['Início da Semana (Segunda-feira)'] = pd.to_datetime(df_total['Início da Semana (Segunda-feira)']).dt.date
    df_total['Último Dia da Semana (Domingo)'] = pd.to_datetime(df_total['Último Dia da Semana (Domingo)']).dt.date

    # Reordenar as colunas para consistência
    df_total = df_total[
        ['Início da Semana (Segunda-feira)', 'Último Dia da Semana (Domingo)',
         'Vendas_Totais_Semana', 'Qtd_CPF_Clube_Semana', '% CPF Clube (Semana)']
    ]

    return df_total

#start_date = datetime.date(2025, 7, 21) # Primeiro dia de agosto de 2025
#end_date = datetime.date(2025, 7, 27)   # Nono dia de agosto de 2025

#df = get_club_data(start_date=start_date ,end_date=end_date)
#df2 = generate_weekly_df(df)
#print(df2)
#df3 = generate_total_weekly_df(df2)
#print(df3)