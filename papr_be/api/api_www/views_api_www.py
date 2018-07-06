# -*- coding: utf-8 -*-
from __future__ import unicode_literals
#
from django.conf.urls import url
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
# DRF
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from rest_framework import filters
# BOTO
import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
# OTHER
# from . import serializers
# from . import models
# from . import permissions
from papr_be import settings
# from .models import UserAccount
import json
import psycopg2
from psycopg2.extras import RealDictCursor
import string
import datetime
import html

# Create your views here.

class ApiShare(APIView):
    """ SHARE API View """
    if (settings.DEBUG):
        permission_classes = (AllowAny,)

    def get(self, request, format=None):
        """ Return shorty_dictionary For url_shorty """

        print("ApiShare . GET . 1")

        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('SHARE_URLS')

        url_shorty = request.GET.get('url_shorty')
        publisher_id = request.GET.get('publisher_id')

        print("ApiShare . GET . 2 . url_shorty = {0}".format(url_shorty))

        try:responseQUERY = table.query(KeyConditionExpression=Key('PUBLISHER_ID').eq(publisher_id) & Key('URL_SHORTY').eq(url_shorty))
        except ClientError as e:

            print("ApiCommentsVotes . GET . 3 . NOT FOUND . FAILURE")
            responseDictionary = {"success":"0"}
            return Response(json.dumps(responseDictionary, indent=0))

        else:

            print("ApiCommentsVotes . GET . 3 . FOUND")
            print("ApiCommentsVotes . GET . 3 . FOUND . responseQUERY = {0}".format(responseQUERY))
            items = responseQUERY['Items']
            shorty_dictionary = items[0]
            responseDictionary = {"success":"1", "shorty_dictionary":shorty_dictionary}
            return Response(json.dumps(responseDictionary, indent=0))

    def post(self, request, format=None):
        """ Create/Return shorty_dictionary """

        print("ApiShare . POST . 1")

        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('SHARE_URLS')

        url_actual = request.data.get('url_actual', None)
        url_shorty = request.data.get('url_shorty', None)
        post_title = request.data.get('post_title', None)
        post_image_url = request.data.get('post_image_url', None)
        publisher_id = request.data.get('post_publisher', None)
        shorty_dictionary = {"PUBLISHER_ID":publisher_id, "URL_SHORTY":url_shorty, "URL_ACTUAL":url_actual, "POST_TITLE":post_title, "POST_IMAGE_URL":post_image_url}

        try:responseQUERY = table.query(KeyConditionExpression=Key('PUBLISHER_ID').eq(publisher_id) & Key('URL_SHORTY').eq(url_shorty))
        except ClientError as e:

            print("ApiShare . POST . 3 . NOT FOUND")
            responseDictionary = {"success":"0"}
            return Response(json.dumps(responseDictionary, indent=0))

        else:

            items = responseQUERY['Items']
            if items:

                responseDictionary = {"success":"1", "shorty_dictionary":shorty_dictionary}
                return Response(json.dumps(responseDictionary, indent=0))

            else:

                try:responsePUT = table.put_item(Item=shorty_dictionary)
                except ClientError as error:
                    print("ApiShare . POST . 3 . put shorty_dictionary . error = {0}".format(error))
                    responseDictionary = {"success":"0"}
                    return Response(json.dumps(responseDictionary, indent=0))
                else:
                    print("ApiShare . POST . 3 . put shorty_dictionary . SUCCESS")
                    responseDictionary = {"success":"1", "shorty_dictionary":shorty_dictionary}
                    return Response(json.dumps(responseDictionary, indent=0))

class ApiShareView(APIView):
    """ SHARE View API """
    if (settings.DEBUG):
        permission_classes = (AllowAny,)

    def get(self, request, format=None):
        """ Return shorty_dictionary For url_shorty """

        print("ApiShareView . GET . 1")

        url_shorty = request.GET.get('url_shorty')
        publisher_id = request.GET.get('publisher_id')

        return render(request, 'article/index.html')



def www_article(request):

    article_url = request.GET.get('article_url', '')

    return render(request, 'article/index.html')

def www_home(request):

    return render(request, 'home/index.html')

def www_invite(request):

    return render(request, 'invite/index.html')


def www_share(request):

    print("www_share . 1")

    url_path = request.__dict__['path_info']
    url_shorty = url_path[3:15]
    publisher_shorty = url_path[3:7]

    print("www_share . 2 . publisher_shorty = {0}".format(publisher_shorty))

    try:publisher_id = www_share_decoder(publisher_shorty)
    except ClientError as e:
        pass
    else:
        pass

    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('SHARE_URLS')

    try:responseQUERY = table.query(KeyConditionExpression=Key('PUBLISHER_ID').eq(publisher_id) & Key('URL_SHORTY').eq(url_shorty))
    except ClientError as e:

        return render(request, 'article/index.html', {"OG_TITLE":"FAIL Jose's Beach at Rockaway", "OG_IMAGE":"https://static01.nyt.com/images/2018/05/26/opinion/26sat1-2/26sat1-2-facebookJumbo.jpg"})

    else:

        items = responseQUERY['Items']
        if items:
            shorty_dictionary = items[0]
            print("www_share . 3 . FOUND . shorty_dictionary = {0}".format(shorty_dictionary))
            return render(request, 'article/index.html', {
            "OG_TITLE":shorty_dictionary["POST_TITLE"],
            "OG_IMAGE":shorty_dictionary["POST_IMAGE_URL"],
            "OG_URL":shorty_dictionary["URL_ACTUAL"]})
            # JUST IN CASE: "OG_IMAGE":html.unescape(shorty_dictionary["POST_IMAGE_URL"])
        else:
            print("www_share . 3 . EMPTY")
            # OPTIONAL: CREATE DEFAULT PAPR IMAGES / TEXT?
            # return render(request, 'article/index.html', {"OG_TITLE":shorty_dictionary[POST_TITLE], "OG_IMAGE":shorty_dictionary[POST_IMAGE_URL]})
            pass

    return render(request, 'article/index.html')


def www_share_decoder(url_shorty):

    arrayNumbers = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"];
    arrayPublisherBase62 = ["k", "l", "m", "n", "o", "p", "q", "r", "s", "t"];
    publisher_id_PRE = "p700"
    publisher_id_decoded = ""

    for code in url_shorty:
        index = arrayPublisherBase62.index(code)
        publisher_id_decoded = arrayNumbers[index] + publisher_id_decoded

    publisher_id = publisher_id_PRE + publisher_id_decoded

    return publisher_id


def www_universal_links(request):

    return render(request, 'home/apple-app-site-association')
