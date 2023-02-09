import scrapy
import scrapy
from scrapy.http import HtmlResponse
from instaparse.items import InstaparseItem
import re
import json
from urllib.parse import urlencode
from copy import deepcopy


class InstacomSpider(scrapy.Spider):
    name = 'instacom'
    allowed_domains = ['instagram.com']
    start_urls = ['https://www.instagram.com/']
    inst_login_link = 'https://www.instagram.com/accounts/login/ajax/'
    inst_login = False  # ввести логин
    inst_password = False  # ввести пароль
    parse_user = []  # список целевых пользователей, т.е. тех, чьих подписчиков и подписки хотим собрать
    status_list = ['following',
                   'follower']  # список информации о целевом пользователе которую хотим собрать
    status_hash = ['3dec7e2c57367ef3da3d987d89f9dbc8',
                   # хэш-коды информации о целевом пользователе которую хотим собрать
                   '5aefa9893005572d237da5068082d8d5']
    graphql_url = 'https://www.instagram.com/graphql/query/'

    def __init__(self, person):
        super(InstacomSpider, self).__init__()

        self.person = person
        for name in self.person:
            self.parse_user.append(name)
        # запрос логина
        if not self.inst_login:
            self.inst_login = input('Введите ваш логин Instagram: ')
        # запрос пароля
        if not self.inst_password:
            self.inst_password = input(
                'Введите пароль(значение поля "enc_password" из запроса\n'
                ' по ссылке "https://www.instagram.com/accounts/login/ajax/"): ')

    def parse(self, response: HtmlResponse):
        csrf_token = self.fetch_csrf_token(response)
        yield scrapy.FormRequest(self.inst_login_link,
                                 method='POST',
                                 callback=self.user_login,
                                 formdata={'username': self.inst_login,
                                           'enc_password': self.inst_password,
                                           'queryParams': {},
                                           'optIntoOneTap': 'false'},
                                 headers={'x-csrftoken': csrf_token})

    def user_login(self, response: HtmlResponse):
        j_body = response.json()
        if j_body.get('authenticated'):
            for name in self.parse_user:
                yield response.follow(
                    f'/{name}/',
                    # слэш в конце чтобы не получать редирект по 301 статусу
                    callback=self.user_data_parse,
                    cb_kwargs={'username': deepcopy(name)}
                )

    # для каждого целевого пользователя будем сразу разделять запросы на сбор
    # данных по подпискам и подписчикам
    def user_data_parse(self, response: HtmlResponse, username):
        person_id = self.fetch_person_id(response.text, username)
        variables = {'id': person_id, "include_reel": 'true',
                     "fetch_mutual": 'false', 'first': 24}
        for status_name, target_hash, method in zip(self.status_list,
                                                    self.status_hash,
                                                    [self.following_parse,
                                                     self.follower_parse]):
            url_post = f'{self.graphql_url}?query_hash={target_hash}&{urlencode(variables)}'

            yield response.follow(url_post,
                                  callback=method,
                                  cb_kwargs={'variables': deepcopy(variables),
                                             'username': username,
                                             'status_name':
                                                 status_name,
                                             'target_hash':
                                                 target_hash})

    # собираем подписки
    def following_parse(self, response: HtmlResponse, variables, username,
                        status_name, target_hash):
        j_son = json.loads(response.text)
        page_info = j_son.get('data').get('user').get(
            'edge_follow').get('page_info')
        if page_info.get('has_next_page'):
            variables.update({'after': page_info.get('end_cursor')})
            url_post = f'{self.graphql_url}?query_hash={target_hash}&{urlencode(variables)}'
            yield response.follow(url_post,
                                  callback=self.following_parse,
                                  cb_kwargs={'variables': variables,
                                             'username': username,
                                             'status_name':
                                                 status_name,
                                             'target_hash':
                                                 target_hash})
        followings = j_son.get('data').get('user').get('edge_follow').get(
            'edges')
        for following in followings:
            yield InstaparseItem(
                status_name=status_name,
                main_acc_name=username,
                user_id=following.get('node').get('id'),
                user_name=following.get('node').get('username'),
                user_full_name=following.get('node').get('full_name'),
                avatar=following.get('node').get('profile_pic_url'),
                user_data=following.get('node')
            )

    # собираем подписчиков
    def follower_parse(self, response: HtmlResponse, variables, username,
                       status_name, target_hash):
        j_son = json.loads(response.text)
        page_info = j_son.get('data').get('user').get(
            'edge_followed_by').get('page_info')
        if page_info.get('has_next_page'):
            variables.update({'after': page_info.get('end_cursor')})
            url_post = f'{self.graphql_url}?query_hash={target_hash}&{urlencode(variables)}'
            yield response.follow(url_post,
                                  callback=self.follower_parse,
                                  cb_kwargs={'variables': variables,
                                             'username': username,
                                             'status_name':
                                                 status_name,
                                             'target_hash':
                                                 target_hash})
        followers = j_son.get('data').get('user').get(
            'edge_followed_by').get('edges')
        for follower in followers:
            yield InstaparseItem(
                status_name=status_name,
                main_acc_name=username,
                user_id=follower.get('node').get('id'),
                user_name=follower.get('node').get('username'),
                user_full_name=follower.get('node').get('full_name'),
                avatar=follower.get('node').get('profile_pic_url'),
                user_data=follower.get('node')
            )

    # получаем токен для авторизации
    def fetch_csrf_token(self, response: HtmlResponse):
        text = response.xpath(
            '//script[contains(text(), "csrf_token")]/text()').get()
        my_son = json.loads(text[text.find('=') + 1:-1])
        return my_son.get('config').get('csrf_token')

    # получаем ID целевого пользователя
    def fetch_person_id(self, text, username):
        matched = re.search(
            '{\"id\":\"\\d+\",\"username\":\"%s\"}' % username, text
        ).group()
        return json.loads(matched).get('id')