import os
import json
import psycopg2
import time
import traceback
from dotenv import load_dotenv
from multiprocessing import Pool, cpu_count
from datetime import datetime
from Walmart import walmart_parser
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler = logging.FileHandler('walmart_data_pipeline.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


# Load environment variables
load_dotenv('./.env')
db_host ='localhost' #os.getenv('HOST')
db_name = os.getenv('Warehouse_DB_NAME')
db_user = os.getenv('DB_USER')
db_password = os.getenv('PASSWORD')
cache_db_name = os.getenv('DB_NAME')


warehouse_db_config = {
    'host': db_host,
    'dbname': db_name,
    'user': db_user,
    'password': db_password,
    'port': 5432
}

cache_db_config = {
    'host': db_host,
    'dbname': cache_db_name,
    'user': db_user,
    'password': db_password,
    'port': 5555
}

def save_product_data(connection, cursor, data):
    product_data = data['product_info']
    try:
        insert_product_query = """
            INSERT INTO public.walmart_product(
                url, item_id, product_id, manufacture_number, upc, product_name, brand,main_image, images, rating, 
                review_count,categories_path,category_1,category_2,category_3, currency_code, retail_price, msrp_price, discount, in_stock,
                description, specifications, variant_options, current_selection, variants
            )
            VALUES(
                %(url)s,%(item_id)s,%(product_id)s,%(manufacture_number)s,%(upc)s,%(product_name)s,%(brand)s,%(main_image)s,%(images)s,%(rating)s,
                %(review_count)s,%(categories_path)s,%(category_1)s,%(category_2)s,%(category_3)s,%(currency_code)s,%(retail_price)s,%(msrp_price)s,%(discount)s,%(in_stock)s,
                %(description)s,%(specifications)s,%(variant_options)s,%(current_selection)s,%(variants)s
            ) RETURNING id;
        """
        cursor.execute(insert_product_query,  {
            'url': product_data.get('url', ''),
            'item_id': product_data.get('us_item_id', ''),
            'product_id': product_data.get('product_id', ''),
            'manufacture_number': product_data.get('manufacture_number', ''),
            'upc': product_data.get('upc', ''),
            'product_name': product_data.get('title', ''),
            'brand': product_data.get('brand', ''),
            'main_image': product_data.get('images', [])[0],
            'images':' | '.join(product_data.get('images',[])),
            'rating': product_data.get('reviews_results',{}).get('average_rating', 0),
            'review_count': product_data.get('reviews_results', {}).get('total_reviews', 0),
            'categories_path': ' > ' .join([cat['name'] for cat in product_data.get('categories', [])]),
            'category_1': product_data.get('category_1', ''),
            'category_2': product_data.get('category_2', ''),
            'category_3': product_data.get('category_3', ''),
            'currency_code': product_data.get('price_info', {}).get('current_price',{}).get('currencyUnit', ''),
            'retail_price': product_data.get('price_info', {}).get('current_price',{}).get('price', 0.0),
            'msrp_price': product_data.get('price_info', {}).get('was_price', {}).get('price', 0.0),
            'discount': product_data.get('price_info',{}).get('saving_amount')/product_data.get('price_info',{}).get('current_price',{}).get('price',0.0)*100 if product_data.get('price_info',{}).get('current_price',{}).get('price', 0.0) and product_data.get('price_info',{}).get('saving_amount') else 0.0,
            'in_stock': product_data.get('in_stock', False),
            'description': product_data['short_description_text'] +' | '+ product_data['long_description_text'] if product_data.get('short_description_text') and product_data.get('long_description_text') else product_data['short_description_text'] if product_data.get('short_description_text') else product_data['long_description_text'] if product_data.get('long_description_text') else '',
            'specifications': json.dumps(product_data.get('specifications', {})),
            'variant_options': json.dumps(product_data.get('variants_options', {})),
            'current_selection': json.dumps(product_data.get('current_selection', {})),
            'variants': json.dumps(product_data.get('available_variants', {}))
        })
        product_id = cursor.fetchone()[0]

        insert_rawdata_query = """
            INSERT INTO walmart_rawdata (product_id, data)
            VALUES (%s, %s);
            """
        # Step 2: Insert into amazon_rawdata
        cursor.execute(insert_rawdata_query, (product_id, json.dumps(data)))

        connection.commit()
        print("Data inserted successfully into both Walmart_Product and Walmart_rawdata!")

    except psycopg2.OperationalError as e:
        print(f"Operational error during data insert: {e}")
        raise  # Let the caller handle retries
    except Exception as e:
        print(f"Error inserting data: {e}")
        print(traceback.format_exc())
        connection.rollback()

# Retry logic for establishing a connection
def connect_with_retries(db_config,retry_limit=5, retry_delay=5):
    attempt = 0
    while attempt < retry_limit:
        try:
            connection = psycopg2.connect(**db_config)
            print("Database connection established")
            return connection
        except psycopg2.OperationalError as e:
            attempt += 1
            print(f"Database connection failed. Attempt {attempt}/{retry_limit}. Error: {e}")
            if attempt >= retry_limit:
                raise e  # Raise the exception if the retry limit is reached
            time.sleep(retry_delay)



def process_row(connection, cursor,row):
    
    print('Processing row:', row[0])
    try:
        if '"message":""' not in row[1]:
            try:
                print(json.loads(row[1]).keys())
                content = json.loads(row[1])['html']
            except:
                content = row[1]
            data = walmart_parser(row[0], content)
            save_product_data(connection, cursor, data)
        else:
            raise Exception('Invalid URL')
    
        return 1
    
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        
    return {
        'url': row[0],
        'data':row[1],
        'id': row[2]
    }


if __name__ == '__main__':
    
    non_processed_rows = []
    
    batch_size = 1000
    cache_connection = None
    cache_cursor = None

    warehouse_connection = None
    warehouse_cursor = None
    
    batch_no = 1
    try:
        cache_connection = connect_with_retries(cache_db_config)
        cache_cursor = cache_connection.cursor()
        cache_cursor.execute("SELECT COUNT(id) FROM res r where r.url  like '%walmart%'")
        total_rows = cache_cursor.fetchone()[0]
        print(total_rows)

        warehouse_connection = connect_with_retries(warehouse_db_config)
        warehouse_cursor = warehouse_connection.cursor()
        while True:
            cache_cursor.execute("SELECT url, content,id FROM res r WHERE r.url LIKE %s ORDER BY id LIMIT %s",
            ('%walmart%', batch_size))
            rows = cache_cursor.fetchall()

            if len(rows) == 0:
                break

            for row in rows:
                data = process_row(warehouse_connection, warehouse_cursor, row)
                if data == 1:
                    pass
                    # cache_cursor.execute("delete from res where id = %s", (row[2],))
                    # print('Deleted row:', cache_cursor.rowcount)
                    # cache_connection.commit()
                else:
                    non_processed_rows.append(data)
            
            if len(non_processed_rows) >= 500:
                with open(f'./parsed_data/none_processed_{batch_no}.json', 'w') as f:
                    json.dump(non_processed_rows, f,indent=4)

                non_processed_rows = []
                batch_no += 1

            logger.info(f"Processed {batch_size} rows")

    except KeyboardInterrupt:
        print('Interrupted')

    except Exception as e:
        print(e)
        logger.error(traceback.format_exc())

    finally:
        if len(non_processed_rows):
            with open(f'./parsed_data/none_processed_{batch_no}.json', 'w') as f:
                json.dump(non_processed_rows, f,indent=4)

        if cache_connection:
            cache_connection.close()
        if warehouse_connection:
            warehouse_connection.close()
        