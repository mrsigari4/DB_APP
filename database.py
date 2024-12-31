import pymssql

def query_to_db(CONN, QUERY) -> str:
    try:
        cursor = CONN.cursor()
        cursor.execute(QUERY)

        CONN.commit()

        results = cursor.fetchall() if cursor.description else None
        print(results)
        if results is None:
            cursor.close()
            return 'NO RESULTS'

        if results:
            results_keys = results[0].keys()
            keys = list(results_keys)
            return {'results': results, 'keys': keys}
            
        else:
            return 'NO RESULTS'
    except Exception as e:

        CONN.rollback()
        return f'Error executing query: {str(e)}'
    finally:
        cursor.close()


def connect_to_db(SERVER, DATABASE, USER, PASSWORD) -> object:
    try:
        print("Server name = " + SERVER)
        conn = pymssql.connect(
            server=SERVER,
            user=USER,
            password=PASSWORD,
            database=DATABASE,
            charset = 'UTF-8',
            as_dict=True,
        )
    except Exception as e:
        print(e)
        return None
        raise
    return conn
