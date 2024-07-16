from celery import Celery

tasks = [
    'Automalluae.AutomalluaeCrawler', 'Automalluae.AutomalluaeParser_v2',
    'Cars24.Cars24Crawler', 'Cars24.Cars24Parser',
    'Carswitch.CarswitchCrawler', 'Carswitch.CarswitchParser',
    'Dubaicars.DubaiCarscrawler', 'Dubaicars.DubaiCarsParser',
    'Kavak.KavakCrawler', 'Kavak.KavakParser',
    'Yallamotor.YallamotorCrawler', 'Yallamotor.YallamotorParser',
]

celery_app = Celery('tasks', broker='redis://localhost:6379/0', include=tasks)
celery_app.conf.update(
    result_backend='redis://localhost:6379/0',
    timezone='UTC',
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    task_routes={
        'Automalluae.AutomalluaeCrawler.crawl_urls': {'queue': 'automalluae'},
        'Automalluae.AutomalluaeParser_v2.start_scraper': {'queue': 'automalluae'},
        'Automalluae.AutomalluaeParser_v2.automalluae_parser': {'queue': 'automalluae'},
        
        'Cars24.Cars24Crawler.crawl_urls': {'queue': 'cars24'},
        'Cars24.Cars24Parser.start_scraper': {'queue': 'cars24'},
        'Cars24.Cars24Parser.cars24_parser': {'queue': 'cars24'},
        
        'Carswitch.CarswitchCrawler.crawl_category': {'queue': 'carswitch'},
        'Carswitch.CarswitchCrawler.crawl_urls': {'queue': 'carswitch'},
        'Carswitch.CarswitchParser.start_scraper': {'queue': 'carswitch'},
        'Carswitch.CarswitchParser.carswitch_parser': {'queue': 'carswitch'},
        
        'Dubaicars.DubaiCarscrawler.crawl_makers': {'queue': 'dubaicars'},
        'Dubaicars.DubaiCarscrawler.check_makers_fesibility': {'queue': 'dubaicars'},
        'Dubaicars.DubaiCarscrawler.crawl_products': {'queue': 'dubaicars'},
        'Dubaicars.DubaiCarsParser.start_scraper': {'queue': 'dubaicars'},
        'Dubaicars.DubaiCarsParser.dubaicars_parser': {'queue': 'dubaicars'},
        
        'Kavak.KavakCrawler.crawl_main_page': {'queue': 'kavak'},
        'Kavak.KavakCrawler.crawl_urls': {'queue': 'kavak'},
        'Kavak.KavakParser.start_scraper': {'queue': 'kavak'},
        'Kavak.KavakParser.kavak_parser': {'queue': 'kavak'},
        
        'Yallamotor.YallamotorCrawler.crawl_page': {'queue': 'yallamotor'},
        'Yallamotor.YallamotorCrawler.crawl_urls': {'queue': 'yallamotor'},
        'Yallamotor.YallamotorParser.start_scraper': {'queue': 'yallamotor'},
        'Yallamotor.YallamotorParser.yallamotor_parser': {'queue': 'yallamotor'},
    },
    task_queues={
        'automalluae': {'exchange': 'automalluae', 'routing_key': 'automalluae'},
        'cars24': {'exchange': 'cars24', 'routing_key': 'cars24'},
        'carswitch': {'exchange': 'carswitch', 'routing_key': 'carswitch'},
        'dubicars': {'exchange': 'dubicars', 'routing_key': 'dubicars'},
        'kavak': {'exchange': 'kavak', 'routing_key': 'kavak'},
        'yallamotor': {'exchange': 'yallamotor', 'routing_key': 'yallamotor'},
    }
)