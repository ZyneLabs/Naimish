
import psycopg2
import os
from dotenv import load_dotenv
from multiprocessing import Pool,cpu_count
import json
from Amazon import amazon_parser,get_domain_name,get_asin
from Amazon_offer import get_offer_info
import traceback

load_dotenv('./.env')
db_host = os.getenv('HOST')
db_name = os.getenv('DB_NAME')
db_user = os.getenv('USER')
db_password = os.getenv('PASSWORD')
db_port = os.getenv('PORT')

def get_db_connection():
    connection = psycopg2.connect(
        host=db_host,
        dbname=db_name,
        user=db_user,
        password=db_password,
        port = db_port
    )

    return connection

def process_row(row):
    
    print('Processing row:', row[0])
    try:
        if '"message":""' not in row[1] and 'https://www.amazon.com/gp/product/ajax/' not in row[0]:
            domain = get_domain_name(row[0])
            asin = get_asin(row[0])
            data = amazon_parser(row[0],domain,row[1],asin)
            return {
                'url': row[0],
                'data': data,
                'id': row[2]}
        elif 'https://www.amazon.com/gp/product/ajax/' in row[0]:
            data = get_offer_info(row[1])
            return {
                'url': row[0],
                'data': data,
                'id': row[2]}
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        
    return {
        'url': row[0],
        'data':row[1],
        'id': row[2]
    }
if __name__ == '__main__':
    connection = get_db_connection()
    cursor = connection.cursor()
    batch_size = 1000
    parser_data = []
    start_offset = 121000
    print(cpu_count())
    try:
        cursor.execute("SELECT COUNT(id) FROM res r where r.url  like '%amazon%'")
        total_rows = cursor.fetchone()[0]
        print(total_rows)
        for offset in range(start_offset, total_rows, batch_size):
            cursor.execute("SELECT url, content,id FROM res r WHERE r.url LIKE %s ORDER BY id LIMIT %s OFFSET %s",
            ('%amazon%', batch_size, offset))
            rows = cursor.fetchall()
            for row in rows:
                parser_data.append(process_row(row))
            
            if len(parser_data) >= 1000:
                with open(f'./parsed_data/{start_offset}-{offset + batch_size}.json', 'w') as f:
                    json.dump(parser_data, f,indent=4)

                # for row in parser_data:
                #     cursor.execute("delete from res where id = %s", (True, row['id']))

                #     print('Deleted row:', cursor.rowcount)
                # connection.commit()
                parser_data = []
                start_offset = offset+batch_size

            print(f"Processed {offset}-{offset + batch_size} rows")
    except KeyboardInterrupt:
        print('Interrupted')

    except Exception as e:
        print(e)
        print("Unexpected error:")
        print(traceback.format_exc())
    
    finally:
        # with open(f'./parsed_data/{start_offset}-{offset}.json', 'w') as f:
        #     json.dump(parser_data, f)
       
        with open(f'./parsed_data/{start_offset}-{offset}.txt', 'w') as f:
            f.write(str(parser_data))

        cursor.close()
        connection.close()