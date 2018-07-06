from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
# BOTO
import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
#API / AUTRE
import json
import datetime

"""

THIS IS CALLED USING:
python3 manage.py add_new_publisher "Publisher Display Title IN QUOTES" http://avatar_url.com/avatar.jpg publisher_id newsapi_source_id

"""

class Command(BaseCommand):

    def add_arguments(self, parser):

        parser.add_argument('publisher_json', nargs='+', type=str)

    def handle(self, *args, **options):

        self.stdout.write("add_new_publisher.py . 1")

        publisher_array = options['publisher_json']
        publisher_dictionary = {
            "display_title": publisher_array[0],
            "image_url": publisher_array[1],
            "PUBLISHER_ID": publisher_array[2],
            "sortBy": "top",
            "source": publisher_array[3]
            }
        publisher_edition = {
            "EDITION_HEADER": {
                "edition_avatar_url": publisher_array[1],
                "edition_display_name": publisher_array[0],
                "edition_is_serif": "1",
                "edition_mast_url": "GGXGG",
                "user_username": "@{0}".format(publisher_array[3])
            },
            "EDITION_POSTS": [],
            "PUBLISHER_ID": publisher_array[2]
            }

        if self.addPublisherToSubscriptionDictionaries(publisher_dictionary):
            self.stdout.write("add_new_publisher.py . 2 . addPublisherToSubscriptionDictionaries . SUCCESS")
        else:
            self.stdout.write("add_new_publisher.py . 2 . addPublisherToSubscriptionDictionaries . FAILURE")
            return

        if self.addPublisherEdition(publisher_edition):
            self.stdout.write("add_new_publisher.py . 3 . addPublisherEdition . SUCCESS")
        else:
            self.stdout.write("add_new_publisher.py . 3 . addPublisherEdition . FAILURE")
            return


    def addPublisherToSubscriptionDictionaries(self, publisher_dictionary):

        """ ADD NEW PUBLISHER DICTIONARY TO DB.CONSTANTS SUBSCRIPTIONS DICTIONARY """
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('CONSTANTS')

        try:responseGET = table.get_item(Key={'KEY': 'API_SUBSCRIPTION_DICTIONARIES'})
        except ClientError as error:
            self.stdout.write("add_new_publisher.py . 2 . FAILURE(Client) . error = {0}".format(error))
            return False
        else:

            if responseGET['Item']:

                responseDictionary = responseGET['Item']
                returnArray = responseDictionary['VALUABLE']

                for subscription_dictionary in returnArray:

                    if subscription_dictionary['PUBLISHER_ID'] == publisher_dictionary['PUBLISHER_ID']:
                        self.stdout.write("add_new_publisher.py . 2 . FAILURE . PUBLISHER_ID ALREADY EXISTS!")
                        return False

                # RIGHT HERE, WE ACTUALLY ADD
                # returnArray.append(publisher_dictionary)

                try:resultUPDATE = table.update_item(
                    Key={'KEY': 'API_SUBSCRIPTION_DICTIONARIES'},
                    UpdateExpression="SET VALUABLE = list_append(VALUABLE, :i)",
                    ExpressionAttributeValues={':i': [publisher_dictionary],},
                    ReturnValues="UPDATED_NEW")
                except ClientError as error:
                    self.stdout.write("add_new_publisher.py . 2 . FAILURE(ClientError2) . error = {0}".format(error))
                    return False
                else:
                    return True

            else:

                self.stdout.write("add_new_publisher.py . 2 . FAILURE(Item) . error = {0}".format(error))
                return False


    def addPublisherEdition(self, publisher_edition):

        """ ADD NEW PUBLISHER EDITION TO EDITIONS """
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('EDITIONS')

        try:responsePUT = table.put_item(Item=publisher_edition)
        except ClientError as error:
            self.stdout.write("add_new_publisher.py . 3 . FAILURE(ClientError3) . error = {0}".format(error))
            return False
        else:
            return True







""" breathe """
