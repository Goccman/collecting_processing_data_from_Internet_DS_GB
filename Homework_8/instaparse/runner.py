from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings

from instaparse.spiders.instacom import InstacomSpider
from instaparse import settings

if __name__ == '__main__':
    crawler_settings = Settings()
    crawler_settings.setmodule(settings)
    process = CrawlerProcess(settings=crawler_settings)
    person = False
    while not person:
        person = list(input(
            'Введите имя пользователя, или имена пользователей через пробел\n'
            '(например: leomessi cristiano kimkardashian): ').split())
    process.crawl(InstacomSpider, person=person)
    process.start()