from common import *

def avnet_get_releted_products(product_url):
    headers = {
        'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'Content-Type': 'application/json'
    }

    res = send_req_syphoon(0, "GET", product_url, headers=headers)
  
    if res.status_code != 200:
        return {'message' : 'Page loading failed'}
    
    releted_products_url = search_text_between(res.text, "newSubAltCallURL = '", "';")
    
    if releted_products_url is None:
        return {'message' : 'No releted products found'}
    releted_products_url = releted_products_url.replace("/shop/search/","/search/").replace('byIds/?','byIds?')
    print(releted_products_url)
    releted_product_res = send_req_syphoon(0, "GET", releted_products_url, headers=headers)

    if releted_product_res.status_code != 200:
        return {'message' : 'Releted products loading failed'}
    
    
    releted_products = [
        {
            'url': product.get('resourceId',''),
            'id' : product.get('uniqueID',''),
            'productNumber' : product.get('productNumber',''),
            'manufacturePartNumber': product.get('mfPartNumber_ntk',''),
            'manufacturer' : product.get('manufacturer',''),
            'description' : product.get('shortDescription',''),
            'price': product.get('price_USD',''),
         }

        for product in releted_product_res.json()['catalogEntryView']
    ]

    return releted_products

if __name__ == "__main__":
    urls = [
            # 'https://www.avnet.com/shop/us/products/amphenol/d38999-26wc35pn-3074457345628692271/',
            # 'https://www.avnet.com/shop/us/products/amphenol/d38999-26wf35pn-3074457345641494195/',
            # 'https://www.avnet.com/shop/us/products/odu/s11yar-p05xjg0-0000-3074457345635862023/'
            'https://www.avnet.com/shop/us/products/amphenol/d38999-20wb98pn-3074457345628683660/'
        ]
    for url in urls:
        with open('Response.json','w') as f:
            json.dump(avnet_get_releted_products(url),f,indent=4)