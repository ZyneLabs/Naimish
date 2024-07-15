from Automalluae import AutomalluaeCrawler, AutomalluaeParser_v2
from Cars24 import Cars24Crawler, Cars24Parser
from Carswitch import CarswitchCrawler, CarswitchParser
from Dubicars import DubaiCarscrawler, DubaiCarsParser
from Kavak import KavakCrawler, KavakParser
from Yallamotor import YallamotorCrawler, YallamotorParser

# crawler_funtions = [
    # AutomalluaeCrawler.crawl_urls,
    # Cars24Crawler.crawl_urls,
    # CarswitchCrawler.crawl_category,
    # DubaiCarscrawler.crawl_makers,
    # KavakCrawler.crawl_main_page,
    # YallamotorCrawler.crawl_from_brands
    # ]

# for func in crawler_funtions:
#     func.delay()


parser_functions = [
    # AutomalluaeParser_v2.start_scraper,
    Cars24Parser.start_scraper,
    CarswitchParser.start_scraper,
    DubaiCarsParser.start_scraper,
    KavakParser.start_scraper,
    YallamotorParser.start_scraper
]

for func in parser_functions:
    func.delay()