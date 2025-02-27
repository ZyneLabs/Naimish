import json
from bs4 import BeautifulSoup
import requests
import traceback
import os
from dotenv import load_dotenv
load_dotenv(override=True)

APIKEY = os.getenv("APIKEY")

def zillow_scraper(url:str) -> requests.Response | None:
    try:
        payload = {
            "key" : APIKEY, #kw3 will work fine.
            "method" : "GET",
            "url" : url,
            "keep_headers": True
        }
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-US,en;q=0.9',
            'cache-control': 'max-age=0',
            'priority': 'u=0, i',
            'referer': url,
            'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        }

        response = requests.post('https://api.syphoon.com/',json=payload,headers=headers)
        return response
    except:
        print(traceback.print_exc())


def remove_null_values(d: dict) -> dict:

    if not isinstance(d, dict):
        return d
    return {
        k: remove_null_values(v)
        for k, v in d.items()
        if v is not None and v != "" and v != []
    }

def extract_property_data(html: str) -> dict:

    try:
        soup = BeautifulSoup(html,'lxml')
        page_json = json.loads(soup.select_one('#__NEXT_DATA__').text)
        
        if page_json['props']['pageProps']["componentProps"].get('gdpClientCache'):
            data = list(json.loads(page_json['props']['pageProps']["componentProps"]["gdpClientCache"]).values())[0]
            property_json = data.get("property", data)
            return property_json
        else:
            data = page_json['props']['pageProps']["componentProps"]["initialReduxState"]["gdp"]["building"]
            return data
    except json.JSONDecodeError as e:
        print("Error parsing JSON:", e)
        return {}



def parse_property_data(prop: dict) -> dict:
    details = {}

    details["zpid"] = prop.get("zpid")
    details["listingTypeDimension"]  = prop.get("listingTypeDimension")
    if prop.get("hdpUrl"):
        details["url"] = 'https://www.zillow.com'+prop.get("hdpUrl")
    else:
        details["url"] = 'https://www.zillow.com'+ prop.get("bdpUrl")
    details["listingDataSource"] = prop.get("listingDataSource")
    details["propertystatus"] = prop.get("homeStatus")
    details["propertyType"] = prop.get("homeType")  
    details["propertySubType"] = prop.get("propertySubType")

    details["address"] = prop.get("address", {})
    
    if "latLong" in prop:
        details["latitude"] = prop["latLong"].get("latitude")
        details["longitude"] = prop["latLong"].get("longitude")
    else:
        details["latitude"] = prop.get("latitude")
        details["longitude"] = prop.get("longitude")
    
    details["description"] = prop.get("description")
    details["bedrooms"] = prop.get("bedrooms")
    details["bathrooms"] = prop.get("bathrooms")
    details["livingArea"] = prop.get("livingArea")
    details["livingAreaUnits"] = prop.get("livingAreaUnits")
    details["yearBuilt"] = prop.get("yearBuilt")
    if prop.get("responsivePhotos"):
        details["photos"] = [img['url'] for img in prop.get("responsivePhotos")]
    else:
        details["photos"] = [img['mixedSources']['jpeg'][-1]['url'] for img in prop.get("photos")]
    details["price"] = prop.get("price")
    details["unformattedPrice"] = prop.get("unformattedPrice")
    details["currency"] = prop.get("currency")
    details["floorPlans"] = prop.get("floorPlans")
    details["postingUrl"] = prop.get("postingUrl") 
    details["priceHistory"] = prop.get("priceHistory")
    details["priceChangeDateString"] = prop.get("priceChangeDateString")
    details['priceChange'] = prop.get('priceChange')
    details["lastSoldPrice"] = prop.get("lastSoldPrice")
    details["taxHistory"] = prop.get("taxHistory")
    details["propertyTaxRate"] = prop.get("propertyTaxRate")

    details["brokerageName"] = prop.get("brokerageName")
    details["listedBy"]  = prop.get("listedBy")
    details["annualHomeownersInsurance"] = prop.get("annualHomeownersInsurance")
    details["zestimate"]  = prop.get("zestimate")
    details["newConstructionType"] = prop.get("newConstructionType")
    details["zestimateLowPercent"] = prop.get("zestimateLowPercent")
    details["zestimateHighPercent"] = prop.get("zestimateHighPercent")
    details["rentZestimate"] = prop.get("rentZestimate")
    details["restimateLowPercent"] = prop.get("restimateLowPercent")
    details["restimateHighPercent"] = prop.get("restimateHighPercent")
   
    details["datePosted"]  = prop.get("datePostedString")

    details['resoFacts'] =remove_null_values(prop.get("resoFacts", {}))
    details["attribution"] = remove_null_values (prop.get("attributionInfo", {}))

    details["homeInsights"] = prop.get("homeInsights", {})
    details["daysOnZillow"] = prop.get("daysOnZillow")
    details["timeOnZillow"] = prop.get("timeOnZillow")
    details["pageViewCount"] = prop.get("pageViewCount")
    details["favoriteCount"] = prop.get("favoriteCount")
    details["whatILove"] = prop.get("whatILove")
    details["tourViewCount"] = prop.get("tourViewCount")
    
    return details


def zillow_raw_detail(url: str) -> dict | None:
    '''
    Use this for scraping raw property details
    '''
    try:
        response = zillow_scraper(url)
        return extract_property_data(response.text)
        
    except:
        print(traceback.print_exc())
        return 
    
def zillow_parse_detail(url: str) -> dict | None:
    '''
    Use this for parsing property details
    '''
    try:
        response = zillow_scraper(url)
        return parse_property_data(extract_property_data(response.text))
    except:
        print(traceback.print_exc())