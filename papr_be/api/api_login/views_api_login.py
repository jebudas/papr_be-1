# -*- coding: utf-8 -*-
from __future__ import unicode_literals
#
from django.conf.urls import url
from django.http import HttpResponse, HttpRequest
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
# DRF
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers
from rest_framework.renderers import JSONRenderer
# BOTO
import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
# OTHER
import json
import psycopg2
from . import serializers
from papr_be import settings
from api.api_user.views_api_user import ApiUser
#import re
import string


class ApiCreateUser(APIView):
    """ Create User """

    def post(self, request, format=None):
        print("ApiCreateUser(LOGIN) . POST . 1")


class ApiViewAuthCode(APIView):
    """ Test API View """

    serializer_class = serializers.AuthCodeSerializer

    def get(self, request, format=None):
        """ Return a list of API features """

        array_of_names = ['jose', 'juanita', 'juan']

        return Response({'success':True, 'array_of_names' : array_of_names})

    def post(self, request, format=None):
        """ Return received Auth Code """

        # {"authcode":"7"}

        serializer = serializers.AuthCodeSerializer(data=request.data)

        if serializer.is_valid():
            authcode = serializer.data.get('authcode')
            message = "{0}".format(authcode)
            return Response({'authcode':message})
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class HelloApiView(APIView):
    """ Test API View """

    def get(self, request, format=None):
        """ Return a list of API features """

        dbHost     = settings.DATABASES['default']['HOST']
        dbUsername = settings.DATABASES['default']['USER']
        dbPassword = settings.DATABASES['default']['PASSWORD']
        dbName     = settings.DATABASES['default']['NAME']

        conn_string = ("host='{0}' dbname='{1}' user='{2}' password='{3}'".format(dbHost,dbName,dbUsername,dbPassword))
        print(conn_string)
        print('NOTE: ____________________________________________________ PostgreSQL database version: ')
        #conn_string = "host='localhost' dbname='iotd' user='jebudas' password='Postgres1234'"
        # print the connection string we will use to connect
        # print "Connecting to database\n	->%s" % (conn_string)

        # get a connection, if a connect cannot be made an exception will be raised here
        conn = psycopg2.connect(conn_string)

        # conn.cursor will return a cursor object, you can use this cursor to perform queries
        cursor = conn.cursor()

        # execute our Query
        cursor.execute("SELECT * FROM api_user_useraccount")

        # retrieve the records from the database
        records = cursor.fetchall()

        # print out the records using pretty print
        # note that the NAMES of the columns are not shown, instead just indexes.
        # for most people this isn't very useful so we'll show you how to return
        # columns as a dictionary (hash) in the next example.
        print(records)

        return Response({'success':True, 'db_connected' : records})




    def post(self, request, format=None):
        """ Return received Auth Code """

        return Response({'success':True, 'authcode' : request.POST['authcode']})


def usernameIsAvailable(username):

        print("Hello SIGNUP . 2 . usernameIsAvailable")

        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('USERNAMES')
        USERNAME_LETTER = username[0]

        try:response = table.query(KeyConditionExpression=Key('USERNAME_LETTER').eq(USERNAME_LETTER) & Key('USERNAME_ACTUAL').eq(username))
        except ClientError as e:
            return False
        else:
            items = response['Items']
            if items:
                return False
            else:
                return True




# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)
