import requests
from urllib.parse import urlencode,parse_qs, urlparse
from bs4 import BeautifulSoup,Comment
import re
import json

API_KEY='YV749KjNlvgdbjsVWkW4'


def send_req_syphoon(
    api_key, method, url, params=None, headers=None, payload=None, cookies=None, total_retries=5
) :

    if params is not None:
        url = f"{url}?{urlencode(params)}"

    if headers is None:
        headers = {}

    if payload is None:
        payload = {}

    payload = {
        **payload,
        "key": api_key,
        "url": url,
        "method": method,
        "keep_headers": True,
    }

    if cookies is not None:
        headers["cookie"] = ";".join([f"{k}={v}" for k, v in cookies.items()])

    retry_count = 0

    while retry_count < total_retries:
        try:
            return requests.post(
                "https://api.syphoon.com", json=payload, headers=headers, verify=False
            )
        except Exception as ex:
            retry_count += 1

headers = {
    'accept': 'application/json',
    'origin': 'https://www.loveholidays.com',
    'priority': 'u=1, i',
    'cookie': 'oct_last_used=2635; lvh_ch=default; lvhid=8755921720781042; rl_page_init_referrer=RudderEncrypt%3AU2FsdGVkX1%2Bntown3Esh%2B2hO0vRLOFGUPnksdQqlsUc%3D; rl_page_init_referring_domain=RudderEncrypt%3AU2FsdGVkX1%2Ftg2whoqfWk4DtiT%2Fqy2hFIfguadUV%2Fbw%3D; lvh_cookies_accepted_ver=1_2024-07-12T10:44:04.738Z; lvh_cookies_accepted={%22GB%22:[%22performance%22%2C%22marketing%22%2C%22essential%22%2C%22social%22]}; _gcl_au=1.1.1934491930.1720781045; _ga=GA1.1.762577308.1720781045; lps=; savedSearchSelection=%25multiSite__%7B%22GB%22%3A%22departureAirports%3DLHR%26nights%3D5%26date%3D2025-04-30%26flexibility%3D0%26rooms%3D2%26sort%3DPOPULAR%22%7D; rl_user_id=RudderEncrypt%3AU2FsdGVkX1%2BzFhgg1L0%2B1Fylm%2Fin69Sr%2F9qRefFm7%2FE%3D; rl_trait=RudderEncrypt%3AU2FsdGVkX1%2BqbT5TAvZgQun6LpISbmzfDdiNle2LUjE%3D; rl_group_id=RudderEncrypt%3AU2FsdGVkX1%2FNhXKVigIFHEb8vDGIpUBaAlXu7eIqBBk%3D; rl_group_trait=RudderEncrypt%3AU2FsdGVkX18DMLB9dkZaUigNxuhrLQMZCZ%2B931iEoDs%3D; rl_anonymous_id=RudderEncrypt%3AU2FsdGVkX19DdX3%2FRdXm6xSWZX2U29VzizZAFn0x5o7Z%2FC3MJ0a31dnmjA0EGwHB; _ga_KC0MW8NHTR=GS1.1.1720791853.3.1.1720791881.32.0.0; _uetsid=a8d3f3b0403b11efb5390398613e8f10; _uetvid=a8d42ac0403b11ef858c1b6f58427a79; datadome=s2i~l_19kqqKfbU2y1hmZ0R_DhGV9LCVQ~URPQDOq4BvdybYcQQ7BMxOjZbPdubuGqPjt_DCqzCenr7W1NN0fOvfYOLbQFr~mpW7qSndglDMSdYjmtdYPAJcINUlSTCs; rl_session=RudderEncrypt%3AU2FsdGVkX18Ej6q4G62CmXpw6H1VX6YMi4DWKo8HX72wj9OwF90bxMZBrgVOhJQ4S54U%2B1ZdRVAImP3d279R%2B7FIwEm57g4Sqr1IIyfgUrrOkPpPYMVblC%2BQGfjfX3PEo4boLB204%2BdW1F1ZcijLhg%3D%3D; datadome=Ur5pEhmK3ZHVoQb~XpBlC2tIHpbkEYwDP027oQTNlc6HPi2zZGpnpNPtu0yAd2fBKoDedXB8H7VdnIUFPIQ00G2w7IbSYdHo7RwsHukWMYpqAW8ZeUuKfnmSLmE6jcRh; lvh_ch=default; lvhid=8755921720781042',

    # 'cookie':'datadome=KKCDIUylV~yDKRzNzs1EVczfgUMjAVdVtYJZ2uuUT4uvZVmizb1OSaBIyPUKAxDf_lWHX5pHxSDJ30Fcnugp5DZELWltAF0Z1xHHkraZnwz5cl1AWiOY2KKlD0lZg~u6',
    'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
}


def make_graphql_request(payload):
    try:
        response = send_req_syphoon(API_KEY,'post','https://www.loveholidays.com/graphql?app=sunrise', headers=headers,payload=payload)
        return response.json()
    except Exception as ex:
        print('Error in send_api_request: ', ex)
        return {}
    

def getOfferDetails(req_params):
    try:
        payload  = {
            'query': 'query getOfferDetails($masterId: ID!, $boardBasis: BoardBasisCode, $departureAirports: [String!]!, $rooms: [RoomConfigurationInput!]!, $nights: Int!, $date: Date!, $cancellationPolicy: [CancellationPolicy!]!, $maxFlightStops: [Float!]!, $includedCheckedBags: [Float!]!) {\n  Search {\n    offerDetails(\n      masterId: $masterId\n      date: $date\n      searchOptions: {boardBasis: $boardBasis, departureAirports: $departureAirports, rooms: $rooms, nights: $nights, cancellationPolicy: $cancellationPolicy, maxFlightStops: $maxFlightStops, includedCheckedBags: $includedCheckedBags}\n      caller: PANDA\n    ) {\n      ...PandaOfferDetailsFragment\n      __typename\n    }\n    __typename\n  }\n}\nfragment PandaOfferDetailsFragment on OfferDetails {\n  hotel {\n    checkInDate\n    nights\n    boardBasisCode\n    accommodation {\n      id\n      sashes {\n        adult {\n          variant\n          label\n          __typename\n        }\n        __typename\n      }\n      name\n      priceBreakdownEligible\n      destination {\n        region {\n          name\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  flights {\n    isOpenJaw\n    luggage {\n      isIncluded\n      displayText\n      tooltip\n      __typename\n    }\n    freeAmendments {\n      from\n      to\n      rebookDate\n      __typename\n    }\n    outbound {\n      ...FlightData\n      __typename\n    }\n    inbound {\n      ...FlightData\n      __typename\n    }\n    __typename\n  }\n  pricing {\n    ...PricingFragment\n    __typename\n  }\n  paymentPlans {\n    payInFull {\n      amount\n      __typename\n    }\n    standardDeposit {\n      amount\n      fee\n      dueDate\n      __typename\n    }\n    spreadTheCost {\n      amount\n      fee\n      repaymentAmount\n      installments\n      __typename\n    }\n    lowDeposit {\n      amount\n      fee\n      initialDueDate\n      dueDate\n      installments\n      __typename\n    }\n    __typename\n  }\n  lowestDeposit\n  bookingLink\n  redirectToNewCheckout\n  badges {\n    type\n    icon\n    borderColor\n    text\n    variant\n    tooltip\n    __typename\n  }\n  isPackageRefundable\n}\nfragment Airport on Airport {\n  id\n  name\n  iataCode\n}\nfragment FlightSegmentItem on OfferFlight {\n  arrivalAirport {\n    ...Airport\n    __typename\n  }\n  departureAirport {\n    ...Airport\n    __typename\n  }\n  departureDate\n  departureTime\n  arrivalDate\n  arrivalTime\n  duration\n  flightNumber\n  operatingCarrier\n  operatingCarrierName\n  stopoverDuration\n}\nfragment FlightData on OfferFlightsLeg {\n  arrivalAirport {\n    ...Airport\n    __typename\n  }\n  departureAirport {\n    ...Airport\n    __typename\n  }\n  departureDate\n  departureTime\n  arrivalDate\n  arrivalTime\n  duration\n  segments {\n    items {\n      ...FlightSegmentItem\n      __typename\n    }\n    __typename\n  }\n}\nfragment PricingFragment on Pricing {\n  currency\n  currencyIcon\n  hotel\n  flight\n  total\n  originalTotal\n  offlinePrice\n  margin\n  previous\n  adult\n  child\n  infant\n  atolProtected\n  atolFee\n  discount\n  discountPercentage\n  showDiscount\n  perPerson\n  referral {\n    uuid\n    xref\n    __typename\n  }\n  discountPresentation {\n    type\n    textTotal\n    textPerPerson\n    tooltipText\n    __typename\n  }\n  pricingPresentation {\n    textTotal\n    textPerPerson\n    wasTotal\n    wasPerPerson\n    showStrikeThrough\n    showPreviousPrice\n    tooltipText\n    discountTotal\n    discountPerPerson\n    discountPercentage\n    __typename\n  }\n}',
                'operationName': 'getOfferDetails',
                'variables': {
                    'masterId': req_params['masterId'],
                    'boardBasis': [],
                    'departureAirports':
                        req_params['departureAirports'].split(',')
                    ,
                    'rooms': req_params['rooms'],
                    'nights':int(req_params['nights']),
                    'date': req_params['date'],
                    'cancellationPolicy': [],
                    'maxFlightStops': [],
                    'includedCheckedBags': [],
                },
            }
        # return payload
        return make_graphql_request(payload)
    except Exception as ex:
        print('Error in loveholidays_scraper: ', ex)
        return {}
    
def getPandaFlightAvailability(req_params):
    try:
        payload = {
            'query': 'fragment FilterStepper on AlternativeFlightFilterStepper {\n  min\n  max\n}\nfragment FilterOption on AlternativeFlightFilterOption {\n  value\n  label\n  price\n}\nfragment FlightOfferDetailsFragment on OfferDetails {\n  badges {\n    type\n    borderColor\n    icon\n    text\n    tooltip\n    variant\n    __typename\n  }\n  isPackageRefundable\n  bookingLink\n  redirectToNewCheckout\n  pricing {\n    ...PricingFragment\n    __typename\n  }\n  hotel {\n    accommodation {\n      id\n      name\n      __typename\n    }\n    __typename\n  }\n  flights {\n    isOpenJaw\n    inbound {\n      ...FlightData\n      __typename\n    }\n    outbound {\n      ...FlightData\n      __typename\n    }\n    freeAmendments {\n      from\n      to\n      rebookDate\n      __typename\n    }\n    luggage {\n      isIncluded\n      displayText\n      tooltip\n      __typename\n    }\n    __typename\n  }\n}\nquery getPandaFlightAvailability($masterId: ID!, $boardBasis: BoardBasisCode, $departureAirports: [String!]!, $rooms: [RoomConfigurationInput!]!, $nights: Int!, $date: Date!, $filters: AlternativeFlightFiltersInput, $offersStart: Int!, $offersLimit: Int!, $includeFullOfferDetails: Boolean!) {\n  Search {\n    alternativeFlights(\n      masterId: $masterId\n      searchOptions: {boardBasis: $boardBasis, departureAirports: $departureAirports, rooms: $rooms, nights: $nights}\n      date: $date\n      filters: $filters\n      caller: PANDA\n    ) {\n      filters {\n        airportPreferences {\n          ...FilterOption\n          __typename\n        }\n        arrivalPreferences {\n          ...FilterOption\n          __typename\n        }\n        cancellationPolicy {\n          ...FilterOption\n          __typename\n        }\n        stops {\n          ...FilterOption\n          __typename\n        }\n        includedCheckedBags {\n          ...FilterStepper\n          __typename\n        }\n        departureAirports {\n          ...FilterOption\n          __typename\n        }\n        carriers {\n          ...FilterOption\n          __typename\n        }\n        outboundTimes {\n          ...FilterOption\n          __typename\n        }\n        inboundTimes {\n          ...FilterOption\n          __typename\n        }\n        duration {\n          min\n          max\n          __typename\n        }\n        __typename\n      }\n      offers(limit: $offersLimit, start: $offersStart) {\n        totalCount\n        items {\n          ...FlightOfferDetailsFragment @skip(if: $includeFullOfferDetails)\n          ...PandaOfferDetailsFragment @include(if: $includeFullOfferDetails)\n          display {\n            highlightLabel\n            highlightColor\n            __typename\n          }\n          flights {\n            inboundSupplier\n            outboundSupplier\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\nfragment PricingFragment on Pricing {\n  currency\n  currencyIcon\n  hotel\n  flight\n  total\n  originalTotal\n  offlinePrice\n  margin\n  previous\n  adult\n  child\n  infant\n  atolProtected\n  atolFee\n  discount\n  discountPercentage\n  showDiscount\n  perPerson\n  referral {\n    uuid\n    xref\n    __typename\n  }\n  discountPresentation {\n    type\n    textTotal\n    textPerPerson\n    tooltipText\n    __typename\n  }\n  pricingPresentation {\n    textTotal\n    textPerPerson\n    wasTotal\n    wasPerPerson\n    showStrikeThrough\n    showPreviousPrice\n    tooltipText\n    discountTotal\n    discountPerPerson\n    discountPercentage\n    __typename\n  }\n}\nfragment Airport on Airport {\n  id\n  name\n  iataCode\n}\nfragment FlightSegmentItem on OfferFlight {\n  arrivalAirport {\n    ...Airport\n    __typename\n  }\n  departureAirport {\n    ...Airport\n    __typename\n  }\n  departureDate\n  departureTime\n  arrivalDate\n  arrivalTime\n  duration\n  flightNumber\n  operatingCarrier\n  operatingCarrierName\n  stopoverDuration\n}\nfragment FlightData on OfferFlightsLeg {\n  arrivalAirport {\n    ...Airport\n    __typename\n  }\n  departureAirport {\n    ...Airport\n    __typename\n  }\n  departureDate\n  departureTime\n  arrivalDate\n  arrivalTime\n  duration\n  segments {\n    items {\n      ...FlightSegmentItem\n      __typename\n    }\n    __typename\n  }\n}\nfragment PandaOfferDetailsFragment on OfferDetails {\n  hotel {\n    checkInDate\n    nights\n    boardBasisCode\n    accommodation {\n      id\n      sashes {\n        adult {\n          variant\n          label\n          __typename\n        }\n        __typename\n      }\n      name\n      priceBreakdownEligible\n      destination {\n        region {\n          name\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  flights {\n    isOpenJaw\n    luggage {\n      isIncluded\n      displayText\n      tooltip\n      __typename\n    }\n    freeAmendments {\n      from\n      to\n      rebookDate\n      __typename\n    }\n    outbound {\n      ...FlightData\n      __typename\n    }\n    inbound {\n      ...FlightData\n      __typename\n    }\n    __typename\n  }\n  pricing {\n    ...PricingFragment\n    __typename\n  }\n  paymentPlans {\n    payInFull {\n      amount\n      __typename\n    }\n    standardDeposit {\n      amount\n      fee\n      dueDate\n      __typename\n    }\n    spreadTheCost {\n      amount\n      fee\n      repaymentAmount\n      installments\n      __typename\n    }\n    lowDeposit {\n      amount\n      fee\n      initialDueDate\n      dueDate\n      installments\n      __typename\n    }\n    __typename\n  }\n  lowestDeposit\n  bookingLink\n  redirectToNewCheckout\n  badges {\n    type\n    icon\n    borderColor\n    text\n    variant\n    tooltip\n    __typename\n  }\n  isPackageRefundable\n}',
            'operationName': 'getPandaFlightAvailability',
            'variables': {
                'masterId': req_params['masterId'],
                'boardBasis': [],
                'departureAirports':
                    req_params['departureAirports'].split(',')
                ,
                'nights': int(req_params['nights']),
                'rooms': req_params['rooms'],
                'date': req_params['date'],
                'filters': {
                    'stops': [
                        '0',
                    ],
                    'includedCheckedBags': 0,
                },
                'offersStart': 0,
                'offersLimit': 10,
                'includeFullOfferDetails': False,
            },
        }
        
        return make_graphql_request(payload)
        # return payload
    
    except Exception as e:
        print(e)
        return {}

def loveholidays_scraper(url):
    try:
        req_params = {k: v[0] if len(v) == 1 else v for k, v in parse_qs(urlparse(url).query).items()}
        rooms = req_params['rooms'].split(',')
        rooms_list = []
        for room in rooms:
            persons = room.split('-')
            room_info = {}
            if len(persons) == 1:
                room_info['adults'] = int(persons[0])
                room_info['childAges'] = []
            else:
                room_info['adults'] = int(persons[0])
                room_info['childAges'] = [int(x) for x in persons[1:]]
            rooms_list.append(room_info)

        req_params['rooms'] = rooms_list

        page_data = {}
        
        # uncomment this code if you want to get html of main page

        # homepage_req = send_req_syphoon(API_KEY,'get',url)
        # homepage_req.raise_for_status()

        # html = homepage_req.text

        # # use this code if you want to remove autopage reload and cookie prompt
        # soup= BeautifulSoup(html,'html.parser')

        # load_script = soup.find('script',string=re.compile('__SENTRY_DSN__'))
        # comment_script = Comment(str(load_script))
        # load_script.replace_with(comment_script)

        # cookies_script = soup.find('script',attrs={'src':re.compile('loveholidays/GB/cookies.js')})
        # commnet_cookies = Comment(str(cookies_script))
        # cookies_script.replace_with(commnet_cookies)

        # html = soup.prettify()

        # page_data['html'] = html
        page_data['Offers'] = getOfferDetails(req_params)
        page_data['Flight Data']  = getPandaFlightAvailability(req_params)

        return page_data

    except Exception as ex:
        print(ex)
        return {}
    
if __name__ == '__main__':
    json.dump(loveholidays_scraper('https://www.loveholidays.com/holidays/l/?masterId=2460&departureAirports=LHR&nights=5&rooms=2&date=2025-04-26&source=srp'),open('output.json','w',encoding='utf-8'),indent=4)