import os
import json
import psycopg2


def save_data():
    db = psycopg2.connect(
        host="localhost",
        database="postgres",
        user="postgres",
        password="postgres"
    )

    cursor = db.cursor()
    chunk_limit = 1000

    def get_latest_version(website_name):
        cursor.execute(f"SELECT MAX(version) FROM  versions where website = '{website_name}'")
        latest_version = cursor.fetchone()[0]
        if latest_version is None:
            latest_version = 1
        else:
            latest_version += 1
        cursor.execute(f"INSERT INTO versions (website, version) VALUES ('{website_name}', {latest_version})")
        db.commit()
        return latest_version

    # read all the json files
    for file in os.listdir():
        if file.endswith(".json"):
            with open(file, 'r') as f:
                data = f.read()

                data = json.loads(data.replace('][',','))

                if len(data)>0:
                    version = get_latest_version(file.replace('.json', ''))

                    chunk_data = []
                    for item in data:
                        if type(item.get('extra')) == dict:
                            item['extra'] = ' | '.join([f'{key}: {value}' for key, value in item['extra'].items()])
                        
                        input_data = ['default']
                        input_data.extend(item.values())
                        input_data.append(version)

                        chunk_data.append(tuple(input_data))

                        if len(chunk_data) == chunk_limit:
                            cursor.executemany(f"INSERT INTO cars_crawl VALUES %s", chunk_data)
                        
                # move file to other folder
                os.makedirs('crawled_data', exist_ok=True)
                os.rename(file, os.path.join('crawled_data', file))
                