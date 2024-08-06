walmart_product_examples = {
    'Valid Example':{
        "summary": "Valid Example",
        "description": "Valid Example",
        "value": {
            "url" : "https://www.walmart.com/ip/Straight-Talk-TCL-ION-V-32GB-Black-Prepaid-Smartphone-Locked-to-Straight-Talk/3759467724?athbdg=L1103&adsRedirect=true",
            "token" : "API_TOKEN"
        }
    }
}

amazon_prodcut_examples = {
    'Valid Example':{
        "summary": "Valid Example",
        "description": "Valid Example",
        "value": {
            "url" : "https://www.amazon.com/dp/B07D9WZ5ZM",
            "token" : "API_TOKEN"
        }
    }
    
}

bestbuy_product_examples = {
    'Valid Example':{
        "summary": "Valid Example",
        "description": "Valid Example",
        "value": {
            "url" : "https://www.bestbuy.com/site/sony-playstation-5-console/6429441.p?skuId=6429441",
            "token" : "API_TOKEN"
        }
    }
}


amazon_review_examples= {
        'without page':{
            "summary": "Without page number",
            "description": "Without page number",
            "value": {
                "domain" : "amazon.com",
                "asin" : "B07D9WZ5ZM",
                "token" : "API_TOKEN",
            }
        },
        'with page':{
            "summary": "With page number",
            "description": "With page number",
            "value": {
                "domain" : "amazon.com",
                "asin" : "B07D9WZ5ZM",
                "token" : "API_TOKEN",
                "page" : 1
            }
        },
        'with invalid page':{
            "summary": "With invalid page number",
            "description": "With invalid page number",
            "value": {
                "domain" : "amazon.com",
                "asin" : "B07D9WZ5ZM",
                "token" : "API_TOKEN",
                "page" : 0
            }
        }

    }