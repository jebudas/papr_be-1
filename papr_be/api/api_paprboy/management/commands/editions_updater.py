from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
# BOTO
import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
#API / AUTRE
import urllib.request
from urllib.request import urlopen
import json
import datetime

"""

THIS IS CALLED USING:
python3 manage.py editions_updater

"""

class Command(BaseCommand):

    def handle(self, *args, **options):

        """ FIRST WE GRAB THE LIST OF SUBSCRIPTIONS WE NEED TO CHECK """
        try:array_of_api_subscriptions = self.returnArrayOfApiSubscriptions()
        except ClientError as error:
            return

        # self.stdout.write("editions_updater.py . array_of_api_subscriptions = {0}".format(array_of_api_subscriptions))

        """ RETURN WALL : IF WE HAVE NO IDs, STOP """
        if len(array_of_api_subscriptions) < 1:
            return

        """ ENUMERATE THROUGH ARRAY, GRAB FRESH HEADLINES """
        for api_subscription_dictionary in array_of_api_subscriptions:

            new_papr = {}

            """ GET OLD EDITION DICTIONARY """
            old_edition_dictionary = {}
            publisher_id = api_subscription_dictionary['PUBLISHER_ID']

            #if publisher_id == "p7000035":
            #    self.stdout.write("editions_updater.py . STARTING (publisher_id = {0})".format(publisher_id))
            #    pass
            #else:
            #    self.stdout.write("editions_updater.py . SKIPPING (publisher_id = {0})".format(publisher_id))
            #    continue

            dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
            table = dynamodb.Table('EDITIONS')
            try:responseOldEditionDictionary = table.get_item(Key={'PUBLISHER_ID': publisher_id})
            except ClientError as error:
                # self.stdout.write("editions_updater.py . EDITIONS . FAILURE = {0}".format(publisher_id))
                continue
            else:
                if 'Item' in responseOldEditionDictionary:
                    old_edition_dictionary = responseOldEditionDictionary['Item']
                else:
                    # self.stdout.write("editions_updater.py . EDITIONS . FAILURE.ELSE.publisher_id = {0}".format(publisher_id))
                    # self.stdout.write("editions_updater.py . EDITIONS . FAILURE.ELSE.responseOldEditionDictionary = {0}".format(responseOldEditionDictionary))
                    continue

            """ GET API EDITION DICTIONARY """
            # self.stdout.write("PROGRESS: editions_updater.py . GET API EDITION DICTIONARY ({0})".format(publisher_id))
            try:api_edition_dictionary = self.returnApiEditionDictionary(api_subscription_dictionary)
            except ClientError as error:
                # TODO GGXGG : MIGHT WANT TO HANDLE THIS HERE.
                continue
            else:
                if api_edition_dictionary:
                    # self.stdout.write("editions_updater.py . GET API EDITION DICTIONARY ({0}) . SUCCESS".format(publisher_id))
                    pass
                else:
                    # self.stdout.write("editions_updater.py . GET API EDITION DICTIONARY ({0}) . FAILURE".format(publisher_id))
                    pass

            """ CREATE AN ARAY OF NEW PAPR ITEMS """
            # self.stdout.write("PROGRESS: editions_updater.py . CREATE AN ARAY OF NEW PAPR ITEMS ({0})".format(publisher_id))
            try:array_of_papr_items = self.returnArrayOfPaprItems(api_edition_dictionary, old_edition_dictionary)
            except ClientError as error:
                continue
            else:
                if array_of_papr_items:
                    pass
                else:
                    continue


            """ CREATE COMMENTS/STATISTICS DATABASE FOR EACH NEW ITEM """
            # self.stdout.write("PROGRESS: editions_updater.py . CREATE COMMENTS/STATISTICS DATABASE FOR EACH NEW ITEM ({0})".format(publisher_id))
            for this_item in array_of_papr_items:
                self.createCommentsRowInDatabase(this_item)
                self.createStatisticsRowInDatabase(this_item)


            """ CREATE NEW PAPR DICTIONARY """
            # self.stdout.write("PROGRESS: editions_updater.py . CREATE NEW PAPR DICTIONARY ({0})".format(publisher_id))
            try:new_papr_edition = self.returnPaprItemComplete(array_of_papr_items, old_edition_dictionary)
            except ClientError as error:
                continue


            """ PUBLISH NEW PAPR DICTIONARY """
            # self.stdout.write("PROGRESS: editions_updater.py . PUBLISH NEW PAPR DICTIONARY ({0})".format(publisher_id))
            try:new_papr = self.updateThisEdition(new_papr_edition)
            except ClientError as error:
                continue
            else:
                # self.stdout.write("PROGRESS: editions_updater.py . COMPLETE! {0} was published successfully.".format(publisher_id))
                pass

    def returnArrayOfApiSubscriptions(self):

        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('CONSTANTS')

        try:responseGET = table.get_item(Key={'KEY': 'API_SUBSCRIPTION_DICTIONARIES'})
        except ClientError as error:
            # self.stdout.write("editions_updater.py . returnArrayOfApiSubscriptions . FAILURE: {0}".format(updated_edition))
            return {}
        else:
            if responseGET['Item']:
                responseDictionary = responseGET['Item']
                returnArray = responseDictionary['VALUABLE']
                return returnArray
            else:
                # self.stdout.write("editions_updater.py . returnArrayOfApiSubscriptions . FAILURE: {0}".format(updated_edition))
                return []


    def returnApiEditionDictionary(self, api_subscription_dictionary):

        apiNewsKey = settings.API_NEWS_KEY
        # url = "https://newsapi.org/v1/articles?source={0}&sortBy={1}&apiKey={2}".format(api_subscription_dictionary['source'], api_subscription_dictionary['sortBy'], apiNewsKey)
        url = "https://newsapi.org/v2/top-headlines?sources={0}&apiKey={1}".format(api_subscription_dictionary['source'], apiNewsKey)
        req = urllib.request.Request(url)
        try:url_response = urllib.request.urlopen(req)
        except urllib.error.HTTPError as err2:
            return {}
        else:
            html = url_response.read()
            htmljson = html.decode('utf8')
            api_edition_dictionary = json.loads(htmljson)
            return api_edition_dictionary


    def returnArrayOfPaprItems(self, api_dictionary_rcvd, old_dictionary_rcvd):

        article_counter = 0
        article_limiter = 12
        array_of_articles_dirty = api_dictionary_rcvd['articles']
        array_of_articles_clean = []

        """ CONVERT API ARTICLES TO CLEAN PAPR ARTICLES """
        for article_dictionary in array_of_articles_dirty:

            if article_counter == article_limiter:
                return array_of_articles_clean

            try:clean_papr_post = self.returnPaprPostFromDictionary(article_dictionary, old_dictionary_rcvd)
            except ClientError as e:
                pass
            else:
                array_of_articles_clean.append(clean_papr_post)

            article_counter = article_counter + 1

        if array_of_articles_clean:
            return array_of_articles_clean
        else:
            return [];


    def updateThisEdition(self, updated_edition):

        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('EDITIONS')

        try:responsePUT = table.put_item(Item=updated_edition)
        except ClientError as error:
            # self.stdout.write("editions_updater.py . updateThisEdition . FAILURE: {0}".format(updated_edition['PUBLISHER_ID']))
            pass
        else:
            # self.stdout.write("editions_updater.py . updateThisEdition . SUCCESS")
            pass


    def returnPaprPostFromDictionary(self, api_dictionary_rcvd, old_dictionary_rcvd):

        edition_header = old_dictionary_rcvd['EDITION_HEADER']

        if edition_header["edition_mast_url"]:
            post_publisher_mast_url = edition_header["edition_mast_url"]
        else:
            post_publisher_mast_url = "-"

        post_publisher_avatar_url = edition_header["edition_avatar_url"]
        post_publisher_display_name = edition_header["edition_display_name"]

        if api_dictionary_rcvd["author"]:
            post_author = api_dictionary_rcvd["author"]
        else:
            post_author = "-"

        if api_dictionary_rcvd["description"]:
            post_description = api_dictionary_rcvd["description"]
        else:
            post_description = "-"

        #v1.4 UPDATE/NEW >
        # WE LOOK FOR A PREVIOUS DICTIONARY, BC WE SHOULDNT ASSIGN A NEW post_id OR post_timestamp FOR AN OLDER ARTICLE
        post_check_previous_dictionary = self.returnPostCheckPreviousDictionary(api_dictionary_rcvd, old_dictionary_rcvd)
        post_id = post_check_previous_dictionary["post_id"]
        post_timestamp = post_check_previous_dictionary["post_timestamp"]

        post_image_url = api_dictionary_rcvd["urlToImage"]
        post_link = api_dictionary_rcvd["url"]
        post_publisher = old_dictionary_rcvd['PUBLISHER_ID']
        post_title = api_dictionary_rcvd["title"]
        post_type = "text"

        papr_post = {"post_author":post_author, "post_description":post_description, "post_id":post_id, "post_image_url":post_image_url,
                     "post_link":post_link, "post_publisher":post_publisher, "post_title":post_title, "post_timestamp": post_timestamp,
                     "post_type":post_type, "post_publisher_mast_url":post_publisher_mast_url,
                     "post_publisher_display_name":post_publisher_display_name, "post_publisher_avatar_url":post_publisher_avatar_url}

        return papr_post


    def returnPaprItemComplete(self, array_of_articles_clean, old_dictionary_rcvd):

        new_papr_item = {   "PUBLISHER_ID":old_dictionary_rcvd['PUBLISHER_ID'],
                            "EDITION_HEADER":old_dictionary_rcvd['EDITION_HEADER'],
                            "EDITION_POSTS":array_of_articles_clean}

        return new_papr_item


    def returnPostCheckPreviousDictionary(self, api_dictionary_rcvd, old_dictionary_rcvd):

        array_edition_posts_old = old_dictionary_rcvd['EDITION_POSTS']
        for old_post in array_edition_posts_old:

            if api_dictionary_rcvd["title"] == old_post['post_title']:
                # WE FOUND AN OLD POST SO WE USE THAT ID && TIMESTAMP
                post_check_previous_dictionary = {"post_id":old_post['post_id'], "post_timestamp":old_post['post_timestamp']}
                return post_check_previous_dictionary

        # WE NEED A NEW TIMESTAMP
        milliseconds_full = datetime.datetime.now().strftime('%f')
        milliseconds = milliseconds_full[-2:] # grabs last two digits; first two digits is [:2]
        post_timestamp = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S-{0}'.format(milliseconds))

        # WE NEED A NEW ID
        post_id = "{0}-{1}".format(old_dictionary_rcvd['PUBLISHER_ID'], post_timestamp)

        # RETURN A NEW DICTIONARY
        post_check_previous_dictionary = {"post_id":post_id, "post_timestamp":post_timestamp}
        return post_check_previous_dictionary


    def createCommentsRowInDatabase(self, this_item):

        publisher_id = this_item['post_publisher']
        comment_set_id = this_item['post_id']
        new_comment_dictionary = {"PUBLISHER_ID":publisher_id, "COMMENT_SET_ID":comment_set_id, "COMMENT_SET_THREADS":[]}

        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('COMMENTS')

        try:responseGET = table.get_item(Key={'PUBLISHER_ID': publisher_id, 'COMMENT_SET_ID': comment_set_id})
        except ClientError as e:
            pass
        else:
            if 'Item' in responseGET:
                pass
            else:
                try:responsePUT = table.put_item(Item=new_comment_dictionary)
                except ClientError as error:
                    pass
                else:
                    pass


    def createStatisticsRowInDatabase(self, this_item):

        publisher_id = this_item['post_publisher']
        post_id = this_item['post_id']
        post_title = this_item['post_title']
        stats = {"comments": "0", "likes": "1", "reposts": "0", "views": "1"}
        new_stats_dictionary = {"PUBLISHER_ID":publisher_id, "POST_ID":post_id, "POST_TITLE":post_title, "STATS":stats}

        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('STATISTICS')

        try:responseGET = table.get_item(Key={'PUBLISHER_ID':publisher_id, "POST_ID":post_id})
        except ClientError as e:
            pass
        else:
            if 'Item' in responseGET:
                pass
            else:
                try:responsePUT = table.put_item(Item=new_stats_dictionary)
                except ClientError as error:
                    pass
                else:
                    # self.stdout.write("PUBLISHER_ID ({0}) NOT FOUND, ADDED".format(publisher_id))
                    pass
