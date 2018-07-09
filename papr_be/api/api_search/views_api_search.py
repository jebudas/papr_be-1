# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from papr_be import settings
# DRF
from rest_framework.views import APIView
from rest_framework.response import Response
# BOTO
import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
# OTHER
import json
import psycopg2
import decimal
import time
import urllib.parse


class ApiSearch(APIView):

    def get(self, request, format=None):
        """ Return a list of API features """

        print("ApiSearch . GET . 1")

        dbHost     = settings.DATABASES['default']['HOST']
        dbUsername = settings.DATABASES['default']['USER']
        dbPassword = settings.DATABASES['default']['PASSWORD']
        dbName     = settings.DATABASES['default']['NAME']

        conn_string = ("host='{0}' dbname='{1}' user='{2}' password='{3}'".format(dbHost,dbName,dbUsername,dbPassword))
        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()

        print("ApiSearch . GET . 2")
        search_text = request.GET.get('search_text')
        search_type = request.GET.get('search_type')
        print("ApiSearch . GET . 3 . search_text = {0}, search_type = {1}".format(search_text, search_type))

        search_row = "user_username"
        if search_type == "hashtag":
            search_row = "user_hastags"

        execution_string = "SELECT user_fb_id, user_username, user_profile from api_user_useraccount WHERE LOWER({0}) LIKE LOWER(\'{1}%\')".format(search_row, search_text)

        print("ApiSearch . GET . 3 . execution_string = {0}".format(execution_string))

        cursor.execute(execution_string)
        records = cursor.fetchall()

        records_updated = []
        for this_record in records:
            # print("ApiSearch . GET . 4 . this_record = {0}".format(this_record))
            this_record_profile = eval(this_record[2])
            # print("ApiSearch . GET . 5 . this_record_profile = {0}".format(this_record_profile))
            this_record_dictionary = {
                "user_fb_id": this_record[0],
                "publisher_username" : this_record[1],
                "publisher_display_name" : this_record_profile["user_profile_display_name"],
                "publisher_avatar" : this_record_profile["user_profile_avatar_url"]}

            print("ApiSearch . GET . 6 . this_record_dictionary = {0}".format(this_record_dictionary))

            records_updated.append(this_record_dictionary)

        print("ApiSearch . GET . 7 . records_updated = {0}".format(records_updated))

        responseDictionary = {"success":"?", "records_updated":records_updated}
        print("ApiSearch . GET . 4 . responseDictionary = {0}".format(responseDictionary))
        #return Response(json.dumps(responseDictionary, indent=0))
        return Response(responseDictionary)


class ApiGetFeatured(APIView):

    def get(self, request, format=None):
        """ GET Signup Subscriptions """

        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('CONSTANTS')

        try:responseGET = table.get_item(Key={'KEY': 'API_FEATURED_DICTIONARIES'})
        except ClientError as error:
            print("ApiGetFeatured . API_FEATURED_DICTIONARIES ERROR: {0}".format(error))
            return []
        else:
            if responseGET['Item']:
                responseDictionary = responseGET['Item']
                featured_array = responseDictionary['VALUABLE']
                print("ApiGetFeatured . returnArrayOfApiFeatured . 2 . responseGET['Item'] = {0}".format(featured_array))
                return Response({"success":"1", "featuredDictionary" : featured_array})
            else:
                print("ApiGetFeatured . API_FEATURED_DICTIONARIES ERROR: MISSING ITEM")
                return []















"""
BREATHE
"""
