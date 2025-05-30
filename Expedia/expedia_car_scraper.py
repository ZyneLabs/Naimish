import urllib.parse
import re
import json
from uuid import uuid4
import asyncio
from httpx import AsyncClient

DOMAIN_CONFIG = {
    'expedia.co.id' : {
        'siteId' :61,
        'locale': 'en_GB',
        'eapid': 0,
        'currency': 'IDR',
    },

    'expedia.co.uk':{
        'siteId': 3,
        'locale': 'en_GB',
        'eapid': 0,
        'currency': 'GBP',
    },
}

def parse_dt(qs_dict,date_key, time_key):
    date_str = qs_dict[date_key][0]   
    if '-' in date_str:    
        year, month, day = map(int, date_str.split('-'))
    else:
        day, month, year = map(int, date_str.split('/'))

    time_str = qs_dict[time_key][0]       
    m = re.match(r"(\d{3,4})(AM|PM)", time_str)
    if not m:
        raise ValueError(f"Bad time: {time_str}")
    hhmm, ampm = m.groups()
    hhmm = hhmm.zfill(4)
    hour = int(hhmm[:2])
    minute = int(hhmm[2:])
    
    if ampm == 'PM' and hour != 12:
        hour += 12
    if ampm == 'AM' and hour == 12:
        hour = 0

    return {
        'day': day,
        'month': month,
        'year': year,
        'hour': hour,
        'minute': minute,
        'second': 0,
    }

def make_search_payload_from_url(url):

    parts = urllib.parse.urlparse(url)
    qs_dict = urllib.parse.parse_qs(parts.query)

    pickup = parse_dt(qs_dict,'date1', 'time1')
    dropoff = parse_dt(qs_dict,'date2', 'time2')

    selections = []
    
    for key, values in qs_dict.items():
        if key in {'locn', 'dpln', 'd1', 'd2', 'date1', 'date2', 'time1', 'time2'} or key == 'searchId':
            continue
        raw = values[0]

        if raw.startswith('[') and raw.endswith(']'):
            try:
                items = json.loads(raw)
            except json.JSONDecodeError:
                items = [raw]
        else:
            items = [raw]

        for item in items:
            if isinstance(item, str):
                selections.append({'id': key, 'value': item})
            else:
                selections.append({'id': key, 'value': str(item)})

    try:
        sid = qs_dict.get('searchId')[0]
    except:
        sid = str(uuid4())

    selections.append({'id': 'searchId', 'value': sid})

    domain_details = DOMAIN_CONFIG[parts.netloc.replace('www.','')]
    payload = {
        'query': 'query CarSearchV3($context: ContextInput!, $primaryCarSearchCriteria: PrimaryCarCriteriaInput!, $secondaryCriteria: ShoppingSearchCriteriaInput!, $shoppingContext: ShoppingContextInput) {\n  carSearchOrRecommendations(\n    context: $context\n    primaryCarSearchCriteria: $primaryCarSearchCriteria\n    secondaryCriteria: $secondaryCriteria\n    shoppingContext: $shoppingContext\n  ) {\n    carSearchResults {\n      shoppingContext {\n        multiItem {\n          id\n        }\n      }\n      carsShoppingContext {\n        searchId\n      }\n      multiItemAnchorPriceToken\n      multiItemPickUpDropOffMessage {\n        message {\n          __typename\n          ... on CarPhraseText {\n            text\n          }\n        }\n      }\n      multiItemPlayBackTitleBar {\n        primary {\n          __typename\n          ... on CarPhraseText {\n            text\n          }\n        }\n        secondary {\n          longMessage {\n            __typename\n            ... on CarPhraseText {\n              text\n            }\n          }\n          shortMessage {\n            __typename\n            ... on CarPhraseText {\n              text\n            }\n          }\n          accessibilityMessage {\n            __typename\n            ... on CarPhraseText {\n              text\n            }\n          }\n        }\n      }\n      listings {\n        __typename\n        ... on CarMessagingCard {\n          ...messagingCard\n        }\n        ... on CarOfferCard {\n          accessibilityString\n          offerBadges {\n            ...badge\n          }\n          offerDiscountBadges {\n            ...badge\n          }\n          vehicle {\n            image {\n              ...image\n            }\n            ecoFriendlyFuel {\n              ... on CarsRichText {\n                value\n                style\n                theme\n              }\n            }\n            category\n            categoryIcon {\n              ...icon\n            }\n            description\n            attributes {\n              icon {\n                ...icon\n              }\n              text\n            }\n            features {\n              ...feature\n            }\n            fuelInfo {\n              ...feature\n            }\n          }\n          tripLocations {\n            pickUpLocation {\n              ...carOfferVendorLocationInfo\n            }\n            dropOffLocation {\n              ...carOfferVendorLocationInfo\n            }\n          }\n          vendor {\n            image {\n              ...image\n            }\n          }\n          detailsContext {\n            carOfferToken\n            selectedAccessories\n            rewardPointsSelection\n            continuationContextualId\n          }\n          priceBadges {\n            ...badge\n          }\n          actionableConfidenceMessages {\n            ...carPhrase\n          }\n          loyaltyEarnWithMQDMessage {\n            ...carPhrase\n          }\n          review {\n            rating\n            superlative\n            totalCount\n            richRatingText {\n              ...detailsRichText\n            }\n          }\n          priceSummary {\n            ...offerPriceSummary\n          }\n          shortList {\n            favorited\n            saveUrl\n            removeUrl\n          }\n          action {\n            ...carAction\n          }\n          reserveButtonText\n          reserveButtonAction {\n            ...carPhrase\n          }\n          infositeURL {\n            relativePath\n          }\n          offerHeading\n          multiItemPriceToken\n          additionalBenefits {\n            ...carPhrase\n          }\n          cancellationAndPaymentMessages {\n            ...carPhrase\n          }\n          clubbedPriceOptions {\n            dialogTrigger {\n              ...carActionableItem\n            }\n            dialogContent {\n              title\n              vendor {\n                image {\n                  ...image\n                }\n              }\n              vehicleCategory\n              vehicleDescription\n              optionsSummary {\n                ...carPhrase\n              }\n              clubbedPrices {\n                heading {\n                  ...carPhrase\n                }\n                title {\n                  ...carPhrase\n                }\n                offerBadges {\n                  ...badge\n                }\n                priceBadges {\n                  ...badge\n                }\n                priceSummary {\n                  ...offerPriceSummary\n                }\n                paymentMessages {\n                  ...carPhrase\n                }\n                additionalPaymentMessages {\n                  ...carPhrase\n                }\n                cancellationMessages {\n                  ...carPhrase\n                }\n                additionalBenefits {\n                  ...carPhrase\n                }\n                loyaltyEarnMessages {\n                  ...carPhrase\n                }\n                reserveButtonAction {\n                  ...carAction\n                }\n                reserveButtonText\n                infositeURL {\n                  relativePath\n                }\n              }\n              commonAdditionalBenefits {\n                ...carPhrase\n              }\n              modalFooter\n            }\n          }\n          isFareComparisonTestEnabled\n          priceSummaryText\n          enhancedCleanlinessDialog {\n            images {\n              value\n            }\n            title\n            description\n            content {\n              title {\n                icon {\n                  ...icon\n                }\n                text\n              }\n              infos\n            }\n            carouselButtonAllyStrings\n          }\n          guaranteedAnalytics {\n            ...analytics\n          }\n          personalisedDeal {\n            ...carPhrase\n          }\n          tripsSaveItemWrapper {\n            tripsSaveItem {\n              initialChecked\n              itemId\n              source\n              attributes {\n                ...TripsSaveCarOfferAttributesFragment\n                ...TripsSaveStayAttributesFragment\n                ...TripsSaveActivityAttributesFragment\n                ...TripsSaveFlightSearchAttributesFragment\n              }\n              save {\n                ...TripsSaveItemPropertiesFragment\n              }\n              remove {\n                ...TripsSaveItemPropertiesFragment\n              }\n            }\n            variant\n          }\n          offerPositionClickAnalytics {\n            ...analytics\n          }\n        }\n        ... on InsurtechPrimingCarListingCard {\n          placement {\n            placementContext {\n              lob\n              path\n              packageType\n              placement\n            }\n          }\n        }\n      }\n      carRentalLocations {\n        routeType\n        pickUpLocation {\n          ...carSearchLocation\n        }\n        dropOffLocation {\n          ...carSearchLocation\n        }\n        searchAccessibility\n      }\n      changeRentalLocation {\n        link {\n          ... on CarActionableItem {\n            text\n          }\n        }\n        placeHolder {\n          ... on CarPhraseText {\n            text\n          }\n        }\n        primary {\n          ... on CarPhraseText {\n            text\n          }\n        }\n        secondary {\n          ... on CarPhraseText {\n            text\n          }\n        }\n      }\n      summary {\n        title\n        dynamicTitle {\n          ...carPhrase\n        }\n        pageTitle\n        includedFeeFooter {\n          title\n          description\n        }\n        carRecommendations {\n          ...carRecommendations\n        }\n      }\n      filterNoMatchMessage {\n        messagingCard {\n          ...messagingCard\n        }\n        allOffersTextSeparator\n      }\n      loadMoreAction {\n        action {\n          ...carAction\n        }\n        icon {\n          ...icon\n        }\n        searchPagination {\n          size\n          startingIndex\n        }\n        text\n      }\n      loyaltyInfo {\n        __typename\n        ... on CarPhraseText {\n          text\n        }\n        ... on CarActionableItem {\n          ...carActionableItem\n        }\n        ... on CarPhraseMark {\n          text\n          name\n          url {\n            value\n            relativePath\n          }\n          description\n        }\n      }\n      oneKeyInfo {\n        isOneKeyEnrolled\n      }\n      saleBannerInfo {\n        isSaleBannerApplicableForGuestUser\n      }\n      sortAndFilter {\n        title\n        close {\n          ...icon\n        }\n        appliedFilterCount\n        clearButtonTitle\n        sections {\n          title\n          fields {\n            __typename\n            primary\n            secondary\n            ...SingleSelectionFragment\n            ...MultiSelectionFragment\n          }\n        }\n      }\n      carAppliedSortAndFilters {\n        appliedSortAndFilters {\n          id\n          text\n          value\n          crossIcon {\n            ...icon\n          }\n          analytics {\n            ...clientSideAnalytics\n          }\n        }\n      }\n      shareFeedbackAction {\n        text\n        button {\n          ...carActionableItem\n        }\n      }\n      adsTargetingData {\n        uuid\n        siteId\n        pageName\n        origin\n        dest\n        locResolver\n        dateStart\n        dateEnd\n        adProvider\n      }\n      recommendedSortDisclaimer {\n        ...carPhrase\n      }\n      recommendedSortExplanation {\n        content {\n          ...carPhrase\n        }\n        feedback {\n          ...searchUserFeedback\n        }\n        closeAnalytics {\n          ...analytics\n        }\n        closeIconLabel\n      }\n      makeModelDisclaimer {\n        ...carPhrase\n      }\n      map {\n        title\n        text\n        dialogAccessibility\n        closeIcon {\n          ...icon\n        }\n        closeAction {\n          ...carAction\n        }\n        center {\n          ...coordinates\n        }\n        bounds {\n          northeast {\n            ...coordinates\n          }\n          southwest {\n            ...coordinates\n          }\n        }\n        zoomLevel\n        markers {\n          __typename\n          type\n          action {\n            ...carAction\n          }\n          hoverAction {\n            ...analytics\n          }\n          coordinates {\n            ...coordinates\n          }\n          ... on CarItemCardMapMarker {\n            itemCard {\n              ... on CarMapSearchLocationCard {\n                title\n                text\n              }\n              ... on CarMapPickupLocationCard {\n                vendorLocationId\n                placeId\n                vendorImage {\n                  ...image\n                }\n                vendorReview {\n                  rating\n                  superlative\n                  totalCount\n                  richRatingText {\n                    ...detailsRichText\n                  }\n                }\n                address\n                shortAddress\n                distance\n                superlative\n                priceSummary {\n                  lead {\n                    ...priceInfo\n                  }\n                  total {\n                    ...priceInfo\n                  }\n                  strikeThroughFirst\n                  loyaltyPointsOption {\n                    formattedPoints\n                    leadingCaption\n                    pointsFirst\n                    pointsAmount {\n                      raw\n                      formatted\n                    }\n                  }\n                  accessibility\n                }\n                seeCarsButtonText\n                action {\n                  ...carAction\n                }\n                totalResultsByLocation\n                totalResultsByLocationFormatted\n              }\n            }\n          }\n        }\n        mapButton {\n          url {\n            value\n          }\n          text\n          action {\n            ...carAction\n          }\n        }\n        filterTitle\n        mapSearchThisAreaButton {\n          text\n          action {\n            ...carAction\n          }\n        }\n      }\n      isCaliforniaUser\n    }\n    carsErrorContent {\n      icon {\n        ...icon\n      }\n      heading\n      subText\n      analytics {\n        linkName\n        referrerId\n      }\n      errorEventName\n      locationAnalytics {\n        linkName\n        referrerId\n      }\n    }\n    carRecommendationContent {\n      ... on CarRecommendations {\n        ...carRecommendations\n      }\n    }\n  }\n}\n\nfragment messagingCard on CarMessagingCard {\n  title\n  cardTitle {\n    ...carPhrase\n  }\n  description\n  descriptions\n  cardDescriptions {\n    ...carPhrase\n  }\n  mark\n  image {\n    description\n    url\n  }\n  illustrationURL {\n    value\n  }\n  icon {\n    ...icon\n  }\n  badge {\n    ...badge\n  }\n  links {\n    text\n    url {\n      value\n      relativePath\n    }\n    icon {\n      ...icon\n    }\n    action {\n      actionType\n      analytics {\n        linkName\n        referrerId\n      }\n    }\n    disabled\n  }\n  dialog {\n    title\n    buttonText\n    text\n    content {\n      header {\n        ...carPhrase\n      }\n      body {\n        title {\n          ...carPhrase\n        }\n        body {\n          ...carPhrase\n        }\n      }\n      footer {\n        ...carPhrase\n      }\n    }\n    type\n  }\n  carRecommendations {\n    ...carRecommendations\n  }\n  analytics {\n    ...analytics\n  }\n  linkPosition\n}\n\nfragment carPhrase on CarPhrase {\n  __typename\n  ... on CarPhraseText {\n    text\n  }\n  ... on CarPhrasePairText {\n    richText {\n      ...detailsRichText\n    }\n    richSubText {\n      ...detailsRichText\n    }\n  }\n  ... on CarPhraseIconText {\n    text\n    icon {\n      ...icon\n    }\n  }\n  ... on CarActionableItem {\n    ...carActionableItem\n  }\n  ... on CarDialogConfidenceMessage {\n    ...carDialogConfidenceMessage\n  }\n  ... on CarsRichText {\n    value\n    style\n    theme\n  }\n  ... on CarPhraseMark {\n    text\n    name\n    url {\n      value\n      relativePath\n    }\n    description\n  }\n  ... on CarOfferBadge {\n    icon {\n      ...icon\n    }\n    mark {\n      id\n      url {\n        value\n      }\n    }\n    text\n    badgeTheme: theme\n  }\n  ... on CarActionableItemForSignin {\n    memberSignInDialog {\n      __typename\n      actionDialog {\n        __typename\n        footer {\n          __typename\n          buttons {\n            ...tertiaryButton\n            ...primaryButton\n          }\n        }\n        closeAnalytics {\n          linkName\n          referrerId\n        }\n      }\n      dialogContent\n      title\n      graphic {\n        ...UIGraphicFragment\n      }\n      triggerMessage {\n        accessibility\n        label\n        __typename\n      }\n    }\n  }\n}\n\nfragment detailsRichText on CarsRichText {\n  value\n  theme\n  style\n}\n\nfragment icon on Icon {\n  description\n  id\n  withBackground\n  size\n  spotLight\n}\n\nfragment carActionableItem on CarActionableItem {\n  url {\n    value\n    relativePath\n  }\n  action {\n    ...carAction\n  }\n  text\n  icon {\n    ...icon\n  }\n}\n\nfragment carAction on CarAction {\n  actionType\n  accessibility\n  analytics {\n    ...analytics\n  }\n}\n\nfragment analytics on CarAnalytics {\n  linkName\n  referrerId\n}\n\nfragment carDialogConfidenceMessage on CarDialogConfidenceMessage {\n  text\n  icon {\n    ...icon\n  }\n  openDialogAction {\n    ...carAction\n  }\n  dialogContent {\n    title\n    text\n    buttonText\n    content {\n      header {\n        ...dialogContentCarPhrase\n      }\n      body {\n        __typename\n        title {\n          ...dialogContentCarPhrase\n        }\n        body {\n          ...dialogContentCarPhrase\n        }\n      }\n      footer {\n        ...dialogContentCarPhrase\n      }\n    }\n    type\n  }\n  iconMobileRender\n  theme\n}\n\nfragment dialogContentCarPhrase on CarPhrase {\n  __typename\n  ... on CarPhraseText {\n    text\n  }\n  ... on CarPhraseIconText {\n    text\n    icon {\n      ...icon\n    }\n  }\n  ... on CarsRichText {\n    value\n    style\n  }\n  ... on CarActionableItem {\n    ...carActionableItem\n  }\n}\n\nfragment tertiaryButton on UITertiaryButton {\n  __typename\n  accessibility\n  analytics {\n    referrerId\n    linkName\n  }\n  egdsElementId\n  disabled\n  icon {\n    id\n    size\n  }\n  primary\n  action {\n    ... on UILinkAction {\n      __typename\n      resource {\n        value\n        __typename\n      }\n      analytics {\n        referrerId\n        linkName\n      }\n    }\n  }\n}\n\nfragment primaryButton on UIPrimaryButton {\n  __typename\n  disabled\n  primary\n  accessibility\n  icon {\n    __typename\n  }\n  action {\n    ...linkAction\n  }\n  analytics {\n    __typename\n    linkName\n    referrerId\n    uisPrimeMessages {\n      messageContent\n      schemaName\n    }\n  }\n}\n\nfragment linkAction on UILinkAction {\n  __typename\n  resource {\n    value\n    __typename\n  }\n  analytics {\n    linkName\n    referrerId\n    __typename\n  }\n}\n\nfragment UIGraphicFragment on UIGraphic {\n  ... on Icon {\n    ...IconFragment\n  }\n  ... on Mark {\n    ...MarkFragment\n  }\n  ... on Illustration {\n    ...IllustrationFragment\n  }\n  __typename\n}\n\nfragment IconFragment on Icon {\n  description\n  id\n  iconSize: size\n  iconTheme: theme\n  title\n  withBackground\n  spotLight\n  __typename\n}\n\nfragment MarkFragment on Mark {\n  description\n  id\n  markSize: size\n  url {\n    ... on HttpURI {\n      relativePath\n      value\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment IllustrationFragment on Illustration {\n  description\n  id\n  link: url\n  __typename\n}\n\nfragment badge on CarOfferBadge {\n  icon {\n    ...icon\n  }\n  text\n  theme\n  mark {\n    id\n    url {\n      value\n    }\n  }\n}\n\nfragment carRecommendations on CarRecommendations {\n  __typename\n  heading\n  analytics {\n    linkName\n    referrerId\n  }\n  carRecommendationsCards {\n    ...carRecommendationCard\n  }\n}\n\nfragment carRecommendationCard on CarRecommendationCard {\n  __typename\n  icon {\n    ...icon\n  }\n  action {\n    ...carAction\n  }\n  ... on DateTimeRecommendationCard {\n    icon {\n      ...icon\n    }\n    text {\n      ...detailsRichText\n    }\n    subText {\n      ...carPhrase\n    }\n    action {\n      ...carAction\n    }\n  }\n  ... on LocationRecommendationCard {\n    icon {\n      ...icon\n    }\n    location {\n      ...detailsRichText\n    }\n    city {\n      ...carPhrase\n    }\n    distanceText {\n      ...carPhrase\n    }\n    action {\n      ...carAction\n    }\n    pickUpLocation {\n      ...carSearchLocation\n    }\n  }\n  ... on PartnerRecommendationCard {\n    icon {\n      ...icon\n    }\n    action {\n      ...carAction\n    }\n    analytics {\n      ...analytics\n    }\n    image {\n      ...image\n    }\n    title {\n      ...carPhrase\n    }\n    subText {\n      ...carPhrase\n    }\n    button {\n      ...carActionableItem\n    }\n    dialog {\n      ... on PartnerRecommendationDialog {\n        title {\n          ...carPhrase\n        }\n        subTitle {\n          ...carPhrase\n        }\n        text {\n          ...carPhrase\n        }\n        button {\n          ...carActionableItem\n        }\n        closeDialog {\n          ...carAction\n        }\n        content {\n          ... on PartnerRecommendationDialogContent {\n            title {\n              ...carPhrase\n            }\n            body {\n              ...carPhrase\n            }\n            confidenceMessage {\n              ...carPhrase\n            }\n          }\n        }\n        image {\n          ...image\n        }\n      }\n    }\n  }\n  ... on AlternateRecommendationCard {\n    icon {\n      ...icon\n    }\n    action {\n      ...carAction\n    }\n    analytics {\n      ...analytics\n    }\n    image {\n      ...image\n    }\n    title {\n      ...carPhrase\n    }\n    subText {\n      ...carPhrase\n    }\n    button {\n      ...carActionableItem\n    }\n  }\n  ... on LimitedResultMessageOnRecommendationCard {\n    icon {\n      ...icon\n    }\n    action {\n      ...carAction\n    }\n    recommendationDialog {\n      title\n      buttonText\n      text\n      content {\n        header {\n          ...carPhrase\n        }\n        body {\n          title {\n            ...carPhrase\n          }\n          body {\n            ...carPhrase\n          }\n        }\n        footer {\n          ...carPhrase\n        }\n      }\n    }\n  }\n}\n\nfragment carSearchLocation on CarSearchLocation {\n  shortName\n  fullName\n  regionId\n}\n\nfragment image on Image {\n  description\n  url\n}\n\nfragment feature on VehicleFeature {\n  icon {\n    ...icon\n  }\n  text\n  info {\n    vehicleFeatureDialog {\n      title\n      text\n      buttonText\n    }\n    carActionableItem {\n      ...carActionableItem\n    }\n  }\n}\n\nfragment carOfferVendorLocationInfo on CarOfferVendorLocationInfo {\n  locationId\n  placeId\n  icon {\n    ...icon\n  }\n  text\n  locationSubInfo\n}\n\nfragment offerPriceSummary on CarPriceSummary {\n  discountBadge {\n    ...badge\n  }\n  lead {\n    ...priceInfo\n  }\n  total {\n    ...priceInfo\n  }\n  strikeThroughFirst\n  loyaltyPointsOption {\n    formattedPoints\n    leadingCaption\n    pointsFirst\n    pointsAmount {\n      raw\n      formatted\n    }\n  }\n  accessibility\n  reference {\n    additionalInfo\n    price {\n      ...money\n    }\n    qualifier\n    openDialogAction {\n      ...carAction\n    }\n    dialogContent {\n      text\n      buttonText\n    }\n  }\n  paymentInfo {\n    icon {\n      ...icon\n    }\n    text\n    additionalPaymentInfo\n  }\n  priceAdditionalInfo\n}\n\nfragment priceInfo on CarPriceInfo {\n  price {\n    ...money\n  }\n  accessibility\n  qualifier\n  formattedValue\n}\n\nfragment money on Money {\n  amount\n  formatted\n  currencyInfo {\n    code\n    name\n    symbol\n  }\n}\n\nfragment TripsSaveCarOfferAttributesFragment on TripsSaveCarOfferAttributes {\n  __typename\n  categoryCode\n  fuelAcCode\n  offerToken\n  searchCriteria {\n    dropOffDateTime {\n      ...DateTimeFragment\n    }\n    dropOffLocation {\n      ...CarRentalLocationFragment\n    }\n    pickUpDateTime {\n      ...DateTimeFragment\n    }\n    pickUpLocation {\n      ...CarRentalLocationFragment\n    }\n  }\n  transmissionDriveCode\n  typeCode\n  vendorCode\n}\n\nfragment DateTimeFragment on DateTime {\n  day\n  hour\n  minute\n  month\n  second\n  year\n}\n\nfragment CarRentalLocationFragment on CarRentalLocation {\n  airportCode\n  coordinates {\n    ...CoordinatesFragment\n  }\n  isExactLocationSearch\n  regionId\n  searchTerm\n}\n\nfragment CoordinatesFragment on Coordinates {\n  latitude\n  longitude\n}\n\nfragment TripsSaveStayAttributesFragment on TripsSaveStayAttributes {\n  __typename\n  checkInDate {\n    ...DateFragment\n  }\n  checkoutDate {\n    ...DateFragment\n  }\n  regionId\n  roomConfiguration {\n    numberOfAdults\n    childAges\n  }\n}\n\nfragment DateFragment on Date {\n  day\n  month\n  year\n}\n\nfragment TripsSaveActivityAttributesFragment on TripsSaveActivityAttributes {\n  __typename\n  regionId\n  dateRange {\n    start {\n      ...DateFragment\n    }\n    end {\n      ...DateFragment\n    }\n  }\n}\n\nfragment TripsSaveFlightSearchAttributesFragment on TripsSaveFlightSearchAttributes {\n  __typename\n  searchCriteria {\n    primary {\n      journeyCriterias {\n        arrivalDate {\n          ...DateFragment\n        }\n        departureDate {\n          ...DateFragment\n        }\n        destination\n        destinationAirportLocationType\n        origin\n        originAirportLocationType\n      }\n      searchPreferences {\n        advancedFilters\n        airline\n        cabinClass\n      }\n      travelers {\n        age\n        type\n      }\n      tripType\n    }\n    secondary {\n      booleans {\n        id\n        value\n      }\n      counts {\n        id\n        value\n      }\n      dates {\n        id\n        value {\n          ...DateFragment\n        }\n      }\n      ranges {\n        id\n        min\n        max\n      }\n      selections {\n        id\n        value\n      }\n    }\n  }\n}\n\nfragment TripsSaveItemPropertiesFragment on TripsSaveItemProperties {\n  accessibility\n  analytics {\n    referrerId\n    linkName\n    uisPrimeMessages {\n      messageContent\n      schemaName\n    }\n  }\n  adaptexSuccessCampaignIds {\n    ...AdaptexCampaignTrackingDetailFragment\n  }\n  label\n}\n\nfragment AdaptexCampaignTrackingDetailFragment on AdaptexCampaignTrackingDetail {\n  campaignId\n  eventTarget\n}\n\nfragment SingleSelectionFragment on ShoppingSelectionField {\n  primary\n  secondary\n  options {\n    ...FilterOption\n  }\n  expando {\n    ...Expando\n  }\n}\n\nfragment FilterOption on ShoppingSelectableFilterOption {\n  id\n  value\n  primary\n  secondary\n  description\n  accessibility\n  selected\n  disabled\n  icon {\n    ...icon\n  }\n  analytics {\n    ...clientSideAnalytics\n  }\n}\n\nfragment clientSideAnalytics on ClientSideAnalytics {\n  linkName\n  referrerId\n}\n\nfragment Expando on ShoppingSelectionExpando {\n  expandLabel\n  collapseLabel\n  visible\n  threshold\n  minimalHeight\n  analytics {\n    ...clientSideAnalytics\n  }\n}\n\nfragment MultiSelectionFragment on ShoppingMultiSelectionField {\n  primary\n  primaryIcon {\n    ...icon\n  }\n  secondary\n  options {\n    ...FilterOption\n  }\n  expando {\n    ...Expando\n  }\n}\n\nfragment searchUserFeedback on UserFeedback {\n  userSurveyTitle\n  options {\n    inputHeading\n    inputTextPlaceholder\n    option {\n      ...carActionableItem\n    }\n  }\n  submitConfirmation\n  submit {\n    ...carActionableItem\n  }\n}\n\nfragment coordinates on Coordinates {\n  latitude\n  longitude\n}\n',
        'variables': {
            'context': {
                'siteId': domain_details['siteId'],
                'locale': domain_details['locale'],
                'eapid': 0,
                'tpid': domain_details['siteId'],
                'currency': domain_details['currency'],
                'device': {'type': 'DESKTOP'},
                'identity': {'duaid': str(uuid4()), 'authState': 'ANONYMOUS'},
                'privacyTrackingState': 'CAN_NOT_TRACK',
                'debugContext': {'abacusOverrides': []},
            },
            'primaryCarSearchCriteria': {
                'pickUpLocation': {
                    'searchTerm': qs_dict['locn'][0],
                    'regionId': qs_dict['dpln'][0],
                    'isExactLocationSearch': False,
                },
                'pickUpDateTime': pickup,
                'dropOffDateTime': dropoff,
            },
            'secondaryCriteria': {
                'booleans': [{'id': 'SALES_UNLOCKED', 'value': False}],
                'selections': selections,
            },
            'shoppingContext': None,
        },
        'operationName': 'CarSearchV3',
    }

    return payload


def make_detail_payload_from_url(url):
    parts = urllib.parse.urlparse(url)
    qs = urllib.parse.parse_qs(parts.query)
    def get(key, default=''):
        return qs.get(key, [default])[0]

    cont_keys = [
        'totalPriceShown', 'referenceTotalShown', 'referenceDailyPriceShown',
        'dailyPriceShown', 'offerQualifiers', 'avgCatPR', 'searchKey',
        'dpln', 'drid1', 'locn', 'loc2', 'time1', 'time2', 'date1', 'date2',
        'needAncillaryBundles', 'period', 'isOffAirport', 'isTravelApiSearch',
        'isCaliforniaUser', 'offerSourceId', 'searchUrl'
    ]
    orig_keys = [
        'avgCatPR', 'comparableDealsTkn', 'dailyPriceShown', 'date1', 'date2',
        'dpln', 'isCaliforniaUser', 'isOffAirport', 'isTravelApiSearch',
        'locn', 'offerSourceId', 'period', 'piid', 'searchUrl',
        'selAPLoc', 'selCC', 'selCap', 'selOpt', 'selPR', 'selPickup',
        'selTRtr', 'selVen', 'showComparableDeals', 'time1', 'time2', 'totalPriceShown'
    ]

    continuation = '&'.join(f"{k}={get(k, 'undefined')}" for k in cont_keys)
    original = '&'.join(f"{k}={get(k, 'undefined')}" for k in orig_keys)

    domain_details = DOMAIN_CONFIG[parts.netloc.replace('www.','')]
    
    payload = {
        'query': 'query CarDetail($context: ContextInput!, $carDetailContext: CarDetailContextInput!) {\n  carDetail(context: $context, carDetailContext: $carDetailContext) {\n    detailsNavTabs {\n      navTabs {\n        name\n        analytics {\n          ...detailAnalytics\n        }\n      }\n    }\n    reviewsSummary {\n      title\n      dialogCloseIconLabel\n      recommendedRate\n      recommendedText\n      topReviews\n      superlative\n      location\n      actionableVerifiedRatingsCountMsg {\n        ...detailCarDialogConfidenceMessage\n      }\n      theme\n      dialogTrigger {\n        ...detailActionableItem\n      }\n      dialogContent {\n        heading\n        description\n        totalRatings\n        disclaimerTitle\n        disclaimerFullDescription\n        disclaimerLink {\n          ...detailActionableItem\n        }\n        userFeedback {\n          ...userFeedback\n        }\n        reviewBreakdown {\n          heading\n          description\n          percentage\n          score\n        }\n        reviewsSeeMoreAction {\n          text\n          analytics {\n            ...detailAnalytics\n          }\n        }\n        reviews {\n          text\n          rentalDuration\n          author\n          classificationName\n          expandButton {\n            expandButton\n            collapseButton\n          }\n          submissionTime\n          themes {\n            icon {\n              id\n            }\n            label\n          }\n        }\n      }\n    }\n    deal {\n      ...detailsMessagingCard\n    }\n    easeCancel {\n      ...detailsMessagingCard\n    }\n    signInBanner {\n      ...detailsMessagingCard\n    }\n    oneKeyInfo {\n      ...detailBadge\n    }\n    isTravelApiPath\n    oneKeyDetails {\n      earnBanner {\n        ...detailBadge\n      }\n      isOfferEligibleForBurn\n      isOneKeyEnrolled\n      analytics {\n        ...detailAnalytics\n      }\n    }\n    priceAlert {\n      ...detailsMessagingCard\n    }\n    saleUnlocked {\n      ...detailsMessagingCard\n    }\n    dropOffCharge {\n      ...detailsMessagingCard\n    }\n    vehicle {\n      image {\n        ...detailImage\n      }\n      ecoFriendlyFuel {\n        ... on CarsRichText {\n          value\n          style\n          theme\n        }\n      }\n      category\n      categoryIcon {\n        ...detailIcon\n      }\n      description\n      attributes {\n        ...detailFeature\n      }\n      features {\n        ...detailFeature\n      }\n      fuelInfo {\n        ...detailFeature\n      }\n    }\n    vendor {\n      image {\n        ...detailImage\n      }\n    }\n    rentalLocations {\n      title\n      isLocationDataMerged\n      pickUpLocation {\n        ...carRentalLocationDetail\n      }\n      dropOffLocation {\n        ...carRentalLocationDetail\n      }\n      pickupRequirement {\n        ...carPickupRequirementDetail\n      }\n      pickUpLocationInstructions {\n        description\n        title\n      }\n      pickupRequirementDetailsForSupplier {\n        text\n        title\n      }\n    }\n    telesales {\n      label\n      phoneNumberLink {\n        ...detailActionableItem\n      }\n    }\n    tripsSaveItemWrapper {\n      tripsSaveItem {\n        initialChecked\n        itemId\n        source\n        attributes {\n          ...TripsSaveCarOfferAttributesFragment\n          ...TripsSaveStayAttributesFragment\n          ...TripsSaveActivityAttributesFragment\n          ...TripsSaveFlightSearchAttributesFragment\n        }\n        save {\n          ...TripsSaveItemPropertiesFragment\n        }\n        remove {\n          ...TripsSaveItemPropertiesFragment\n        }\n      }\n      variant\n    }\n    promotions {\n      icon {\n        ...detailIcon\n      }\n      text\n      additionalInfo\n    }\n    inclusionsDetail {\n      title\n      text\n      inclusions {\n        icon {\n          ...detailIcon\n        }\n        title\n        summary\n        description\n        analytics {\n          ...detailAnalytics\n        }\n        infos {\n          ...detailCarPhrase\n        }\n      }\n    }\n    availableAccessories {\n      title\n      description\n      accessories {\n        id\n        name\n        price\n        pricePeriod\n        selectionState\n        analytics {\n          ...detailAnalytics\n        }\n        accessibility\n        token\n      }\n    }\n    importantInfo {\n      title\n      infos\n      importantInfoItems {\n        name\n        subtext\n        description\n        analytics {\n          ...detailAnalytics\n        }\n      }\n      rulesAndRestrictions {\n        ...detailActionableItem\n      }\n    }\n    actionableConfidenceMessages {\n      ...detailCarPhrase\n    }\n    paymentReassuranceMessage {\n      value\n    }\n    pairConfidenceMessages {\n      ...detailCarPhrase\n    }\n    additionalBenefits {\n      headingText\n      benefits {\n        ...detailCarPhrase\n      }\n    }\n    priceDetails {\n      title\n      closeAction {\n        ...detailAction\n      }\n      closeIcon {\n        ...detailIcon\n      }\n      breakupSection {\n        ...carBreakupComponent\n      }\n      summary {\n        title\n        total\n        lineItems {\n          ...carBreakupLineItem\n        }\n        notIncludedInTotal {\n          ...carBreakupComponent\n        }\n      }\n      priceDetailsButton {\n        ...detailActionableItem\n      }\n    }\n    priceSummary {\n      lead {\n        ...detailPriceInfo\n      }\n      total {\n        ...detailPriceInfo\n      }\n      strikeThroughFirst\n      loyaltyPointsOption {\n        formattedPoints\n        leadingCaption\n        pointsFirst\n        pointsAmount {\n          raw\n          formatted\n        }\n      }\n      reference {\n        additionalInfo\n        price {\n          ...detailMoney\n        }\n        qualifier\n        openDialogAction {\n          ...detailAction\n        }\n        dialogContent {\n          text\n          buttonText\n        }\n      }\n      paymentInfo {\n        icon {\n          ...detailIcon\n        }\n        text\n        additionalPaymentInfo\n      }\n      discountBadge {\n        ...detailBadge\n      }\n      priceAdditionalInfo\n      accessibility\n      floatingCTAPriceDetailsAnalytics {\n        ...detailAnalytics\n      }\n      floatingCTAReserveButtonAnalytics {\n        ...detailAnalytics\n      }\n    }\n    reserveAction {\n      ...detailActionableItem\n    }\n    reserveButtonAction {\n      ...detailCarPhrase\n    }\n    shareFeedbackAction {\n      text\n      button {\n        ...detailActionableItem\n      }\n    }\n    loyaltyInfo {\n      ...detailCarPhrase\n    }\n    variantsSummary {\n      title\n      variants {\n        title\n      }\n    }\n    carSearchLink {\n      ...detailActionableItem\n    }\n    offerBadges {\n      ...detailBadge\n    }\n    detailSummary {\n      pageTitle\n    }\n    onlineCheckInInfo {\n      icon {\n        ...detailIcon\n      }\n      title\n      infos {\n        ...detailCarPhrase\n      }\n    }\n    skipTheCounterInfo {\n      icon {\n        ...detailIcon\n      }\n      title\n      infos {\n        ...detailCarPhrase\n      }\n    }\n    enhancedCleanlinessInfo {\n      title\n      infos {\n        icon {\n          ...detailIcon\n        }\n        text\n      }\n      seeAllAction {\n        ...detailActionableItem\n      }\n      vendorCleanlinessBadge {\n        value\n      }\n      infoProviderText\n      dialog {\n        images {\n          value\n        }\n        title\n        description\n        content {\n          title {\n            icon {\n              ...detailIcon\n            }\n            text\n          }\n          infos\n        }\n        carouselButtonAllyStrings\n      }\n    }\n    adsTargetingData {\n      uuid\n      siteId\n      pageName\n      origin\n      dest\n      locResolver\n      dateStart\n      dateEnd\n      adProvider\n    }\n    rentalProtectionInfo {\n      title\n      rentalProtectionCard {\n        ...rentalProtectionCard\n      }\n    }\n    directFeedbackListing {\n      ...directFeedbackListing\n    }\n    carOfferToken\n  }\n}\n\nfragment detailAnalytics on CarAnalytics {\n  linkName\n  referrerId\n}\n\nfragment detailCarDialogConfidenceMessage on CarDialogConfidenceMessage {\n  text\n  icon {\n    ...detailIcon\n  }\n  openDialogAction {\n    ...detailAction\n  }\n  dialogContent {\n    title\n    text\n    buttonText\n  }\n  iconMobileRender\n  theme\n}\n\nfragment detailIcon on Icon {\n  description\n  id\n  size\n  withBackground\n  spotLight\n}\n\nfragment detailAction on CarAction {\n  actionType\n  accessibility\n  analytics {\n    ...detailAnalytics\n  }\n}\n\nfragment detailActionableItem on CarActionableItem {\n  url {\n    value\n    relativePath\n  }\n  action {\n    ...detailAction\n  }\n  text\n  icon {\n    ...detailIcon\n  }\n  tel {\n    phoneNumber\n    value\n  }\n}\n\nfragment userFeedback on UserFeedback {\n  userSurveyTitle\n  options {\n    inputHeading\n    inputTextPlaceholder\n    option {\n      ...detailActionableItem\n    }\n  }\n  submitConfirmation\n  submit {\n    ...detailActionableItem\n  }\n}\n\nfragment detailsMessagingCard on CarMessagingCard {\n  title\n  cardTitle {\n    ...detailCarPhrase\n  }\n  description\n  descriptions\n  cardDescriptions {\n    ...detailCarPhrase\n  }\n  mark\n  image {\n    description\n    url\n  }\n  illustrationURL {\n    value\n  }\n  icon {\n    ...detailIcon\n  }\n  badge {\n    ...detailBadge\n  }\n  links {\n    text\n    url {\n      value\n      relativePath\n    }\n    icon {\n      ...detailIcon\n    }\n    action {\n      actionType\n      analytics {\n        linkName\n        referrerId\n      }\n    }\n  }\n  dialog {\n    title\n    buttonText\n    text\n    type\n    content {\n      header {\n        ...detailCarPhrase\n      }\n      body {\n        title {\n          ...detailCarPhrase\n        }\n        body {\n          ...detailCarPhrase\n        }\n      }\n      footer {\n        ...detailCarPhrase\n      }\n    }\n  }\n  carRecommendations {\n    ...detailCarRecommendations\n  }\n  analytics {\n    ...detailAnalytics\n  }\n  linkPosition\n  clickstreamAnalytics\n}\n\nfragment detailCarPhrase on CarPhrase {\n  __typename\n  ... on CarPhraseText {\n    text\n  }\n  ... on CarPhrasePairText {\n    richText {\n      ...detailsRichText\n    }\n    richSubText {\n      ...detailsRichText\n    }\n  }\n  ... on CarPhraseIconText {\n    text\n    icon {\n      ...detailIcon\n    }\n  }\n  ... on CarActionableItem {\n    ...detailActionableItem\n  }\n  ... on CarDialogConfidenceMessage {\n    ...detailCarDialogConfidenceMessage\n  }\n  ... on CarsRichText {\n    value\n    style\n    theme\n  }\n  ... on CarPhraseMark {\n    text\n    name\n    url {\n      value\n      relativePath\n    }\n    description\n  }\n  ... on CarActionableItemForSignin {\n    memberSignInDialog {\n      actionDialog {\n        __typename\n        footer {\n          __typename\n          buttons {\n            ...tertiaryButton\n            ...primaryButton\n          }\n        }\n        closeAnalytics {\n          linkName\n          referrerId\n        }\n      }\n      dialogContent\n      title\n      graphic {\n        ...UIGraphicFragment\n      }\n      triggerMessage {\n        accessibility\n        label\n        __typename\n      }\n    }\n  }\n}\n\nfragment detailsRichText on CarsRichText {\n  value\n  theme\n  style\n}\n\nfragment tertiaryButton on UITertiaryButton {\n  __typename\n  accessibility\n  analytics {\n    referrerId\n    linkName\n  }\n  egdsElementId\n  disabled\n  icon {\n    id\n    size\n  }\n  primary\n  action {\n    ... on UILinkAction {\n      __typename\n      resource {\n        value\n        __typename\n      }\n      analytics {\n        referrerId\n        linkName\n      }\n    }\n  }\n}\n\nfragment primaryButton on UIPrimaryButton {\n  __typename\n  disabled\n  primary\n  accessibility\n  icon {\n    __typename\n  }\n  action {\n    ...linkAction\n  }\n  analytics {\n    __typename\n    linkName\n    referrerId\n    uisPrimeMessages {\n      messageContent\n      schemaName\n    }\n  }\n}\n\nfragment linkAction on UILinkAction {\n  __typename\n  resource {\n    value\n    __typename\n  }\n  analytics {\n    linkName\n    referrerId\n    __typename\n  }\n}\n\nfragment UIGraphicFragment on UIGraphic {\n  ... on Icon {\n    ...IconFragment\n  }\n  ... on Mark {\n    ...MarkFragment\n  }\n  ... on Illustration {\n    ...IllustrationFragment\n  }\n  __typename\n}\n\nfragment IconFragment on Icon {\n  description\n  id\n  iconSize: size\n  iconTheme: theme\n  title\n  withBackground\n  spotLight\n  __typename\n}\n\nfragment MarkFragment on Mark {\n  description\n  id\n  markSize: size\n  url {\n    ... on HttpURI {\n      relativePath\n      value\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment IllustrationFragment on Illustration {\n  description\n  id\n  link: url\n  __typename\n}\n\nfragment detailBadge on CarOfferBadge {\n  icon {\n    id\n  }\n  mark {\n    id\n    url {\n      value\n    }\n  }\n  text\n  theme\n}\n\nfragment detailCarRecommendations on CarRecommendations {\n  __typename\n  heading\n  analytics {\n    linkName\n    referrerId\n  }\n  carRecommendationsCards {\n    ...detailCarRecommendationCard\n  }\n}\n\nfragment detailCarRecommendationCard on CarRecommendationCard {\n  __typename\n  icon {\n    ...detailIcon\n  }\n  action {\n    ...detailAction\n  }\n  ... on DateTimeRecommendationCard {\n    icon {\n      ...detailIcon\n    }\n    text {\n      ...detailsRichText\n    }\n    subText {\n      ...detailCarPhrase\n    }\n    action {\n      ...detailAction\n    }\n  }\n  ... on LocationRecommendationCard {\n    icon {\n      ...detailIcon\n    }\n    location {\n      ...detailsRichText\n    }\n    city {\n      ...detailCarPhrase\n    }\n    distanceText {\n      ...detailCarPhrase\n    }\n    action {\n      ...detailAction\n    }\n    pickUpLocation {\n      ...detailCarSearchLocation\n    }\n  }\n  ... on PartnerRecommendationCard {\n    icon {\n      ...detailIcon\n    }\n    action {\n      ...detailAction\n    }\n    analytics {\n      ...detailAnalytics\n    }\n    image {\n      ...detailImage\n    }\n    title {\n      ...detailCarPhrase\n    }\n    subText {\n      ...detailCarPhrase\n    }\n    button {\n      ...detailActionableItem\n    }\n    dialog {\n      ... on PartnerRecommendationDialog {\n        title {\n          ...detailCarPhrase\n        }\n        subTitle {\n          ...detailCarPhrase\n        }\n        text {\n          ...detailCarPhrase\n        }\n        button {\n          ...detailActionableItem\n        }\n        closeDialog {\n          ...detailAction\n        }\n        content {\n          ... on PartnerRecommendationDialogContent {\n            title {\n              ...detailCarPhrase\n            }\n            body {\n              ...detailCarPhrase\n            }\n            confidenceMessage {\n              ...detailCarPhrase\n            }\n          }\n        }\n        image {\n          ...detailImage\n        }\n      }\n    }\n  }\n  ... on LimitedResultMessageOnRecommendationCard {\n    icon {\n      ...detailIcon\n    }\n    action {\n      ...detailAction\n    }\n    recommendationDialog {\n      title\n      buttonText\n      text\n      content {\n        header {\n          ...detailCarPhrase\n        }\n        body {\n          title {\n            ...detailCarPhrase\n          }\n          body {\n            ...detailCarPhrase\n          }\n        }\n        footer {\n          ...detailCarPhrase\n        }\n      }\n    }\n  }\n}\n\nfragment detailCarSearchLocation on CarSearchLocation {\n  shortName\n  fullName\n  regionId\n}\n\nfragment detailImage on Image {\n  description\n  url\n}\n\nfragment detailFeature on VehicleFeature {\n  icon {\n    ...detailIcon\n  }\n  text\n  info {\n    vehicleFeatureDialog {\n      title\n      text\n      buttonText\n      closeButtonLabel\n    }\n    carActionableItem {\n      ...detailActionableItem\n    }\n    carActionableItemOnClose {\n      ...detailActionableItem\n    }\n  }\n}\n\nfragment carRentalLocationDetail on CarRentalLocationDetail {\n  title\n  locationTimeLine\n  showLocationDetail\n  dateTime {\n    ...carVendorLocationInfo\n  }\n  address {\n    ...carVendorLocationInfo\n  }\n  hoursOfOperation {\n    ...carVendorLocationInfo\n  }\n  instruction {\n    ...carVendorLocationInfo\n  }\n  mapData {\n    ...carDetailsMap\n  }\n  analytics {\n    ...detailAnalytics\n  }\n  analyticsOnClose {\n    ...detailAnalytics\n  }\n}\n\nfragment carVendorLocationInfo on CarVendorLocationInfo {\n  icon {\n    ...detailIcon\n  }\n  text\n  locationSubInfo\n  locationSubInfoMap {\n    text\n    accessibility\n  }\n}\n\nfragment carDetailsMap on CarDetailsMap {\n  title\n  dialogAccessibility\n  closeButton {\n    ...detailActionableItem\n  }\n  center {\n    ...detailsCoordinates\n  }\n  bounds {\n    ...carDetailsMapBounds\n  }\n  zoomLevel\n  marker {\n    ...carDetailsCardMapMarker\n  }\n  viewInMapButton {\n    ...detailActionableItem\n  }\n}\n\nfragment detailsCoordinates on Coordinates {\n  latitude\n  longitude\n}\n\nfragment carDetailsMapBounds on CarDetailsMapBounds {\n  northeast {\n    ...detailsCoordinates\n  }\n  southwest {\n    ...detailsCoordinates\n  }\n}\n\nfragment carDetailsCardMapMarker on CarDetailsCardMapMarker {\n  itemCard {\n    ...carDetailsMapLocationCard\n  }\n  type\n  icon {\n    ...detailIcon\n  }\n  coordinates {\n    ...detailsCoordinates\n  }\n  action {\n    ...detailAction\n  }\n  labelText\n}\n\nfragment carDetailsMapLocationCard on CarDetailsMapLocationCard {\n  vendorImage {\n    ...detailImage\n  }\n  vendorName\n  addressText\n  locationSubInfo\n  getDirectionButton {\n    ...detailActionableItem\n  }\n  closeButton {\n    ...detailActionableItem\n  }\n}\n\nfragment carPickupRequirementDetail on CarPickupRequirementDetail {\n  title\n  licenseRequirement {\n    ...carPickupRequirementInfo\n  }\n  cardRequirement {\n    ...carPickupRequirementInfo\n  }\n  pickUpRequirementAnalytics {\n    ...detailAnalytics\n  }\n}\n\nfragment carPickupRequirementInfo on CarPickupRequirementInfo {\n  icon {\n    ...detailIcon\n  }\n  text\n  action {\n    ...detailActionableItem\n  }\n}\n\nfragment TripsSaveCarOfferAttributesFragment on TripsSaveCarOfferAttributes {\n  __typename\n  categoryCode\n  fuelAcCode\n  offerToken\n  searchCriteria {\n    dropOffDateTime {\n      ...DateTimeFragment\n    }\n    dropOffLocation {\n      ...CarRentalLocationFragment\n    }\n    pickUpDateTime {\n      ...DateTimeFragment\n    }\n    pickUpLocation {\n      ...CarRentalLocationFragment\n    }\n  }\n  transmissionDriveCode\n  typeCode\n  vendorCode\n}\n\nfragment DateTimeFragment on DateTime {\n  day\n  hour\n  minute\n  month\n  second\n  year\n}\n\nfragment CarRentalLocationFragment on CarRentalLocation {\n  airportCode\n  coordinates {\n    ...CoordinatesFragment\n  }\n  isExactLocationSearch\n  regionId\n  searchTerm\n}\n\nfragment CoordinatesFragment on Coordinates {\n  latitude\n  longitude\n}\n\nfragment TripsSaveStayAttributesFragment on TripsSaveStayAttributes {\n  __typename\n  checkInDate {\n    ...DateFragment\n  }\n  checkoutDate {\n    ...DateFragment\n  }\n  regionId\n  roomConfiguration {\n    numberOfAdults\n    childAges\n  }\n}\n\nfragment DateFragment on Date {\n  day\n  month\n  year\n}\n\nfragment TripsSaveActivityAttributesFragment on TripsSaveActivityAttributes {\n  __typename\n  regionId\n  dateRange {\n    start {\n      ...DateFragment\n    }\n    end {\n      ...DateFragment\n    }\n  }\n}\n\nfragment TripsSaveFlightSearchAttributesFragment on TripsSaveFlightSearchAttributes {\n  __typename\n  searchCriteria {\n    primary {\n      journeyCriterias {\n        arrivalDate {\n          ...DateFragment\n        }\n        departureDate {\n          ...DateFragment\n        }\n        destination\n        destinationAirportLocationType\n        origin\n        originAirportLocationType\n      }\n      searchPreferences {\n        advancedFilters\n        airline\n        cabinClass\n      }\n      travelers {\n        age\n        type\n      }\n      tripType\n    }\n    secondary {\n      booleans {\n        id\n        value\n      }\n      counts {\n        id\n        value\n      }\n      dates {\n        id\n        value {\n          ...DateFragment\n        }\n      }\n      ranges {\n        id\n        min\n        max\n      }\n      selections {\n        id\n        value\n      }\n    }\n  }\n}\n\nfragment TripsSaveItemPropertiesFragment on TripsSaveItemProperties {\n  accessibility\n  analytics {\n    referrerId\n    linkName\n    uisPrimeMessages {\n      messageContent\n      schemaName\n    }\n  }\n  adaptexSuccessCampaignIds {\n    ...AdaptexCampaignTrackingDetailFragment\n  }\n  label\n}\n\nfragment AdaptexCampaignTrackingDetailFragment on AdaptexCampaignTrackingDetail {\n  campaignId\n  eventTarget\n}\n\nfragment carBreakupComponent on CarBreakupComponent {\n  id\n  title\n  lineItems {\n    ...carBreakupLineItem\n  }\n}\n\nfragment carBreakupLineItem on CarBreakupLineItem {\n  icon {\n    ...detailIcon\n  }\n  mark {\n    id\n    url {\n      value\n    }\n  }\n  dialogContent {\n    commonDialog {\n      title\n      text\n      buttonText\n    }\n    breakupContent {\n      ...carPriceBreakupDialogLineItem\n    }\n  }\n  openDialogAction {\n    ...detailAction\n  }\n  text\n  accessibility\n  subText\n  value\n  richValue {\n    ...detailsRichText\n  }\n  theme\n}\n\nfragment carPriceBreakupDialogLineItem on CarBreakupLineItem {\n  text\n  value\n  subText\n}\n\nfragment detailPriceInfo on CarPriceInfo {\n  price {\n    ...detailMoney\n  }\n  accessibility\n  qualifier\n  formattedValue\n}\n\nfragment detailMoney on Money {\n  amount\n  formatted\n  currencyInfo {\n    code\n    name\n    symbol\n  }\n}\n\nfragment rentalProtectionCard on RentalProtectionCard {\n  title\n  infos {\n    icon {\n      ...detailIcon\n    }\n    text\n  }\n  seeDetailsAction {\n    ...detailActionableItem\n  }\n  priceSummary\n  pricePeriod\n  offerBadge {\n    ...detailBadge\n  }\n  dialog {\n    title\n    description\n    content {\n      title\n      description {\n        icon {\n          ...detailIcon\n        }\n        text\n      }\n    }\n  }\n  selected\n  clickAction {\n    ...detailActionableItem\n  }\n}\n\nfragment directFeedbackListing on DirectFeedbackListing {\n  callToAction {\n    promptId\n    contextValues {\n      key\n      value\n    }\n    callToAction {\n      ...tertiaryButton\n    }\n  }\n}\n',
        'variables': {
            'context': {
                'siteId': domain_details['siteId'],
                'locale': domain_details['locale'],
                'eapid': 0,
                'tpid': domain_details['siteId'],
                'currency': domain_details['currency'],
                'device': {'type': 'DESKTOP'},
                'identity': {'duaid': str(uuid4()), 'authState': 'ANONYMOUS'},
                'privacyTrackingState': 'CAN_TRACK',
                'debugContext': {'abacusOverrides': []},
            },
            'carDetailContext': {
                'carOfferToken': get('piid'),
                'rewardPointsSelection': 'DO_NOT_APPLY_REWARD_POINTS',
                'selectedAccessories': [],
                'continuationContextualId': continuation,
                'optionToken': None,
                'optionAction': None,
                'originalDeeplink': original,
            },
        },
        'operationName': 'CarDetail',
    }
    return payload


async def fetch_car_search_response(search_url,max_retries=3):
    netloc = urllib.parse.urlparse(search_url).netloc
    payload = make_search_payload_from_url(search_url)
    headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'max-age=0',
        'client-info': 'bernie-cars-shopping-web,pwa,us-east-1',
        'content-type': 'application/json',
        'origin': f'https://{netloc}',
        'priority': 'u=1, i',
        'referer': search_url,
        "sec-ch-ua": "\"Google Chrome\";v=\"131\", \"Chromium\";v=\"131\", \"Not_A Brand\";v=\"24\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Sec-Fetch-Site": "?1",
        "Sec-Fetch-Mode": "same-site",
        "Sec-Fetch-User": "document",
        "Sec-Fetch-Dest": "navigate",
        'x-page-id': 'page.Car-Search,C,20',
    }
    payload = {
            "url": f"https://{netloc}/graphql",
            "method" : "POST",
            "key": 'aPQeqcC7bFvO1P7dHLRD',
            "keep_headers": True,
            **payload
        }
    
    async with AsyncClient(timeout=60) as client:
        while max_retries:
            try:
                response = await client.post("https://api.syphoon.com", headers=headers, json=payload)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                max_retries -= 1
    return None


async def fetch_car_detail_response(detail_page_url,max_retries=3):
    netloc = urllib.parse.urlparse(detail_page_url).netloc
    payload = make_detail_payload_from_url(detail_page_url)
    headers = {
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'max-age=0',
        'Client-Info': 'bernie-cars-shopping-web,pwa,us-east-1',
        'Content-Type': 'application/json',
        'Origin': f'https://{netloc}',
        'Priority': 'u=1, i',
        'Referer': detail_page_url,
        'Sec-CH-UA': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'Sec-CH-UA-Mobile': '?0',
        'Sec-CH-UA-Platform': '"Windows"',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'Sec-Fetch-Site': 'same-site',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-User': '?1',
        'Sec-Fetch-Dest': 'document',
        'X-Page-Id': 'page.Cars.Infosite.Information,C,30',
    }

    payload = {
            "url": f"https://{netloc}/graphql",
            "method" : "POST",
            "key": 'aPQeqcC7bFvO1P7dHLRD',
            "keep_headers": True,
            **payload
        }
    async with AsyncClient(timeout=60) as client:
        while max_retries:
            try:
                response = await client.post("https://api.syphoon.com", headers=headers, json=payload)
                response.raise_for_status()
                return response.json()  
            except:
                max_retries -= 1

    return None




async def expedia_internal_search_crawler(search_url, max_results = 0):
    search_response = await fetch_car_search_response(search_url)
    listings = []
    search_page_responses = []
    netloc = urllib.parse.urlparse(search_url).netloc
    if search_response:
        search_page_responses.append(search_response)
        car_list = search_response['data']['carSearchOrRecommendations']['carSearchResults']
        no_of_results = int(car_list['summary']['title'].split()[0])
        page_size = car_list['loadMoreAction']['searchPagination']['size']
        # for result in car_list['listings']:
        #     if result['__typename'] != "CarOfferCard":
        #         continue
        #     detail_page_url = f'https://{netloc}{result["infositeURL"]["relativePath"]}'
        #     listings.append(detail_page_url)

        limit = no_of_results if max_results <= 0 or max_results > no_of_results else max_results
        pages = (limit//page_size) + 1
        
        if pages>1:
            page_urls = [f"{search_url}&selPageIndex={i * page_size}" for i in range(1,pages)]
            search_tasks = [asyncio.create_task(fetch_car_search_response(url)) for url in page_urls]
            search_page_responses.extend(await asyncio.gather(*search_tasks))

        for response in search_page_responses:
            car_list = response['data']['carSearchOrRecommendations']['carSearchResults']
            for result in car_list['listings']:
                if result['__typename'] != "CarOfferCard":
                    continue
                detail_page_url = f'https://{netloc}{result["infositeURL"]["relativePath"]}'
                listings.append(detail_page_url)

        tasks = [asyncio.create_task(fetch_car_detail_response(detail_page_url)) for detail_page_url in listings[:max_results]]
        results = await asyncio.gather(*tasks)
        return [r for r in results if r]
    
    return []

async def expedia_search_crawler(search_url, max_results = 0):
    search_response = await fetch_car_search_response(search_url)
    search_page_responses = []
    if search_response:
        search_page_responses.append(search_response)
        car_list = search_response['data']['carSearchOrRecommendations']['carSearchResults']
        no_of_results = int(car_list['summary']['title'].split()[0])
        page_size = car_list['loadMoreAction']['searchPagination']['size']
        limit = no_of_results if max_results <= 0 or max_results > no_of_results else max_results
        pages = (limit//page_size) + 1
        
        if pages>1:
            page_urls = [f"{search_url}&selPageIndex={i * page_size}" for i in range(1,pages)]
            search_tasks = [asyncio.create_task(fetch_car_search_response(url)) for url in page_urls]
            search_page_responses.extend(await asyncio.gather(*search_tasks))
        return [r for r in search_page_responses if r]
    
    return []
