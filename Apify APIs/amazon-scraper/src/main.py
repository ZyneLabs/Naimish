from httpx import AsyncClient,ReadTimeout,Timeout
from apify import Actor
import os
from dotenv import load_dotenv
from urllib.parse import urlparse
import asyncio
import re
import time

load_dotenv()
API_KEY = os.environ.get('AMAZON_API_KEY')

timeout = Timeout(5,connect=10,read=30)
client = AsyncClient(timeout=timeout)
MAX_CONCURRENT_REQUESTS = 10

def search_urls(text):
    # getting urls from text

    url_pattern = re.compile(
        r'(https?://(?:www\.)?[-\w]+(?:\.\w[-\w]*)+(:\d+)?(?:/[^.!,?;"\'<>()\[\]{}\s\x7F-\xFF]*(?:[.!,?]+[^.!,?;"\'<>()\[\]{}\s\x7F-\xFF]+)?)?)'
    )
    urls = url_pattern.findall(text)
    return urls

async def load_data_from_url(url):
    # getting file data from url

    response = await client.get(url)
    response.raise_for_status()
    return search_urls(response.text)
    

async def process_request(request):
    # sending request to syphoon api

    response  = None
    try: 
        data = {
            "url": request['url'],
            "key": API_KEY,
            "method": 'get',
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
        actor_input = await Actor.get_input() or {}
        input_urls = actor_input.get('urls')

        # returning remaining urls but it will not be used by apify platform
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

        Actor.log.info(f'Enqueuing urls...')

        # making queue for a request
        for url in urls:
            if type(url) == dict:
                url = url.get('url')
            elif type(url) == tuple:
                url = url[0]
            if 'https' not in url or 'amazon' not in urlparse(url).netloc: continue
            default_queue.append({"url":url,"retryCount":3})

        Actor.log.info(f'Enqueuing {len(default_queue)} urls...')

        
        # limiting number of concurrent requests
        sem = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

        async def process_with_sem(request):
            async with sem:
                return await process_request(request)

        while default_queue:
            # making batch of requests
            request_tasks = [ process_with_sem(request) for request in default_queue[:MAX_CONCURRENT_REQUESTS]]

            start = time.time()
            
            # gathering responses
            results = await asyncio.gather(*request_tasks, return_exceptions=True)
            
            Actor.log.info(f'Processed {len(results)} requests in {time.time() - start:.2f} seconds')

            # processing responses
            for request,response in results:
                if response and not isinstance(request, Exception):
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
            Actor.log.info(f'Batch of requests processed in {time.time() - start:.2f} seconds')