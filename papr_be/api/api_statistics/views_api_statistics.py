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


class ApiStatisticsViews(APIView):
    """ Statistics API """
    if (settings.DEBUG):
        permission_classes = (AllowAny,)

    def get(self, request, format=None):
        """ Return a list of User Stats """

        print("ApiStatistics . GET . 1")
        print("ApiStatistics . GET . 1 . request = {0}".format(request))
        print("ApiStatistics . GET . 1 . request.GET = {0}".format(request.GET))

        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('STATISTICS')

        post_id = request.GET.get('post_id')
        publisher_id = request.GET.get('publisher_id')

        print("ApiStatistics . GET . 2 . post_id = {0}".format(post_id))

        try:response = table.query(KeyConditionExpression=Key('PUBLISHER_ID').eq(publisher_id) & Key('POST_ID').eq(post_id))
        except ClientError as e:
            print("ApiStatistics . GET . 3 . FAILURE")
            responseDictionary = {"success":"0"}
            return Response(json.dumps(responseDictionary, indent=0))
        else:
            print("ApiStatistics . GET . 3 . SUCCESS . response = {0}".format(response))
            items = response['Items']
            item_stats_dictionary = items[0]
            responseDictionary = {"success":"1", "item_stats_dictionary":item_stats_dictionary}
            return Response(json.dumps(responseDictionary, indent=0))

    def post(self, request, format=None):
        """ UPDATE STATS . VIEWS """

        print("ApiStatisticsViews . POST . 1")

        if request.data.get('stats_dictionary'):
            print("ApiStatisticsViews . POST . 2")
            stats_dictionary = request.data.get('stats_dictionary', None)
            post_id = stats_dictionary['post_id']
            publisher_id = stats_dictionary['publisher_id']
            type_field = "views"

            try:responseDictionary = updateStatViews(publisher_id, post_id, type_field)
            except ClientError as error:
                print("ApiStatisticsViews . POST . 3 . FAILURE . Error = {0}".format(error))
                responseDictionary = {"success":"0"}
                return Response(json.dumps(responseDictionary, indent=0))
            else:
                print("ApiStatisticsViews . POST . 3 . SUCCESS")
                return Response(json.dumps(responseDictionary, indent=0))

        else:
            responseDictionary = {"success":"0", "request.data":request.data}
            return Response(json.dumps(responseDictionary, indent=0))


class ApiStatistics(APIView):
    """ Statistics API """

    def get(self, request, format=None):
        """ Return a list of User Stats """

        print("ApiStatistics . GET . 1")
        print("ApiStatistics . GET . 1 . request = {0}".format(request))
        print("ApiStatistics . GET . 1 . request.GET = {0}".format(request.GET))

        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('STATISTICS')

        post_id = request.GET.get('post_id')
        publisher_id = request.GET.get('publisher_id')

        print("ApiStatistics . GET . 2 . post_id = {0}".format(post_id))

        try:response = table.query(KeyConditionExpression=Key('PUBLISHER_ID').eq(publisher_id) & Key('POST_ID').eq(post_id))
        except ClientError as e:
            print("ApiStatistics . GET . 3 . FAILURE")
            responseDictionary = {"success":"0"}
            return Response(json.dumps(responseDictionary, indent=0))
        else:
            print("ApiStatistics . GET . 3 . SUCCESS . response = {0}".format(response))
            items = response['Items']
            item_stats_dictionary = items[0]
            responseDictionary = {"success":"1", "item_stats_dictionary":item_stats_dictionary}
            return Response(json.dumps(responseDictionary, indent=0))

    def post(self, request, format=None):
        """ PUBLISH COMMENT """

        print("ApiStatistics . POST . 1")

        if request.data.get('stats_dictionary'):
            stats_dictionary = request.data.get('stats_dictionary', None)
            print("ApiStatistics . POST . 2 . stats_dictionary = {0}".format(stats_dictionary))
            type_field = stats_dictionary['type_field']
            publisher_id = stats_dictionary['publisher_id']

            if type_field == "views":
                """ ENUMERATE THROUGH ARRAY, UPDATE STATS """
                post_id_array = stats_dictionary['post_id_array']

                for this_post_id in post_id_array:

                    updateStatViews(publisher_id, this_post_id, type_field)

            elif type_field == "comments":

                post_id = stats_dictionary['comment_id']
                updateStatViews(publisher_id, post_id, type_field)

            elif type_field == "likes":

                post_id = stats_dictionary['post_id']
                updateStatViews(publisher_id, post_id, type_field)

            elif type_field == "reposts":

                post_id = stats_dictionary['post_id']
                updateStatViews(publisher_id, post_id, type_field)

            else:

                print("ApiStatistics . POST . 3 . type_field<NOPE> = {0}".format(type_field))

        responseDictionary = {"success":"0", "request.data":request.data}
        return Response(json.dumps(responseDictionary, indent=0))




""" THESE FUNCTIONS HAVE NO CLASS. AHEM. """

def updateCommentsVotes(array_of_votes, vote_type):

    if request.data.getlist('votes[]'):

        print("ApiStatistics . POST . 3 . updateCommentsVotes")
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('COMMENTS_VOTES')

        for this_comment_id in array_of_votes:

            temp_array = this_comment_id.split('-')
            publisher_id = temp_array[0]

            try:responseQUERY = table.query(KeyConditionExpression=Key('PUBLISHER_ID').eq(publisher_id) & Key('COMMENT_ID').eq(this_comment_id))
            except ClientError as error:
                print("ApiCommentsVotes . POST . 3 . NOT FOUND . CREATING NEW")
                this_votes_dictionary = {"COMMENT_ID":this_comment_id, "COMMENT_VOTES_DOWN":"0", "COMMENT_VOTES_UP":"0", "PUBLISHER_ID":publisher_id}
            else:
                print("ApiCommentsVotes . POST . 3 . FOUND")
                # print("ApiCommentsVotes . POST . 3 . FOUND . responseQUERY = {0}".format(responseQUERY))
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
                continue

            try:responsePUT = table.put_item(Item=this_votes_dictionary)
            except ClientError as error:
                print("ApiStatistics . POST . 3 . updateCommentsVotes . Error = {0}".format(error))
                pass
            else:
                print("ApiStatistics . POST . 3 . updateCommentsVotes . SUCCESS")
                pass


def updateStatTotals(publisher_id, post_id, type_field):

    print("ApiStatistics . POST . updateStatTotals . 1")

    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('STATISTICS')

    try:response = table.query(KeyConditionExpression=Key('PUBLISHER_ID').eq(publisher_id) & Key('POST_ID').eq(post_id))
    except ClientError as e:
        responseDictionary = {"success":"0"}
        return Response(json.dumps(responseDictionary, indent=0))
    else:
        print("ApiStatistics . POST . updateStatTotals . SUCCESS")

def updateStatViews(publisher_id, post_id, type_field):

    print("ApiStatisticsViews . updateStatViews . 1")

    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('STATISTICS')

    try:response = table.query(KeyConditionExpression=Key('PUBLISHER_ID').eq(publisher_id) & Key('POST_ID').eq(post_id))
    except ClientError as error:
        print("ApiStatisticsViews . updateStatViews . 2 . Error = {0}".format(error))
        responseDictionary = {"success":"0"}
        return False
    else:
        print("ApiStatisticsViews . updateStatViews . 2")
        items = response['Items']
        item_stats_dictionary = items[0]
        new_stats = item_stats_dictionary['STATS']
        del item_stats_dictionary['STATS']
        # views, likes, reposts, comments
        stat = new_stats[type_field]
        int_stat = int(stat)
        int_stat = int_stat + 1
        stat = str(int_stat)
        new_stats[type_field] = str(int_stat)
        item_stats_dictionary['STATS'] = new_stats

        try:responsePUT = table.put_item(Item=item_stats_dictionary)
        except ClientError as error:
            print("ApiStatisticsViews . updateStatViews . 3 . Error = {0}".format(error))
            return False
        else:
            print("ApiStatisticsViews . updateStatViews . 3 . SUCCESS")
            responseDictionary = {"success":"1", "stats_dictionary":item_stats_dictionary}
            return responseDictionary



"""
    #try:response = table.query(KeyConditionExpression=Key('PUBLISHER_ID').eq(publisher_id) & Key('COMMENT_ID').eq(comment_id))
    try:result = table.update_item(
            Key={'PUBLISHER_ID': publisher_id, 'POST_ID': post_id},
            UpdateExpression="SET COMMENTS = list_append(if_not_exists(COMMENTS, :empty_list), :i)",
            ExpressionAttributeValues={
                ':i': [comment_dictionary],
                ":empty_list":[],
            },
            ReturnValues="UPDATED_NEW"
        )
    except ClientError as e:
        print("ApiStatistics . POST . 4 . FAILURE = ClientError: {0}".format(e.response['Error']['Message']))
        responseDictionary = {"success":"0"}
        return Response(json.dumps(responseDictionary, indent=0))
    else:
        if result['ResponseMetadata']['HTTPStatusCode'] == 200 and 'Attributes' in result:
            print("ApiStatistics . POST . 4 . SUCCESS")
            try:response = table.query(KeyConditionExpression=Key('PUBLISHER_ID').eq(publisher_id) & Key('COMMENT_ID').eq(comment_id))
            except ClientError as e:
                return False
            else:
                print("ApiStatistics . POST . 5 . SUCCESS")
                #item = response['Item']
                #print(json.dumps(item, indent=4, cls=DecimalEncoder))
                return Response(str(json.dumps(response, cls=DecimalEncoder)))
        else:
            print("ApiStatistics . POST . 4 . FAILURE")
            responseDictionary = {"success":"0"}
            return Response(json.dumps(responseDictionary, indent=0))

"""
