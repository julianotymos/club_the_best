import pandas as pd
from get_connection import get_connection
import datetime

def read_sale_items_not_buffet(start_date, end_date):
    """
    Busca dados de vendas não-buffet por item e atendente no período informado.
    
    Args:
        start_date (str): Data inicial no formato 'YYYY-MM-DD'.
        end_date (str): Data final no formato 'YYYY-MM-DD'.

    Returns:
        pd.DataFrame: DataFrame com Nome do Item, Atendente e Vendas Totais.
    """
    query = """
        SELECT 
            SI.NAME AS item, 
            MAX(U.NAME) AS atendente,
            COUNT(1) AS vendas_totais
        FROM CASH_HISTORY CH  
        INNER JOIN USER_THE_BEST U ON U.ID = CH.OPENED_BY 
        INNER JOIN SALES S ON S.CASH_HISTORY_ID = CH.ID 
        INNER JOIN SALE_ITEMS SI ON SI.SALE_ID = S.ID 
        WHERE CH.STORE_ID = 467
            AND SI.NAME <> 'self-service'
            AND DATE(S.CREATED_AT) >= %s
            AND DATE(S.CREATED_AT) <= %s
            AND S.ABSTRACT_SALE = FALSE
            AND S.TYPE = 0 
        GROUP BY SI.NAME, U.NAME
    """

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (start_date, end_date))
            data = cursor.fetchall()

            df = pd.DataFrame(data, columns=["item", "atendente", "vendas_totais"])
            df["Vendas Totais"] = pd.to_numeric(df["vendas_totais"], errors="coerce")
            return df


#start_date = datetime.date(2025, 8, 1) # Primeiro dia de agosto de 2025
#end_date = datetime.date(2025, 8, 12)   # Nono dia de agosto de 2025
#data  = read_sale_items_not_buffet(end_date=end_date , start_date=start_date )      
#print(data)