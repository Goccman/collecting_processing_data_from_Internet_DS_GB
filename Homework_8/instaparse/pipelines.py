# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface

from scrapy.utils.project import get_project_settings
import os
from scrapy.pipelines.images import ImagesPipeline
import scrapy
from pymongo import MongoClient



class InstaPhotoPipeline(ImagesPipeline):

    def get_media_requests(self, item, info):
        if item['avatar']:
            try:
                yield scrapy.Request(item['avatar'])
            except Exception as e:
                print(e)

    # переопределим путь к изображениям (images/целевой пользователь/статус отношений/file_name.jpg)
    def file_path(self, request, response=None, info=None, *, item=None):
        cat_name = item['main_acc_name']
        dir_name = item['status_name']
        file_name = item['user_name']
        return f'{cat_name}/{dir_name}/{file_name}.jpg'

    def item_completed(self, results, item, info):
        for result in [x for ok, x in results if ok]:
            path = result['path']
            slug = path.split('/')[0]
            settings = get_project_settings()
            storage = settings.get('IMAGES_STORE')

            # если пути к папке не существует-создадим её
            if not os.path.exists(os.path.join(storage, slug)):
                os.makedirs(os.path.join(storage, slug))

        if self.IMAGES_RESULT_FIELD in item.fields:
            item[self.IMAGES_RESULT_FIELD] = [x for ok, x in results if ok]
        return item


class InstaparsePipeline:

    def __init__(self):
        client = MongoClient('localhost', 27017)
        self.mongo_base = client.insta

    def process_item(self, item, spider):
        # т.к. всю информацию собрали, предварительная обработка полей не нужна,
        # будем сразу укладывать в БД
        collection = self.mongo_base[spider.name]
        collection.update(item, item, upsert=True)
        return item