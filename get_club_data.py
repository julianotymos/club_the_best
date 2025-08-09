import streamlit as st
import psycopg2
import pandas as pd
from psycopg2.extras import RealDictCursor

@st.cache_resource
def get_connection():
    return psycopg2.connect(
        dbname=st.secrets["dbname"],
        user=st.secrets["user"],
        password=st.secrets["password"],
        host=st.secrets["host"],
        port=st.secrets["port"],
        cursor_factory=RealDictCursor
    )

# Função para buscar dados
def get_club_data(start_date, end_date):
    query = """
    WITH vendas_agrupadas AS (
        SELECT 
            DATE(S.CREATED_AT) AS data_venda,
            CAST(SUM(CASE WHEN S.CPF_USED_CLUB = TRUE THEN 1 ELSE 0 END) AS NUMERIC) AS qty_cpf_club,
            CAST(COUNT(1) AS NUMERIC) AS vendas_totais,
            CH.OPENED_BY,
            MAX(U.NAME) AS nome_usuario
        FROM CASH_HISTORY CH  
        LEFT JOIN USER_THE_BEST U ON U.ID = CH.OPENED_BY 
        INNER JOIN BALANCE_HISTORY BH ON BH.CASH_HISTORY_ID = CH.ID 
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