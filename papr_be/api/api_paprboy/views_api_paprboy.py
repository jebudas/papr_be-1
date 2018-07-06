# -*- coding: utf-8 -*-
from __future__ import unicode_literals
#
from django.conf.urls import url
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
# DRF
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
# BOTO
import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
# OTHER
from papr_be import settings
import json
import decimal
import time
import urllib.parse


class ApiArchives(APIView):

    def get(self, request, format=None):
        """ Get User Archives """

        print("ApiArchives . GET . 1")
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('ARCHIVES')

        publisher_id = request.GET.get('publisher_id')

        print("ApiArchives . GET . 2 . publisher_id = {0}".format(publisher_id))

        try:responseGET = table.query(KeyConditionExpression=Key('PUBLISHER_ID').eq(publisher_id))
        except ClientError as e:
            responseDictionary = {"success":"0"}
            return Response(json.dumps(responseDictionary, indent=0))
        else:
            items = responseGET['Items']
            if items:
                print("ApiArchives . GET . 3 . SUCCESS")
                #print(json.dumps(item, indent=4, cls=DecimalEncoder))
                responseDictionary = {"success":"1", "Items":items}
                return Response(json.dumps(responseDictionary, indent=0))
                #return Response(str(json.dumps(items, cls=DecimalEncoder)))
            else:
                print("ApiArchives . GET . 3 . FAILURE")
                responseDictionary = {"success":"0"}
                return Response(json.dumps(responseDictionary, indent=0))





    def post(self, request, format=None):
        """ Save PAPR to Archive """

        print("ApiArchives . POST . 1")

        if request.data.get('post_dictionary'):
            post_dictionary = request.data.get('post_dictionary', None)
            publisher_id = post_dictionary['post_publisher']
            print("ApiArchives . POST . 2 . publisher_id = {0}".format(publisher_id))

            dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
            table = dynamodb.Table('ARCHIVES')

            try:responseCHECK = table.query(KeyConditionExpression=Key('PUBLISHER_ID').eq(publisher_id))
            except ClientError as e:
                pass
            else:
                items = responseCHECK['Items']
                if items:
                    print("ApiArchives . POST . ATTEMPT TYPE: BEING")
                    try:resultUPDATE = table.update_item(
                        Key={'PUBLISHER_ID': publisher_id},
                        UpdateExpression="SET EDITION_POSTS = list_append(:i, EDITION_POSTS)",
                        ExpressionAttributeValues={':i': [post_dictionary],},
                        ReturnValues="UPDATED_NEW"
                    )
                    except ClientError as e:
                        pass
                    else:
                        print("ApiArchives . POST . ATTEMPT TYPE: BEING . SUCCESS")
                        responseDictionary = {"success":"1"}
                        return Response(json.dumps(responseDictionary, indent=0))
                else:
                    print("ApiArchives . POST . ATTEMPT TYPE: NOTHINGNESS")
                    try:resultPUT = table.put_item(Item={'PUBLISHER_ID': publisher_id, 'EDITION_POSTS': [post_dictionary]})
                    except ClientError as e:
                        pass
                    else:
                        print("ApiArchives . POST . ATTEMPT TYPE: NOTHINGNESS . SUCCESS")
                        responseDictionary = {"success":"1"}
                        return Response(json.dumps(responseDictionary, indent=0))

            # WE HAVE TRIED TO UPDATE AND PUT, TO NO AVAIL
            print("ApiArchives . POST . FAILURE")
            responseDictionary = {"success":"0"}
            return Response(json.dumps(responseDictionary, indent=0))


class ApiSavedPosts(APIView):

    def get(self, request, format=None):
        """ Get Saved Posts """

        print("ApiSavedPosts . GET . 1")
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('SAVED_POSTS')

        publisher_id = request.GET.get('publisher_id')

        print("ApiSavedPosts . GET . 2")

        try:responseGET = table.query(KeyConditionExpression=Key('PUBLISHER_ID').eq(publisher_id))
        except ClientError as e:
            responseDictionary = {"success":"0"}
            return Response(json.dumps(responseDictionary, indent=0))
        else:
            items = responseGET['Items']
            if items:
                print("ApiSavedPosts . GET . 3 . SUCCESS")
                #print(json.dumps(item, indent=4, cls=DecimalEncoder))
                item_dictionary = items[0]
                responseDictionary = {"success":"1", "EDITION_POSTS":item_dictionary["EDITION_POSTS"]}
                return Response(json.dumps(responseDictionary, indent=0))
                #return Response(str(json.dumps(items, cls=DecimalEncoder)))
            else:
                print("ApiSavedPosts . GET . 3 . FAILURE")
                responseDictionary = {"success":"0"}
                return Response(json.dumps(responseDictionary, indent=0))

    def post(self, request, format=None):
        """ Save Posts """

        print("ApiSavedPosts . POST . 1")

        if request.data.get('post_dictionary'):
            post_dictionary = request.data.get('post_dictionary', None)
            user_id = request.data.get('user_id', None)

            dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
            table = dynamodb.Table('SAVED_POSTS')

            try:result = table.update_item(
                    Key={'PUBLISHER_ID': user_id},
                    # THE list_append below is prepending, to append, reverse the operands
                    UpdateExpression="SET EDITION_POSTS = list_append(:i, if_not_exists(EDITION_POSTS, :empty_list))",
                    ExpressionAttributeValues={
                        ':i': [post_dictionary],
                        ":empty_list":[],
                    },
                    ReturnValues="UPDATED_NEW"
                )
            except ClientError as e:
                print("ApiSavedPosts . POST . 4 . FAILURE = ClientError: {0}".format(e.response['Error']['Message']))
                responseDictionary = {"success":"0"}
                return Response(json.dumps(responseDictionary, indent=0))
            else:
                if result['ResponseMetadata']['HTTPStatusCode'] == 200 and 'Attributes' in result:
                    print("ApiSavedPosts . POST . 4 . SUCCESS")
                    responseDictionary = {"success":"1"}
                    return Response(json.dumps(responseDictionary, indent=0))
                else:
                    print("ApiSavedPosts . POST . 4 . FAILURE")
                    responseDictionary = {"success":"0"}
                    return Response(json.dumps(responseDictionary, indent=0))


class ApiPublish(APIView):

    def post(self, request, format=None):
        """ PUBLISH Papr """

        print("ApiPublish . POST . 1")

        if request.data.get('new_edition_dictionary'):
            print("ApiPublish . POST . 2 . SUCCESS")
            this_new_edition = request.data.get('new_edition_dictionary', None)

            dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
            table = dynamodb.Table('EDITIONS')

            try:response = table.put_item(Item=this_new_edition)
            except ClientError as e:
                print("PUBLISH ERROR: {0}".format(e.response['Error']['Message']))
                responseDictionary = {"success":"0", "ApiPublish" : "FAILURE: {0}".format(e.response['Error']['Message']), "this_new_edition":this_new_edition}
                return Response(json.dumps(responseDictionary, indent=0))
            else:

                print("ApiPublish . POST . 3 . PUBLISHED")

                array_of_papr_items = this_new_edition['EDITION_POSTS']

                print("ApiPublish . POST . 3 . CREATING STATISTICS ROWS . START")

                for this_item in array_of_papr_items:
                    createStatisticsRowInDatabase(this_item)

                responseDictionary = {"success":"1", "ApiPublish" : "Hey Now"}
                return Response(json.dumps(responseDictionary, indent=0))


class ApiEdition(APIView):
    if (settings.DEBUG):
        permission_classes = (AllowAny,)

    def get(self, request, format=None):
        """ GET User Subscriptions """

        if request.GET.get('publisher_id'):
            publisher_id = request.GET.get('publisher_id', '1')
        else:
            responseDictionary = {"success":"0", "error" : "Publisher ID <NOT> Received"}
            return Response(json.dumps(responseDictionary, indent=0))

        try:this_edition_dictionary = gather_subscriptions(publisher_id)
        except ClientError as e:
            responseDictionary = {"success":"0", "error" : "Publisher ID <NOT> Received"}
            return Response(json.dumps(responseDictionary, indent=0))
        else:
            responseDictionary = {"success":"1", "edition" : this_edition_dictionary}
            return Response(json.dumps(responseDictionary, indent=0))


class ApiSubscriptions(APIView):
    if (settings.DEBUG):
        permission_classes = (AllowAny,)

    def get(self, request, format=None):
        """ GET User Subscriptions """

        if request.GET.getlist('user_subscriptions[]'):
            user_subscriptions = request.GET.getlist('user_subscriptions[]')
        else:
            print("ApiSubscriptions . GET . user_subscriptions = FAILURE. request.GET = {0}".format(request.GET))
            responseDictionary = {"success":"0", "error" : "Zero Subscriptions Received"}
            return Response(json.dumps(responseDictionary, indent=0))

        array_of_editions = []

        print("ApiSubscriptions . GET . 1a")
        print("ApiSubscriptions . GET . 1b . for user_subscriptions = {0}".format(user_subscriptions))
        for this_publisher_id in user_subscriptions:

            try:this_subscription_dictionary = gather_subscriptions(this_publisher_id)
            except ClientError as e:
                pass
            else:
                array_of_editions.append(this_subscription_dictionary)

        responseDictionaryFinal = {"success":"1", "user_subscriptions" : array_of_editions}
        print("ApiSubscriptions . GET . 2 . SUCCESS")
        return Response(json.dumps(responseDictionaryFinal, indent=0))

    def post(self, request, format=None):
        """ POST/UPDATE List of User Subscriptions """

        # RECEIVE AN ARRAY OF SUBSCRIPTIOSN, SAVE TO user_subscriptions
        print("ApiSubscriptions . POST . 1")

        # COLLECT POST DATA
        user_data = request.data
        #user_id = user_data.get('user_id', None)
        # {"user_username":"jose_20170819_034148", "user_subscriptions":"11111,22222,33333,44444"}
        user_username = user_data.get('user_username', None)
        user_subscriptions = user_data.get('user_subscriptions', None)
        updated_rows = 0

        #if user_id:
        if user_username:

            try:
                dbHost     = settings.DATABASES['default']['HOST']
                dbUsername = settings.DATABASES['default']['USER']
                dbPassword = settings.DATABASES['default']['PASSWORD']
                dbName     = settings.DATABASES['default']['NAME']

                connection_string = ("host='{0}' dbname='{1}' user='{2}' password='{3}'".format(dbHost,dbName,dbUsername,dbPassword))
                connection = psycopg2.connect(connection_string)
                cursor = connection.cursor(cursor_factory=RealDictCursor)
                cursor.execute("UPDATE api_user_useraccount SET user_subscriptions=(%s) WHERE user_username = (%s)", (user_subscriptions,user_username));
                connection.commit()

                updated_rows = cursor.rowcount

                connection.close()
                cursor.close()
                print("updated_rows = {0}".format(updated_rows))

                if updated_rows == 1:
                    responseDictionary = {"success":"1", "message" : "User Subscriptions Have Been Updated."}
                    return Response(json.dumps(responseDictionary, indent=0))
                else:
                    responseDictionary = {"success":"0", "error" : "User Subscriptions Have <NOT> Been Updated."}
                    return Response(json.dumps(responseDictionary, indent=0))

            except (Exception, psycopg2.DatabaseError) as error:
                responseDictionary = {"success":"0", "error" : str(error)}
                return Response(json.dumps(responseDictionary, indent=0))

        else:

            responseDictionary = {"success":"0", "error" : "User Subscriptions Have <NOT> Been Updated. Missing Username."}
            return Response(json.dumps(responseDictionary, indent=0))

        responseDictionary = {"user_subscriptions":user_subscriptions}
        return Response(json.dumps(responseDictionary, indent=0))



""" ________ ________ ________ ________ ________ ________ ________ ________ ________ ________ ________ ________ ________ ________ """

def gather_subscriptions(publisher_id):

    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('EDITIONS')

    try:editionDictionary = table.get_item(Key={'PUBLISHER_ID': publisher_id})
    except ClientError as e:
        print("PUBLISHER_ID ERROR: {0}".format(e.response['Error']['Message']))
        pass
    else:
        return editionDictionary

def deliver(request):

    if request.method == 'GET':

        # Let's use Amazon S3
        # dynamodb = boto3.resource('dynamodb', region_name='us-east-1', endpoint_url="http://localhost:5443")
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('EDITIONS')

        edition_publisher = "NYT-1111111"
        edition_header = {
            "title":"The New York Times",
            "username": "@nyt"
        }
        edition_posts = [
            {
        			"post_id": "1001",
        			"text": "Whoa, Trump Did What?",
        			"link": "http://nyt.com/article_1001.html"
        		},
        		{
        			"post_id": "1002",
        			"text": "Nice! Hillary Clinton Indicted!",
        			"link": "http://nyt.com/article_1002.html"
        		},
        		{
        			"post_id": "1003",
        			"text": "Yankees Win 28th World Championship!",
        			"link": "http://nyt.com/article_1003.html"
        		}
        ]

        response = table.put_item(
           Item={
                'PUBLISHER_ID': edition_publisher,
                'EDITION_HEADER': edition_header,
                'EDITION_POSTS': edition_posts
            }
        )

        print("PutItem succeeded.")
        print(json.dumps(response, indent=4, cls=DecimalEncoder))
        return HttpResponse("Received A GET: " + str(json.dumps(response, indent=4, cls=DecimalEncoder)) )

    else:

        return HttpResponse("Received A POST")

def createStatisticsRowInDatabase(this_item):

    print("ApiPublish . POST . createStatisticsRowInDatabase . 1")

    publisher_id = this_item['post_publisher']
    post_id = this_item['post_id']
    post_title = this_item['post_title']
    stats = {"comments": "0", "likes": "1", "reposts": "0", "views": "1"}
    new_stats_dictionary = {"PUBLISHER_ID":publisher_id, "POST_ID":post_id, "POST_TITLE":post_title, "STATS":stats}

    print("ApiPublish . POST . createStatisticsRowInDatabase . 2 . new_stats_dictionary = {0}".format(new_stats_dictionary))

    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('STATISTICS')

    try:responsePUT = table.put_item(Item=new_stats_dictionary)
    except ClientError as error:
        pass
    else:
        print("ApiPublish . POST . createStatisticsRowInDatabase . SUCCESS")
        pass

# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)
