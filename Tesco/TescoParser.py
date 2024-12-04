def product_parser(html):

    product_data = {}

    soup = BeautifulSoup(html, "html.parser")

    page_json = json.loads(
        soup.select_one('script[type="application/discover+json"]').text
    )["mfe-orchestrator"]["props"]["apolloCache"]

    if not page_json:
        return None

    product_url = soup.select_one('link[rel="canonical"]').get("href")
    product_id = product_url.split("/")[-1].split("?")[0]
    product_json = page_json.get(f"MPProduct:{product_id}") or page_json.get(
        f"ProductType:{product_id}"
    )

    product_data["Record id"] = product_id
    product_data["Probe date"] = datetime.now().strftime("%Y-%m-%d")
    product_data["URL date time"] = datetime.now().isoformat()
    product_data["Producer Name"] = product_json["brandName"]
    product_data["Product Name"] = product_json["title"]
    product_data["Product URL"] = product_url

    product_data["Product attributes"] = None

    if product_json['details'].get("specifications"):
        product_data["Product attributes"] = [
            f'{item["name"]} : {item["value"]}'
            for item in product_json["details"]["specifications"][0][
                "specificationAttributes"
            ]
        ]

    product_data["Photo URL"] = product_json["defaultImageUrl"].split("?")[0]
    product_data["Price"] = product_json["price"]["actual"]

    if soup.select_one("div.ddsweb-buybox__price.ddsweb-price__container p"):
        product_data["Price_text"] = soup.select_one(
            "div.ddsweb-buybox__price.ddsweb-price__container p"
        ).text.replace("Â", "")
    else:
        product_data["Price_text"] = ""

    product_data["Price before promotion"] = None
    product_data["Price before promotion_text"] = None
    if product_json.get("promotions") and product_json["promotions"][0].get("__ref"):

        promotion_json = page_json[product_json["promotions"][0].get("__ref")]

        if promotion_json['price'] and promotion_json['price'].get("beforeDiscount"):
            product_data["Price before promotion"] = promotion_json["price"][
                "beforeDiscount"
            ]
            offer_soup = soup.select_one('div[class*="value-bar__promo-text"] span').text.lower()
            product_data["Price before promotion_text"] = (
                offer_soup
                .split("now")[0]
                .replace("was", "")
                .replace("â", "")
                .strip()
            )
            if not product_data["Price_text"]:
                product_data["Price_text"] = (
                    offer_soup.split("now")[1]
                    .replace('â','')
                    .strip()
                    )

    if product_json['reviews({"count":10,"offset":0})'].get("stats"):
        product_data["Star Rating"] = (
            product_json['reviews({"count":10,"offset":0})']
            .get("stats")
            .get("overallRating")
        )
        product_data["Reviews"] = (
            product_json['reviews({"count":10,"offset":0})']
            .get("stats")
            .get("noOfReviews")
        )

    product_data["Codes"] = " | ".join(
        [
            "baseProductId : " + product_json["baseProductId"],
            "gtin : " + product_json["gtin"],
            "tpnb : " + product_json["tpnb"],
            "tpnc : " + product_json["tpnc"],
        ]
    )

    product_data["Availability"] = "N"

    if product_json["status"] == "AvailableForSale":
        product_data["Availability"] = "Y"

    product_data["Product availability text"] = None

    if availability_text := soup.select_one(
        'div[data-auto="pdp-product-tile-messaging"] div[role="status"] span'
    ):
        product_data["Product availability text"] = availability_text.text

    product_data["Is product is sold by official seller"] = "N"
    product_data["Is product is shipped by official seller"] = "N"

    product_data["Seller name"] = None
    if product_json["seller"] and product_json["seller"].get("__ref"):
        product_data["Seller name"] = page_json[product_json["seller"].get("__ref")][
            "name"
        ]

        product_data["Is product is sold by official seller"] = "Y"
        product_data["Is product is shipped by official seller"] = "Y"


    product_data["category"] = " > ".join(
        [
            i.text
            for i in soup.select('nav[aria-label="breadcrumb"] li a')
            if i.text.strip()
        ]
    )
    product_data["Category URL"] = soup.select('nav[aria-label="breadcrumb"] li a')[
        -1
    ].get("href")

    product_data["Rich content presence"] = "Yes"
    product_data["Video presence"] = "No"
    product_data["Gallery pictures"] = len(product_json["images"]["display"])
    product_data["Gallery images URLs"] = " | ".join(
        [img["default"]["url"] for img in product_json["images"]["display"]]
    )

    return product_data
