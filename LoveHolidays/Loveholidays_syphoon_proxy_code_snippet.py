import requests

headers = {
    'content-type': 'application/json',
    'origin': 'https://www.loveholidays.com',
    'priority': 'u=1, i',
    # 'cookie':'datadome=KKCDIUylV~yDKRzNzs1EVczfgUMjAVdVtYJZ2uuUT4uvZVmizb1OSaBIyPUKAxDf_lWHX5pHxSDJ30Fcnugp5DZELWltAF0Z1xHHkraZnwz5cl1AWiOY2KKlD0lZg~u6',
    'referer': 'https://www.loveholidays.com/holidays/l/?masterId=424950&departureAirports=LHR&nights=5&rooms=2&date=2025-04-30&maxFlightStops=0&source=srp',
    'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
}

payload = {
    'query': 'fragment FilterStepper on AlternativeFlightFilterStepper {\n  min\n  max\n}\nfragment FilterOption on AlternativeFlightFilterOption {\n  value\n  label\n  price\n}\nfragment FlightOfferDetailsFragment on OfferDetails {\n  badges {\n    type\n    borderColor\n    icon\n    text\n    tooltip\n    variant\n    __typename\n  }\n  isPackageRefundable\n  bookingLink\n  redirectToNewCheckout\n  pricing {\n    ...PricingFragment\n    __typename\n  }\n  hotel {\n    accommodation {\n      id\n      name\n      __typename\n    }\n    __typename\n  }\n  flights {\n    isOpenJaw\n    inbound {\n      ...FlightData\n      __typename\n    }\n    outbound {\n      ...FlightData\n      __typename\n    }\n    freeAmendments {\n      from\n      to\n      rebookDate\n      __typename\n    }\n    luggage {\n      isIncluded\n      displayText\n      tooltip\n      __typename\n    }\n    __typename\n  }\n}\nquery getPandaFlightAvailability($masterId: ID!, $boardBasis: BoardBasisCode, $departureAirports: [String!]!, $rooms: [RoomConfigurationInput!]!, $nights: Int!, $date: Date!, $filters: AlternativeFlightFiltersInput, $offersStart: Int!, $offersLimit: Int!, $includeFullOfferDetails: Boolean!) {\n  Search {\n    alternativeFlights(\n      masterId: $masterId\n      searchOptions: {boardBasis: $boardBasis, departureAirports: $departureAirports, rooms: $rooms, nights: $nights}\n      date: $date\n      filters: $filters\n      caller: PANDA\n    ) {\n      filters {\n        airportPreferences {\n          ...FilterOption\n          __typename\n        }\n        arrivalPreferences {\n          ...FilterOption\n          __typename\n        }\n        cancellationPolicy {\n          ...FilterOption\n          __typename\n        }\n        stops {\n          ...FilterOption\n          __typename\n        }\n        includedCheckedBags {\n          ...FilterStepper\n          __typename\n        }\n        departureAirports {\n          ...FilterOption\n          __typename\n        }\n        carriers {\n          ...FilterOption\n          __typename\n        }\n        outboundTimes {\n          ...FilterOption\n          __typename\n        }\n        inboundTimes {\n          ...FilterOption\n          __typename\n        }\n        duration {\n          min\n          max\n          __typename\n        }\n        __typename\n      }\n      offers(limit: $offersLimit, start: $offersStart) {\n        totalCount\n        items {\n          ...FlightOfferDetailsFragment @skip(if: $includeFullOfferDetails)\n          ...PandaOfferDetailsFragment @include(if: $includeFullOfferDetails)\n          display {\n            highlightLabel\n            highlightColor\n            __typename\n          }\n          flights {\n            inboundSupplier\n            outboundSupplier\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\nfragment PricingFragment on Pricing {\n  currency\n  currencyIcon\n  hotel\n  flight\n  total\n  originalTotal\n  offlinePrice\n  margin\n  previous\n  adult\n  child\n  infant\n  atolProtected\n  atolFee\n  discount\n  discountPercentage\n  showDiscount\n  perPerson\n  referral {\n    uuid\n    xref\n    __typename\n  }\n  discountPresentation {\n    type\n    textTotal\n    textPerPerson\n    tooltipText\n    __typename\n  }\n  pricingPresentation {\n    textTotal\n    textPerPerson\n    wasTotal\n    wasPerPerson\n    showStrikeThrough\n    showPreviousPrice\n    tooltipText\n    discountTotal\n    discountPerPerson\n    discountPercentage\n    __typename\n  }\n}\nfragment Airport on Airport {\n  id\n  name\n  iataCode\n}\nfragment FlightSegmentItem on OfferFlight {\n  arrivalAirport {\n    ...Airport\n    __typename\n  }\n  departureAirport {\n    ...Airport\n    __typename\n  }\n  departureDate\n  departureTime\n  arrivalDate\n  arrivalTime\n  duration\n  flightNumber\n  operatingCarrier\n  operatingCarrierName\n  stopoverDuration\n}\nfragment FlightData on OfferFlightsLeg {\n  arrivalAirport {\n    ...Airport\n    __typename\n  }\n  departureAirport {\n    ...Airport\n    __typename\n  }\n  departureDate\n  departureTime\n  arrivalDate\n  arrivalTime\n  duration\n  segments {\n    items {\n      ...FlightSegmentItem\n      __typename\n    }\n    __typename\n  }\n}\nfragment PandaOfferDetailsFragment on OfferDetails {\n  hotel {\n    checkInDate\n    nights\n    boardBasisCode\n    accommodation {\n      id\n      sashes {\n        adult {\n          variant\n          label\n          __typename\n        }\n        __typename\n      }\n      name\n      priceBreakdownEligible\n      destination {\n        region {\n          name\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  flights {\n    isOpenJaw\n    luggage {\n      isIncluded\n      displayText\n      tooltip\n      __typename\n    }\n    freeAmendments {\n      from\n      to\n      rebookDate\n      __typename\n    }\n    outbound {\n      ...FlightData\n      __typename\n    }\n    inbound {\n      ...FlightData\n      __typename\n    }\n    __typename\n  }\n  pricing {\n    ...PricingFragment\n    __typename\n  }\n  paymentPlans {\n    payInFull {\n      amount\n      __typename\n    }\n    standardDeposit {\n      amount\n      fee\n      dueDate\n      __typename\n    }\n    spreadTheCost {\n      amount\n      fee\n      repaymentAmount\n      installments\n      __typename\n    }\n    lowDeposit {\n      amount\n      fee\n      initialDueDate\n      dueDate\n      installments\n      __typename\n    }\n    __typename\n  }\n  lowestDeposit\n  bookingLink\n  redirectToNewCheckout\n  badges {\n    type\n    icon\n    borderColor\n    text\n    variant\n    tooltip\n    __typename\n  }\n  isPackageRefundable\n}',
    'operationName': 'getPandaFlightAvailability',
    'variables': {
        'masterId': 424950,
        'boardBasis': [],
        'departureAirports': [
            'LHR',
        ],
        'nights': 5,
        'rooms': [
            {
                'adults': 2,
                'childAges': [],
            },
        ],
        'date': '2025-01-30',
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
api_data = {
	        "key":"xb5Tel13Cuq3kkgttKWr",
            "keep_headers": True,
            "url": "https://www.loveholidays.com/graphql?app=sunrise",
            "method": "POST"
}
api_data.update(payload)
response = requests.post('https://api.syphoon.com', headers=headers, json=api_data)

print(response.text)
print(response.status_code)

# xb5Tel13Cuq3kkgttKWr,KPPahCDcpBELCzbdUSQo,4CjB1r09INeDNieOarUW