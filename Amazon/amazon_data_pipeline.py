import os
import json
import psycopg2
import time
import traceback
from dotenv import load_dotenv
from multiprocessing import Pool, cpu_count
from datetime import datetime
from Amazon import amazon_parser,get_domain_name,get_asin
from Amazon_offer import get_offer_info
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler = logging.FileHandler('amazon_data_pipeline.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


# Load environment variables
load_dotenv('./.env')
db_host ='localhost' #os.getenv('HOST')
db_name = os.getenv('Warehouse_DB_NAME')
db_user = 'dhruvish'
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

def save_product_data(connection, cursor, product_data):
    try:
        insert_product_query = """
            INSERT INTO public.amazon_product(
                url, asin, product_name, brand, main_image, images, rating, 
                review_count, currency_code, retail_price, msrp_price, discount, 
                in_stock, in_stock_text, description, climate_pledge_friendly, 
                rating_breakdown, categories_path, variant_values, current_selection, 
                attributes, specifications, is_bundle, feature_bullets, is_prime, 
                is_new, review_summary, "timestamp"
            )
            VALUES(
                %(url)s, %(asin)s, %(product_name)s, %(brand)s, %(main_image)s, 
                %(images)s, %(rating)s, %(review_count)s, %(currency_code)s, 
                %(retail_price)s, %(msrp_price)s, %(discount)s, %(in_stock)s, 
                %(in_stock_text)s, %(description)s, %(climate_pledge_friendly)s, 
                %(rating_breakdown)s, %(categories_path)s, %(variant_values)s, 
                %(current_selection)s, %(attributes)s, %(specifications)s, 
                %(is_bundle)s, %(feature_bullets)s, %(is_prime)s, %(is_new)s, 
                %(review_summary)s, %(timestamp)s
            ) RETURNING id;
        """
        cursor.execute(insert_product_query,  {
            'url': product_data.get('url', ''),
            'asin': product_data.get('asin', ''),
            'product_name': product_data.get('product_name', ''),
            'brand': product_data.get('brand', ''),
            'main_image': product_data.get('main_image', ''),
            'images': product_data.get('images_flat', ''),
            'rating': product_data.get('rating', 0),
            'review_count': product_data.get('total_ratings', 0),
            'currency_code': product_data.get('currency_code', ''),
            'retail_price': float(product_data.get('promo_price').replace('$','').replace(',','')) if product_data.get('promo_price',0) else  float(product_data.get('list_price', '0').replace('$','').replace(',','')),
            'msrp_price': float(product_data.get('list_price', 0).replace('$','').replace(',','')) if product_data.get('promo_price',0) else 0,
            'discount': float(product_data.get('discount_percentage', 0)) if isinstance(product_data.get('discount_percentage', 0), int) else float(product_data.get('discount_percentage', 0).replace('%','')),
            'in_stock': product_data.get('in_stock', False),
            'in_stock_text': product_data.get('in_stock_text', ''),
            'description': product_data.get('description', ''),
            'climate_pledge_friendly': product_data.get('climate_pledge_friendly', False),
            'rating_breakdown': json.dumps(product_data.get('rating_breakdown', {})),
            'categories_path': product_data.get('categories_flat', ''),
            'variant_values': json.dumps(product_data.get('variant_values', {})),
            'current_selection': product_data.get('current_selection', ''),
            'attributes': json.dumps(product_data.get('attributes', {})),
            'specifications': json.dumps(product_data.get('specifications', {})),
            'is_bundle': product_data.get('is_bundle', False),
            'feature_bullets': product_data.get('feature_bullets', ''),
            'is_prime': product_data.get('is_prime', False),
            'is_new': product_data.get('is_new', False),
            'review_summary': product_data.get('review_summary', ''),
            'timestamp': product_data.get('timestamp', datetime.now())
        })
        product_id = cursor.fetchone()[0]

        insert_rawdata_query = """
            INSERT INTO amazon_rawdata (product_id, data)
            VALUES (%s, %s);
            """
        # Step 2: Insert into amazon_rawdata
        cursor.execute(insert_rawdata_query, (product_id, json.dumps(product_data)))

        connection.commit()
        print("Data inserted successfully into both Amazon_Product and amazon_rawdata!")

    except psycopg2.OperationalError as e:
        print(f"Operational error during data insert: {e}")
        raise  # Let the caller handle retries
    except Exception as e:
        print(f"Error inserting data: {e}")
        print(traceback.format_exc())
        connection.rollback()

def save_offer_data(connection, cursor, url,offer_data):
    try:
        insert_query = """
        INSERT INTO amazon_offers_data (
            url, asin, name, image_url, sellers, available_filters, 
            total_offers, current_page, total_pages
        )
        VALUES (
            %(url)s, %(asin)s, %(name)s, %(image_url)s, %(sellers)s, %(available_filters)s, 
            %(total_offers)s, %(current_page)s, %(total_pages)s
        );
        """
        cursor.execute(insert_query,{
            'url': url,
            'asin': offer_data.get('product',{}).get('asin'),
            'name': offer_data.get('product',{}).get('name'),
            'image_url': offer_data.get('product',{}).get('image_url'),
            'sellers': json.dumps(offer_data.get('sellers',{})),
            'available_filters': json.dumps(offer_data.get('available_filters',{})),
            'total_offers': offer_data.get('no_of_offers'),
            'current_page': offer_data.get('current_page'),
            'total_pages': offer_data.get('no_of_pages')
        })
        connection.commit()
        print("Data inserted successfully into Amazon_Offers_Data!")

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
        if '"message":""' not in row[1] and 'https://www.amazon.com/gp/product/ajax/' not in row[0]:
            domain = get_domain_name(row[0])
            asin = get_asin(row[0])
            data = amazon_parser(row[0],domain,row[1],asin)
            save_product_data(connection, cursor, data)

        elif 'https://www.amazon.com/gp/product/ajax/' in row[0]:
            data = get_offer_info(row[1])
            save_offer_data(connection, cursor, row[0], data)
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
        cache_cursor.execute("SELECT COUNT(id) FROM res r where r.url  like '%amazon%'")
        total_rows = cache_cursor.fetchone()[0]
        print(total_rows)

        warehouse_connection = connect_with_retries(warehouse_db_config)
        warehouse_cursor = warehouse_connection.cursor()

        while True:
            cache_cursor.execute("SELECT url, content,id FROM res r WHERE r.url LIKE %s ORDER BY id LIMIT %s",
            ('%amazon%', batch_size))
            rows = cache_cursor.fetchall()

            if len(rows) == 0:
                break

            for row in rows:
                data = process_row(warehouse_connection, warehouse_cursor, row)
                if data == 1:
                    cache_cursor.execute("delete from res where id = %s", (row[2],))
                    print('Deleted row:', cache_cursor.rowcount)
                    cache_connection.commit()
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
        if cache_connection:
            cache_connection.close()
        if warehouse_connection:
            warehouse_connection.close()
        