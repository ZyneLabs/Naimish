from httpx import AsyncClient,ReadTimeout,Timeout
from apify import Actor
import os
from dotenv import load_dotenv
from urllib.parse import urlparse
import asyncio
import re
import time

load_dotenv()
API_KEY = os.environ.get('SHOPEE_API_KEY')

timeout = Timeout(5,connect=10,read=30)

def search_urls(text):
    url_pattern = re.compile(
        r'(https?://(?:www\.)?[-\w]+(?:\.\w[-\w]*)+(:\d+)?(?:/[^.!,?;"\'<>()\[\]{}\s\x7F-\xFF]*(?:[.!,?]+[^.!,?;"\'<>()\[\]{}\s\x7F-\xFF]+)?)?)'
    )
    urls = url_pattern.findall(text)
    return urls

async def load_data_from_url(url):
    async with AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return search_urls(response.text)
        

async def process_request(request,urls_type):
    response  = None
    try:
        async with AsyncClient() as client:
            data = {
                "url": request['url'],
                "key": API_KEY,
                "method": 'get',
                "data_type": urls_type
            }
            response = await client.post('https://api.syphoon.com', json=data,timeout=timeout)
            response.raise_for_status()

    except ReadTimeout as e:
        if request['retryCount']>0:
            request['retryCount'] = request['retryCount']-1
         
    except Exception as e:
        
        if request['retryCount']>0:
            request['retryCount'] = request['retryCount']-1
        
    return request,response

async def main() -> None:

    async with Actor:
        # Structure of input is defined in input_schema.json
        actor_input = await Actor.get_input() or {}
        input_urls = actor_input.get('urls')
        urls_type = actor_input.get('urls_type')
        remaining_urls_dataset = await Actor.open_dataset(name='remaining-urls')
        urls = []
        default_queue = []
        try:
            for input_url in input_urls:
                if input_url.get('requestsFromUrl','') != '':
                    urls.extend(await load_data_from_url(input_url.get('requestsFromUrl','')))
                elif input_url.get('url'):
                    urls.append(input_url.get('url'))
        except:
            Actor.fail('Cannot load data from File.')

        Actor.log.info(f'Enqueuing {len(urls)} urls...')
        for url in urls:
            if (urls_type == 'search' and 'search' not in url) or (urls_type == 'product' and '/search/' in url):
                await remaining_urls_dataset.push_data({'url':url})
                continue

            if type(url) == dict:
                url = url.get('url')
            elif type(url) == tuple:
                url = url[0]
            if 'https' not in url or 'shopee' not in urlparse(url).netloc: continue
            default_queue.append({"url":url,"retryCount":3})


        while default_queue:
            request_tasks = []
            for request in default_queue[:10]:
                default_queue.remove(request)
                Actor.log.info(f'URL: {request["url"]  }')
                request_tasks.append(process_request(request,urls_type))

            results = await asyncio.gather(*request_tasks)
            for request,response in results:
                if response:
                    if response.status_code == 200:
                        response_data = response.json()
                        await Actor.push_data(response_data)
                    else:
                        await Actor.push_data(response.json())

                elif request['retryCount']>0:
                    default_queue.append(request)
                    Actor.log.info(f'Retrying to {request["url"]}...')
                else:
                    await remaining_urls_dataset.push_data({'url':request['url']})
