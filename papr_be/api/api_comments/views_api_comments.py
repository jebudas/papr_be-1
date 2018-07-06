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
import json
import decimal
from papr_be import settings


class ApiCommentThread(APIView):
    """ COMMENTS API View """
    if (settings.DEBUG):
        permission_classes = (AllowAny,)

    def get(self, request, format=None):
        """ Return Comment Thread For Comment ID  """

        print("ApiCommentThread . GET . 1")
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('COMMENTS')

        publisher_id = request.GET.get('publisher_id')
        comment_set_id = request.GET.get('comment_set_id')

        print("ApiCommentThread . GET . 2")

        try:responseQUERY = table.query(KeyConditionExpression=Key('PUBLISHER_ID').eq(publisher_id) & Key('COMMENT_SET_ID').eq(comment_set_id))
        except ClientError as e:
            print("ApiCommentThread . GET . 3 . FAILURE")
            return False
        else:
            print("ApiCommentThread . GET . 3 . SUCCESS")
            items = responseQUERY['Items']
            my_comment_dictionary = items[0]
            try:responseDictionary = insertCommentVotesAndReplies(publisher_id, comment_set_id, my_comment_dictionary)
            except ClientError as e:
                print("ApiCommentThread . GET . 4 . FAILURE")
                return False
            else:
                print("ApiCommentThread . GET . 4 . SUCCESS")
                return Response(json.dumps(responseDictionary, indent=0))

    def post(self, request, format=None):
        """ PUBLISH COMMENT """

        print("ApiCommentThread . POST . 1")

        if request.data.get('comment_dictionary'):

            print("ApiCommentThread . POST . 2")

            # SETUP COMMENT DICTIONARY
            comment_dictionary = request.data.get('comment_dictionary', None)

            # SETUP COMMENT VARIABLES
            publisher_id = comment_dictionary['article_publisher_id']
            comment_set_id = comment_dictionary['comment_set_id']
            comment_type = comment_dictionary['comment_type']

            print("ApiCommentThread . POST . 2.1 . publisher_id = {0}, comment_set_id = {1}, comment_type = {2}".format(publisher_id, comment_set_id, comment_type))

            my_comment_dictionary = {
                "COMMENT_ID" : comment_dictionary['comment_id'],
                "COMMENT_PUBLISHER_ID" : comment_dictionary['comment_publisher_id'],
                "COMMENT_TEXT" : comment_dictionary['comment_text'],
                "COMMENT_TIMESTAMP" : comment_dictionary['comment_timestamp'],
                "COMMENT_TYPE" : comment_type,
                "COMMENT_USERNAME" : comment_dictionary['comment_username']
            }

            print("ApiCommentThread . POST . 2.2")

            if comment_type == "reply":

                print("ApiCommentThread . POST . 3 . REPLY")

                my_comment_dictionary["PARENT_COMMENT_ID"] = comment_dictionary['parent_comment_id']
                my_comment_dictionary["PARENT_COMMENT_PUBLISHER_ID"] = comment_dictionary['parent_comment_publisher_id']
                my_comment_dictionary["PARENT_COMMENT_USERNAME"] = comment_dictionary['parent_comment_username']

                reply_set_id = my_comment_dictionary["PARENT_COMMENT_ID"]

                # WRITE TO COMMENTS_REPLIES
                if updateCommentsRepliesWithDictionary(publisher_id, reply_set_id, my_comment_dictionary):
                    print("ApiCommentThread . POST . 4 . REPLY . SUCCESS")
                    responseDictionary = {"success":"1"}
                    return Response(json.dumps(responseDictionary, indent=0))
                else:
                    print("ApiCommentThread . POST . 4 . REPLY . FAILURE")
                    responseDictionary = {"success":"0"}
                    return Response(json.dumps(responseDictionary, indent=0))

            elif comment_type == "comment":

                print("ApiCommentThread . POST . 3 . COMMENT")

                if updateCommentsWithDictionary(publisher_id, comment_set_id, my_comment_dictionary):
                    print("ApiCommentThread . POST . 4 . COMMENT . SUCCESS")
                    responseDictionary = {"success":"1"}
                    return Response(json.dumps(responseDictionary, indent=0))
                else:
                    print("ApiCommentThread . POST . 4 . COMMENT . FAILURE")
                    responseDictionary = {"success":"0"}
                    return Response(json.dumps(responseDictionary, indent=0))

            else:

                print("ApiCommentThread . POST . 3 . ELSE")

class ApiCommentsVotes(APIView):
    """ COMMENTS COUNTER API View """
    if (settings.DEBUG):
        permission_classes = (AllowAny,)

    def post(self, request, format=None):
        """ PUBLISH COMMENT """

        if request.data.getlist('votes[]'):

            print("ApiCommentsVotes . POST . 1")
            dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
            table = dynamodb.Table('COMMENTS_VOTES')

            publisher_id = request.data.get('publisher_id')
            comment_id = request.data.get('comment_id')
            vote_type = request.data.get('vote_type')

            print("ApiCommentsVotes . POST . 2")

            try:responseQUERY = table.query(KeyConditionExpression=Key('PUBLISHER_ID').eq(publisher_id) & Key('COMMENT_ID').eq(comment_id))
            except ClientError as error:
                print("ApiCommentsVotes . POST . 3 . NOT FOUND . CREATING NEW")
                this_votes_dictionary = {"COMMENT_ID":comment_id, "COMMENT_VOTES_DOWN":"0", "COMMENT_VOTES_UP":"0", "PUBLISHER_ID":publisher_id}
            else:
                print("ApiCommentsVotes . POST . 3 . FOUND . responseQUERY = {0}".format(responseQUERY))
                items = responseQUERY['Items']
                this_votes_dictionary = items[0]

            if vote_type == "up":
                vote_integer = int(this_votes_dictionary["COMMENT_VOTES_UP"])
                vote_integer = vote_integer + 1
                this_votes_dictionary["COMMENT_VOTES_UP"] = str(vote_integer)
            elif vote_type == "down":
                vote_integer = int(this_votes_dictionary["COMMENT_VOTES_DOWN"])
                vote_integer = vote_integer + 1
                this_votes_dictionary["COMMENT_VOTES_DOWN"] = str(vote_integer)
            else:
                return False

            try:responsePUT = table.put_item(Item=this_votes_dictionary)
            except ClientError as error:
                print("ApiCommentsVotes . POST . 4 . Error = {0}".format(error))
                return False
            else:
                print("ApiCommentsVotes . POST . 4 . SUCCESS")
                responseDictionary = {"success":"1"}
                return responseDictionary

class ApiCommentsReplies(APIView):
    """ COMMENTS REPLIES API View """
    if (settings.DEBUG):
        permission_classes = (AllowAny,)

    def get(self, request, format=None):
        """ Return Comment Thread For Comment ID  """

        print("ApiCommentsReplies . GET . 1")
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('COMMENTS_REPLIES')

        reply_set_id = request.GET.get('reply_set_id')
        temp_array = reply_set_id.split('-')
        publisher_id = temp_array[0]

        print("ApiCommentsReplies . GET . 2")

        # try:responseQUERY = table.query(KeyConditionExpression=Key('PUBLISHER_ID').eq(publisher_id) & Key('REPLY_SET_ID').eq(reply_set_id))
        # except ClientError as error:
        #     print("ApiComments . GET . 4 . FAILURE = ClientError: {0}".format(error.response['Error']['Message']))
        #     return False
        # else:
        #     print("ApiCommentsReplies . GET . 3 . SUCCESS")
        #     #item = response['Item']
        #     #print(json.dumps(item, indent=4, cls=DecimalEncoder))
        #     return Response(str(json.dumps(response, cls=DecimalEncoder)))

        try:responseGET = table.get_item(Key={'PUBLISHER_ID': publisher_id, 'REPLY_SET_ID': reply_set_id})
        except ClientError as error:
            print("ApiCommentsReplies . GET . 3 . FAILURE = ClientError: {0}".format(error.response['Error']['Message']))
            return False
        else:
            if 'Item' in responseGET:
                print("ApiCommentsReplies . GET . 3 . SUCCESS")
                item = responseGET['Item']
                # print(json.dumps(item, indent=4, cls=DecimalEncoder))
                # return Response(str(json.dumps(responseGET, cls=DecimalEncoder)))
                return Response(str(json.dumps(item, cls=DecimalEncoder)))
            else:
                print("ApiCommentsReplies . GET . 3 . FOUND/FAILURE = {0}".format(responseGET))

    def post(self, request, format=None):
        """ PUBLISH COMMENT """

        print("ApiCommentsReplies . POST . 1")

        if request.data.get('comment_dictionary'):

            print("ApiCommentsReplies . POST . 2")



# PRE v1.4
class ApiComments(APIView):
    """ COMMENTS API View """

    def get(self, request, format=None):
        """ Return a list of Comments features """

        print("ApiComments . GET . 1")
        # Let's use Amazon S3
        # dynamodb = boto3.resource('dynamodb', region_name='us-east-1', endpoint_url="http://localhost:5443")
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('COMMENTS')

        COMMENT_ID = request.GET.get('comment_id')
        PUBLISHER_ID = request.GET.get('publisher_id')

        print("ApiComments . GET . 2")

        try:response = table.query(KeyConditionExpression=Key('PUBLISHER_ID').eq(PUBLISHER_ID) & Key('COMMENT_ID').eq(COMMENT_ID))
        except ClientError as e:
            return False
            # print("ApiComments . GET . 4 . FAILURE = ClientError: {0}".format(e.response['Error']['Message']))
            # responseDictionary = {"success":"0"}
            # return Response(json.dumps(responseDictionary, indent=0))
        else:
            print("ApiComments . GET . 3 . SUCCESS")
            #item = response['Item']
            #print(json.dumps(item, indent=4, cls=DecimalEncoder))
            return Response(str(json.dumps(response, cls=DecimalEncoder)))

    def post(self, request, format=None):
        """ PUBLISH COMMENT """

        print("ApiComments . POST . 1")

        if request.data.get('comment_dictionary'):
            comment_dictionary = request.data.get('comment_dictionary', None)
            comment_id = comment_dictionary['comment_id']
            publisher_id = comment_dictionary['publisher_id']

            dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
            table = dynamodb.Table('COMMENTS')

            print("ApiComments . POST . 2")
            #try:response = table.query(KeyConditionExpression=Key('PUBLISHER_ID').eq(publisher_id) & Key('COMMENT_ID').eq(comment_id))
            try:result = table.update_item(
                    Key={'PUBLISHER_ID': publisher_id, 'COMMENT_ID': comment_id},
                    UpdateExpression="SET COMMENTS = list_append(if_not_exists(COMMENTS, :empty_list), :i)",
                    ExpressionAttributeValues={
                        ':i': [comment_dictionary],
                        ":empty_list":[],
                    },
                    ReturnValues="UPDATED_NEW"
                )
            except ClientError as e:
                print("ApiComments . POST . 4 . FAILURE = ClientError: {0}".format(e.response['Error']['Message']))
                responseDictionary = {"success":"0"}
                return Response(json.dumps(responseDictionary, indent=0))
            else:
                if result['ResponseMetadata']['HTTPStatusCode'] == 200 and 'Attributes' in result:
                    print("ApiComments . POST . 4 . SUCCESS")
                    try:response = table.query(KeyConditionExpression=Key('PUBLISHER_ID').eq(publisher_id) & Key('COMMENT_ID').eq(comment_id))
                    except ClientError as e:
                        return False
                    else:
                        print("ApiComments . POST . 5 . SUCCESS")
                        #item = response['Item']
                        #print(json.dumps(item, indent=4, cls=DecimalEncoder))
                        return Response(str(json.dumps(response, cls=DecimalEncoder)))
                else:
                    print("ApiComments . POST . 4 . FAILURE")
                    responseDictionary = {"success":"0"}
                    return Response(json.dumps(responseDictionary, indent=0))

class ApiNotifications(APIView):
    """ NOTIFICATIONS API View """

    def get(self, request, format=None):
        """ Return a list of Comments features """

        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('NOTIFICATIONS')

        PUBLISHER_ID = request.GET.get('publisher_id')

        try:responseGET = table.get_item(Key={'PUBLISHER_ID': PUBLISHER_ID})
        except ClientError as error:
            responseDictionary = {"success":"0"}
            return Response(json.dumps(responseDictionary, indent=0))
        else:
            if responseGET['Item']:
                responseDictionary = responseGET['Item']
                returnArray = responseDictionary['NOTIFICATIONS']
                responseDictionary = {"success":"1", "notifications":returnArray}
                return Response(json.dumps(responseDictionary, indent=0))
            else:
                responseDictionary = {"success":"0"}
                return Response(json.dumps(responseDictionary, indent=0))

    def post(self, request, format=None):
        """ PUBLISH COMMENT """

        print("ApiNotifications . POST . 1")
        print("ApiNotifications . POST . 1 . request.data = {0}".format(request.data))

        if request.data.get('notification_dictionary'):
            notification_dictionary = request.data.get('notification_dictionary', None)
            print("ApiNotifications . POST . 2 . notification_dictionary = {0}".format(notification_dictionary))

            publisher_id = notification_dictionary['publisher_id']
            post_id = notification_dictionary['post_id']
            timestamp = notification_dictionary['timestamp']
            comment = notification_dictionary['comment']
            friend_id = notification_dictionary['friend_id']
            friend_username = notification_dictionary['friend_username']
            friend_avatar_url = notification_dictionary['friend_avatar_url']
            type_field = notification_dictionary['type_field']

            dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
            table = dynamodb.Table('NOTIFICATIONS')

            print("ApiNotifications . POST . 3")
            try:result = table.update_item(
                    Key={'PUBLISHER_ID': publisher_id},
                    UpdateExpression="SET NOTIFICATIONS = list_append(:i, if_not_exists(NOTIFICATIONS, :empty_list))",
                    ExpressionAttributeValues={
                        ':i': [notification_dictionary],
                        ":empty_list":[],
                    },
                    ReturnValues="UPDATED_NEW"
                )
            except ClientError as e:
                print("ApiNotifications . POST . 4 . FAILURE = ClientError: {0}".format(e.response['Error']['Message']))
                responseDictionary = {"success":"0"}
                return Response(json.dumps(responseDictionary, indent=0))
            else:
                if result['ResponseMetadata']['HTTPStatusCode'] == 200 and 'Attributes' in result:
                    print("ApiNotifications . POST . 4 . SUCCESS")
                    try:response = table.query(KeyConditionExpression=Key('PUBLISHER_ID').eq(publisher_id))
                    except ClientError as e:
                        return False
                    else:
                        print("ApiNotifications . POST . 5 . SUCCESS")
                        #item = response['Item']
                        #print(json.dumps(item, indent=4, cls=DecimalEncoder))
                        return Response(str(json.dumps(response, cls=DecimalEncoder)))
                else:
                    print("ApiNotifications . POST . 4 . FAILURE")
                    responseDictionary = {"success":"0"}
                    return Response(json.dumps(responseDictionary, indent=0))

""" ________ ________ ________ ________ ________ ________ ________ ________ ________ ________ ________ ________ ________ ________ """

def insertCommentVotesAndReplies(publisher_id, comment_set_id, my_comment_dictionary):

    print("ApiCommentThread . GET . 4 . insertCommentVotesAndReplies . insertCommentVotes")

    try:my_comment_dictionary_votes = insertCommentVotes(publisher_id, comment_set_id, my_comment_dictionary)
    except ClientError as e:
        print("ApiCommentThread . GET . 4 . insertCommentVotesAndReplies . insertCommentVotes . FAILURE")
        pass
    else:
        print("ApiCommentThread . GET . 4 . insertCommentVotesAndReplies . insertCommentVotes . SUCCESS")
        my_comment_dictionary = my_comment_dictionary_votes

    print("ApiCommentThread . GET . 4 . insertCommentVotesAndReplies . insertReplies")

    try:my_comment_dictionary_replies = insertReplies(publisher_id, comment_set_id, my_comment_dictionary)
    except ClientError as e:
        print("ApiCommentThread . GET . 4 . insertCommentVotesAndReplies . insertReplies . FAILURE")
        return my_comment_dictionary
    else:
        print("ApiCommentThread . GET . 4 . insertCommentVotesAndReplies . insertReplies . SUCCESS")
        return my_comment_dictionary_replies

def insertCommentVotes(publisher_id, comment_set_id, my_comment_dictionary):

    print("ApiCommentThread . GET . 4 . insertCommentVotes")

    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('COMMENTS_VOTES')

    comment_set_threads_NEW = []
    array_of_comments = my_comment_dictionary["COMMENT_SET_THREADS"]
    for this_comment in array_of_comments:

        comment_id = this_comment["COMMENT_ID"]

        try:responseQUERY = table.query(KeyConditionExpression=Key('PUBLISHER_ID').eq(publisher_id) & Key('COMMENT_ID').eq(comment_id))
        except ClientError as error:
            print("ApiCommentThread . GET . 4 . insertCommentVotes . FAILURE . error = {0}".format(error))
            comment_set_threads_NEW.append(this_comment)
        else:
            print("ApiCommentThread . GET . 4 . insertCommentVotes . FOUND . responseQUERY = {0}".format(responseQUERY))
            if responseQUERY["Count"] > 0:
                comments_votes_item = responseQUERY['Items'][0]
                this_comment["COMMENT_VOTES_UP"] = comments_votes_item["COMMENT_VOTES_UP"]
                this_comment["COMMENT_VOTES_DOWN"] = comments_votes_item["COMMENT_VOTES_DOWN"]
            else:
                this_comment["COMMENT_VOTES_UP"] = "0"
                this_comment["COMMENT_VOTES_DOWN"] = "0"

            comment_set_threads_NEW.append(this_comment)

    # for statement ends here

    my_comment_dictionary["COMMENT_SET_THREADS"] = comment_set_threads_NEW
    return my_comment_dictionary

def insertReplies(publisher_id, comment_set_id, my_comment_dictionary):

    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('COMMENTS_REPLIES')

    print("ApiCommentThread . GET . 4 . insertReplies")
    # print("ApiCommentThread . GET . 4 . insertReplies . my_comment_dictionary: {0}".format(my_comment_dictionary))

    comment_set_threads_NEW = []
    array_of_comments = my_comment_dictionary["COMMENT_SET_THREADS"]
    for this_comment in array_of_comments:

        reply_set_id = this_comment["COMMENT_ID"]

        try:responseQUERY = table.query(
            KeyConditionExpression=Key('PUBLISHER_ID').eq(publisher_id) & Key('REPLY_SET_ID').eq(reply_set_id),
            Limit=2)
        except ClientError as error:
            comment_set_threads_NEW.append(this_comment)
        else:
            print("ApiCommentThread . GET . 4 . insertReplies . FOUND")
            if responseQUERY["Count"] > 0:
                array_of_reply_set_threads = responseQUERY['Items'][0]["REPLY_SET_THREADS"] # THIS LOOKS SILLY BC DYNAMO HAS NESTS
                this_first_reply = array_of_reply_set_threads[0]
                this_comment["COMMENT_REPLY_COUNT"] = str(len(array_of_reply_set_threads))
                this_comment["COMMENT_THREAD_FIRST_REPLY"] = this_first_reply
            else:
                this_comment["COMMENT_REPLY_COUNT"] = "0"

            comment_set_threads_NEW.append(this_comment)

    # for statement ends here

    my_comment_dictionary["COMMENT_SET_THREADS"] = comment_set_threads_NEW
    return my_comment_dictionary


def updateCommentsWithDictionary(publisher_id, comment_set_id, my_comment_dictionary):

    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('COMMENTS')

    try:resultUPDATE = table.update_item(
        Key={'PUBLISHER_ID': publisher_id, 'COMMENT_SET_ID': comment_set_id},
        UpdateExpression="SET COMMENT_SET_THREADS = list_append(:i, COMMENT_SET_THREADS)",
        ExpressionAttributeValues={':i': [my_comment_dictionary],},
        ReturnValues="UPDATED_NEW"
    )
    except ClientError as e:
        print("ApiCommentThread . POST . 4 . updateCommentsWithDictionary . FAILURE")
        return False
    else:
        print("ApiCommentThread . POST . 4 . updateCommentsWithDictionary . SUCCESS")
        return True


def updateCommentsRepliesWithDictionary(publisher_id, reply_set_id, my_comment_dictionary):

    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('COMMENTS_REPLIES')

    try:resultUPDATE = table.update_item(
        Key={'PUBLISHER_ID': publisher_id, 'REPLY_SET_ID': reply_set_id},
        UpdateExpression="SET REPLY_SET_THREADS = list_append(if_not_exists(REPLY_SET_THREADS, :empty), :i)",
        ExpressionAttributeValues={':i': [my_comment_dictionary], ':empty': [],},
        ReturnValues="UPDATED_NEW"
    )
    except ClientError as e:
        return False
    else:
        return True


""" ________ ________ ________ ________ ________ ________ ________ ________ ________ ________ ________ ________ ________ ________ """


# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)
