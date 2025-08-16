import streamlit as st
import pandas as pd
from psycopg2.extras import RealDictCursor
import datetime

from get_connection import get_connection

def read_sales_items_report_by_user(start_date, end_date):
    """
    Lê os dados de vendas por atendente do banco de dados e retorna um DataFrame.
    Inclui métricas diárias e acumuladas.
    """
    query = """
    SELECT 
        u.name, 
        a.data_venda AS date, 
        a.vendas_totais, 
        a.itens_n_buffet, 
        round( (a.itens_n_buffet::numeric / a.vendas_totais) * 100 , 2 ) AS perc_venda_itens, 
        SUM(a.vendas_totais) OVER (PARTITION BY u.id ORDER BY a.data_venda) AS vendas_totais_acumulado, 
        SUM(a.itens_n_buffet) OVER (PARTITION BY u.id ORDER BY a.data_venda) AS itens_n_buffet_acumulado,
        round( (SUM(a.itens_n_buffet) OVER (PARTITION BY u.id ORDER BY a.data_venda)::numeric / 
        SUM(a.vendas_totais) OVER (PARTITION BY u.id ORDER BY a.data_venda)) * 100 , 2 ) AS perc_venda_itens_acumulado 
    FROM USER_THE_BEST u 
    INNER JOIN ( 
        SELECT  
            DATE(S.CREATED_AT) AS data_venda, 
            COUNT(1) AS vendas_totais, 
            CH.OPENED_BY,  
            MAX(U.NAME) AS nome_usuario, 
            SUM(COALESCE(si.itens_n_buffet, 0)) AS itens_n_buffet
        FROM CASH_HISTORY CH   
        LEFT JOIN USER_THE_BEST U ON U.ID = CH.OPENED_BY  
        INNER JOIN SALES S ON S.CASH_HISTORY_ID = CH.ID  
        LEFT JOIN ( 
            SELECT  
                COUNT(1) AS itens_n_buffet,  
                DATE(SI.CREATED_AT) AS CREATED_AT,  
                si.sale_id AS sale_id  
            FROM sale_items si  
            WHERE si.name <> 'self-service' 
            GROUP BY si.sale_id, DATE(SI.CREATED_AT) 
        ) AS si ON si.sale_id = s.id  
        WHERE 1=1 
            AND CH.STORE_ID = 467 
            AND DATE(S.CREATED_AT) >= %s
            AND DATE(S.CREATED_AT) <= %s
            AND S.ABSTRACT_SALE = FALSE 
            AND S.TYPE = 0  
        GROUP BY CH.OPENED_BY, DATE(S.CREATED_AT) 
    ) AS A ON a.OPENED_BY = u.id 
    WHERE 1=1 
        AND u.name NOT IN ('juliano') 
    ORDER BY a.data_venda DESC, u.id;
    """
    
    # Mapeamento de colunas para nomes mais amigáveis para o Streamlit
    column_rename_map = {
        'name': 'Atendente',
        'date': 'Data',
        'vendas_totais': 'Vendas Totais',
        'itens_n_buffet': 'Itens Não-Buffet',
        'perc_venda_itens': '% Venda Itens',
        'vendas_totais_acumulado': 'Vendas Totais Acumulado',
        'itens_n_buffet_acumulado': 'Itens Não-Buffet Acumulado',
        'perc_venda_itens_acumulado': '% Venda Itens Acumulado'
    }
    
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (start_date, end_date))
            data = cursor.fetchall()
            
            if not data:
                return pd.DataFrame(columns=list(column_rename_map.values()))
            
            df = pd.DataFrame(data)
            df.columns = list(column_rename_map.keys())

            # Converte as colunas de data e renomeia
            df['date'] = pd.to_datetime(df['date'])
            df.rename(columns=column_rename_map, inplace=True)

            if not df.empty:
    # Pegar apenas a última data de cada atendente
                df_total = (
                df.sort_values("Data")  # garante ordem cronológica
                .groupby("Atendente", as_index=False)
                .last()[["Atendente", "% Venda Itens Acumulado"]]
                )

                #print(ultima_data_por_atendente)
            
            return df , df_total
#start_date = datetime.date(2025, 8, 1) # Primeiro dia de agosto de 2025
#end_date = datetime.date(2025, 8, 12)   # Nono dia de agosto de 2025
#data , df_total = read_sales_items_report_by_user(end_date=end_date , start_date=start_date )      
#print (data)  
#print (df_total)  