# Описание базы:
#   Название: "insta"
#   Коллекции: 1. "instacom"
#   Поля документов:
#       _id : уникальный индекс МонгоДБ,
#       main_acc_name : никнейм пользователя для которого собирались подписки
#       и подписчики(целевой пользователь),
#       status_name : статус взаимоотношений с целевым пользователем(подписчик
#       или подписка),
#       user_id : id подписчика/подписки,
#       user_name : никнейм подписчика/подписки,
#       user_full_name : полное имя подписчика/подписки,
#       avatar : ссылка на аватар подписчика/подписки,
#       user_data : ссылка на аватар подписчика/подписки,


# Написать запрос к базе, который вернет список подписчиков только указанного
# пользователя

from pymongo import MongoClient
from pprint import pprint

client = MongoClient('localhost', 27017)
db = client['insta']
users = db.instacom


def get_followers_list(username):
    result = users.find({'$and': [{'main_acc_name': username},
                                  {'status_name': 'follower'}]},
                        {'user_name': True, '_id': False})

    return [name['user_name'] for name in result]


# Написать запрос к базе, который вернет список профилей, на кого подписан
# указанный пользователь

def get_following_profile_list(username):
    result = users.find({'$and': [{'main_acc_name': username},
                                  {'status_name': 'following'}]},
                        {'user_data': {'id': True, 'username': True,
                                       'full_name': True, 'is_private': True},
                         '_id': False})

    return [name['user_data'] for name in result]
