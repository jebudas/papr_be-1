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
# WWW
from django import forms
from .forms_api_user import FormInviteRequest
# OTHER
from . import serializers
from . import models
from . import permissions
from papr_be import settings
from .models import UserAccount
import json
import psycopg2
from psycopg2.extras import RealDictCursor
import string
import datetime

# Create your views here.

class ApiCreateUser(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, format=None):
        """ CREATE USER """
        print("ApiCreateUser . POST . 1")

        # COLLECT POST DATA
        userDictionary = request.data
        username = userDictionary.get('user_username_TEST', None)
        username_original = userDictionary.get('user_username', None)
        user_profile_avatar_url = userDictionary.get('user_profile_avatar_url', None)
        user_profile_display_name = userDictionary.get('user_profile_display_name', None)
        secret_timecode = userDictionary.get('fb_timestamp', None)

        print("ApiCreateUser . create_papr_user . rejectIfCodeIsBogus . START")
        if rejectIfCodeIsBogus(secret_timecode):
            responseDictionary = {"status":"HTTP 401 Unauthorized"}
            return Response(json.dumps(responseDictionary, indent=0))

        print("ApiCreateUser . create_papr_user . rejectIfAllDataIsNotReady . START")
        # CHECKING INTEGRITY . ALL DATA IS PRESENT
        if rejectIfAllDataIsNotReady(userDictionary):
            responseDictionary = {"success":"0", "error_level" : "large", "message" : "We are missing data."}
            return Response(json.dumps(responseDictionary, indent=0))

        print("ApiCreateUser . create_papr_user . rejectIfUsernameIsImproperLength . START")
        # CHECKING INTEGRITY . No SHORTIES / LONGIES
        if rejectIfUsernameIsImproperLength(username):
            responseDictionary = {"success":"0", "error_level" : "small", "message" : "Please use a shorter username."}
            return Response(json.dumps(responseDictionary, indent=0))

        print("ApiCreateUser . create_papr_user . rejectIfUsernameIsNotAvailable . START")
        # CHECKING INTEGRITY . No DUPS
        if rejectIfUsernameIsNotAvailable(username):
            print("ApiCreateUser . create_papr_user . rejectIfUsernameIsNotAvailable . STOP")
            responseDictionary = {"success":"0", "error_level" : "small", "message" : "Username is already taken. Please try another."}
            return Response(json.dumps(responseDictionary, indent=0))

        print("ApiCreateUser . create_papr_user . rejectIfUsernameIsWacky . START")
        # CHECKING INTEGRITY . No WACKO CHARACTERS
        if rejectIfUsernameIsWacky(username):
            responseDictionary = {"success":"0", "error_level" : "small", "message" : "Please use letters, numbers, underscores, dashes, and periods only."}
            return Response(json.dumps(responseDictionary, indent=0))

        print("ApiCreateUser . create_papr_user . new_user_create. START")
        print("ApiCreateUser . create_papr_user . new_user_create. START . userDictionary = {0}".format(userDictionary))
        # LET'S ADD A USER!
        new_user = UserAccount()
        new_user.user_username = username_original
        new_user.email = "{0}@papr.co".format(username)
        new_user.user_fb_id = userDictionary.get('fb_user_id', "ILLEGAL-ID")
        new_user.user_fb_phone = userDictionary.get('fb_phone_number', "ILLEGAL-PHONE")
        new_user.user_creation_date = datetime.datetime.now()
        new_user.is_active = True
        new_user.is_private = False
        new_user.user_profile = userDictionary.get('user_profile', {"user_profile_display_name":user_profile_display_name, "user_profile_avatar_url":user_profile_avatar_url})
        new_user.user_settings = userDictionary.get('user_settings', {"user_settings":"empty"})
        new_user.user_location = userDictionary.get('user_location', {"user_location":"empty"})

        print("ApiCreateUser . create_papr_user . new_user_save. START")
        # CONFIRM SAVE PROCDURE
        try:new_user.save()
        except ClientError as e:
            print("ApiCreateUser . create_papr_user . 7_NO")
            responseDictionary = {"success":"0", "error_level" : "large", "message" : "There was a problem creating your account (RDS)."}
            return Response(json.dumps(responseDictionary, indent=0))
        else:
            print("ApiCreateUser . create_papr_user . writeUsernameToDynamoDB . START")
            writeUsernameToDynamoDB(username)
            print("ApiCreateUser . create_papr_user . SUCCESS")
            token, _ = Token.objects.get_or_create(user=new_user)
            responseDictionary = {"success":"1", "error_level" : "none", "user_token":token.key, "message" : "User Has Been Created!"}
            return Response(json.dumps(responseDictionary, indent=0))

    def get(self, request, format=None):
        """ GET USER """

        # COLLECT GET DATA
        print("ApiCreateUser . GET . 1")
        print("ApiCreateUser . GET . 2 . secret_timecode = {0}".format(request.GET.get('secret_timecode')))

        secret_timecode = request.GET.get('secret_timecode')

        print("ApiCreateUser . GET . 3 . rejectIfCodeIsBogus . START")
        if rejectIfCodeIsBogus(secret_timecode):
            responseDictionary = {"status":"HTTP 401 Unauthorized"}
            return Response(json.dumps(responseDictionary, indent=0))

        print("ApiCreateUser . GET . 4")
        print("HEY WE'RE TESTING GIMME A BREAK!! STATIC_ROOT = {0}".format(settings.STATIC_ROOT))
        now = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        get_username = "jose_{0}".format(now)
        get_fb_user_id = "fb_{0}".format(now)
        get_fb_phone_number = "ph_{0}".format(now)
        get_fb_timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M17')

        testDictionary = {"user_username":get_username, "fb_user_id":get_fb_user_id, "fb_phone_number":get_fb_phone_number, "fb_timestamp":get_fb_timestamp}
        return Response({"success":"0", "error_level" : "large", "test_dictionary" : testDictionary})

class ApiRequestPublisherAbility(APIView):

    def post(self, request, format=None):
        """ Save PAPR to Archive """

        print("ApiRequestPublisherAbility . POST . 1")

        if request.data.get('publisher_id'):
            publisher_id = request.data.get("publisher_id")
            request_text = request.data.get("request_text")

            print("ApiRequestPublisherAbility . POST . 2 . publisher_id = {0}".format(publisher_id))

            dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
            table = dynamodb.Table('REQUEST_PUBLISHER_ABILITY')

            try:resultPUT = table.put_item(Item={'PUBLISHER_ID': publisher_id, 'REQUEST_TEXT': request_text, 'STATUS': "pending"})
            except ClientError as error:
                print("ApiRequestPublisherAbility . POST . 3 . FAILURE")
                responseDictionary = {"success":"0"}
                return Response(json.dumps(responseDictionary, indent=0))
            else:
                print("ApiRequestPublisherAbility . POST . 3 . SUCCESS")
                responseDictionary = {"success":"1"}
                return Response(json.dumps(responseDictionary, indent=0))


class ApiUpdateUser(APIView):

    def post(self, request, format=None):
        """ CREATE USER """

        # COLLECT POST DATA
        userDictionary = request.data
        print("ApiUpdateUser . START . userDictionary = {0}".format(userDictionary))
        username = userDictionary.get('user_username', None)
        print("ApiUpdateUser . POST_01 . username = {0}".format(username))

        user_updated = UserAccount.objects.get(user_username = username)

        if user_updated:

            print("ApiUpdateUser . POST_02 . user_location = {0}".format(user_updated.user_location))
            user_updated.email = "{0}@papr.co".format(username)
            user_updated.is_private = userDictionary.get('is_private', False)
            user_updated.user_profile = userDictionary.get('user_profile', {"user_profile":"empty"})
            user_updated.user_settings = userDictionary.get('user_settings', {"user_settings":"empty"})
            user_updated.user_location = userDictionary.get('user_location', {"user_location":"empty"})

            print("ApiUpdateUser . POST_02 . userDictionary.user_settings = {0}".format(userDictionary.get('user_settings')))
            print("ApiUpdateUser . POST_02 . user_updated.user_settings = {0}".format(user_updated.user_settings))

            print("ApiUpdateUser . POST_03 . SAVE . START")
            # CONFIRM SAVE PROCDURE
            try:user_updated.save()
            except ClientError as e:
                print("ApiUpdateUser . POST_03 . SAVE . START . FAIL")
                responseDictionary = {"success":"0", "error_level" : "large", "message" : "There was a problem updating your account (RDS)."}
                return Response(json.dumps(responseDictionary, indent=0))
            else:
                print("ApiUpdateUser . POST_03 . SAVE . START . SUCCESS")
                responseDictionary = {"success":"1", "message" : "User Has Been Updated!"}
                return Response(json.dumps(responseDictionary, indent=0))

        else:
            print("ApiUpdateUser . POST_02 . user_updated = FAILURE")
            return Response({"success":"0"})

class ApiSignupSubscriptions(APIView):

    def get(self, request, format=None):
        """ GET Signup Subscriptions """

        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('CONSTANTS')

        try:responseGET = table.get_item(Key={'KEY': 'API_SUBSCRIPTION_DICTIONARIES'})
        except ClientError as error:
            print("ApiSignupSubscriptions . API_SUBSCRIPTION_DICTIONARIES ERROR: {0}".format(error))
            return []
        else:
            if responseGET['Item']:
                responseDictionary = responseGET['Item']
                subscriptionArray = responseDictionary['VALUABLE']
                # print("ApiSignupSubscriptions . returnArrayOfApiSubscriptions . 2 . responseGET['Item'] = {0}".format(subscriptionArray))
                return Response({"success":"1", "subscriptionDictionary" : subscriptionArray})
            else:
                print("ApiSignupSubscriptions . API_SUBSCRIPTION_DICTIONARIES ERROR: MISSING ITEM")
                return []

class ApiUser(APIView):
    """ User API View """

    serializer_class = serializers.UserAccountSerializer
    queryset = models.UserAccount.objects.all()

    def get(self, request, format=None):
        """ GET USER """

        print("ApiUser . GET . 1 . user_id = {0}".format(request.GET.get('user_id')))

        if request.GET.get('user_id'):

            user_id = request.GET.get('user_id', '1')

            dbHost     = settings.DATABASES['default']['HOST']
            dbUsername = settings.DATABASES['default']['USER']
            dbPassword = settings.DATABASES['default']['PASSWORD']
            dbName     = settings.DATABASES['default']['NAME']

            connection_string = ("host='{0}' dbname='{1}' user='{2}' password='{3}'".format(dbHost,dbName,dbUsername,dbPassword))
            connection = psycopg2.connect(connection_string)
            cursor = connection.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT * FROM api_user_useraccount WHERE user_fb_id = \'{0}\';".format(user_id))
            records = cursor.fetchall()
            user_dictionary = records[0]
            print("ApiUser . GET . 4 . user_dictionary.user_username = {0}".format(user_dictionary['user_username']))
            connection.close()
            cursor.close()

            if user_dictionary['user_username']:

                user_profile = user_dictionary['user_profile']
                user_settings = user_dictionary['user_settings']
                user_location = user_dictionary['user_location']

                print("ApiUser . GET . 4 . user_profile = {0}".format(user_profile))

                user_dictionary_censored = {
                    "user_id":user_dictionary['user_fb_id'],
                    "user_username":user_dictionary['user_username'],
                    "user_profile":json.loads(user_profile),
                    "user_settings":json.loads(user_settings),
                    "user_location":json.loads(user_location)
                }

                responseDictionary = {'success':True, "db_connected":user_dictionary_censored}
                return Response(json.dumps(responseDictionary, indent=0))

            else:
                return Response({'success':False, 'db_connected' : "MISSING DATA!"})

        else:

            return Response({'success':False, 'db_connected' : "NEED user_id !"})

class ApiUserFollowers(APIView):
    """ User FOLLOWERS updates """

    def get(self, request, format=None):
        """ List FOLLOWERS for USER """

        publisher_id = request.GET.get('publisher_id')

        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('FOLLOWERS')

        try:list_of_followers = table.get_item(Key={'PUBLISHER_ID': publisher_id})
        except ClientError as error:
            responseDictionary = {"success":"0"}
            return Response(json.dumps(responseDictionary, indent=0))
        else:
            if 'Item' in list_of_followers:
                item_dictionary = list_of_followers['Item']
                responseDictionary = {"success":"1", "item_dictionary":item_dictionary}
                return Response(json.dumps(responseDictionary, indent=0))
            else:
                responseDictionary = {"success":"ApiUserFollowers . GET . ELSE"}
                return Response(json.dumps(responseDictionary, indent=0))

    def post(self, request, format=None):
        """ Updates FOLLOWERS for USER """

        print("ApiUserFollowers . POST . 1")

        if request.data.get('follow_dictionary'):
            print("ApiUserFollowers . POST . 2")
            follow_dictionary = request.data.get('follow_dictionary', None)
            i_should_follow = follow_dictionary['i_should_follow']
            publisher_id = follow_dictionary['publisher_id']
            new_subscriber_id = follow_dictionary['subscriber_id']
            print("ApiUserFollowers . POST . 2 . follow_dictionary = {0}".format(follow_dictionary))
            print("ApiUserFollowers . POST . 2 . i_should_follow = {0}".format(i_should_follow))

            dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
            table = dynamodb.Table('FOLLOWERS')

            if i_should_follow == '1':
                print("ApiUserFollowers . POST . 2 . i_should_follow = YES")
                addFollower(follow_dictionary)

            else:
                print("ApiUserFollowers . POST . 2 . i_should_follow = NO")
                removeFollower(follow_dictionary)

            responseDictionary = {"success":"1"}
            return Response(json.dumps(responseDictionary, indent=0))


        else:
            print("ApiUserFollowers . POST . 2 . follow_dictionary = NO")
            responseDictionary = {"success":"0"}
            return Response(json.dumps(responseDictionary, indent=0))

class ApiUserFollowing(APIView):
    """ User FOLLOWING updates """

    def get(self, request, format=None):
        """ GET User Subscriptions """

        print("ApiUserFollowing . GET . 1")
        #user_subscriptions
        if request.GET.getlist('user_subscriptions[]'):
            user_subscriptions = request.GET.getlist('user_subscriptions[]')
            print("ApiUserFollowing . GET . 2 . user_subscriptions = {0}".format(user_subscriptions))
        else:
            print("ApiUserFollowing . GET . 2 . user_subscriptions FAILURE")
            responseDictionary = {"success":"0", "error" : "user_subscriptions FAILURE"}
            return Response(json.dumps(responseDictionary, indent=0))

        array_of_edition_headers = []

        print("ApiUserFollowing . GET . 3 . for user_subscriptions = {0}".format(user_subscriptions))
        for this_publisher_id in user_subscriptions:

            try:this_subscription_dictionary = gather_subscription_headers(this_publisher_id)
            except ClientError as e:
                pass
            else:
                array_of_edition_headers.append(this_subscription_dictionary)

        responseDictionaryFinal = {"success":"1", "user_subscriptions" : array_of_edition_headers}
        print("ApiUserFollowing . GET . 4 . SUCCESS")
        return Response(json.dumps(responseDictionaryFinal, indent=0))

class ApiUserSubscribe(APIView):
    """ Adds/Removes FOLLOWERS """

class NameForm(forms.Form):

    print("NameForm . 1")
    email = forms.CharField(label='name_form_invite_email', max_length=100)
    print("NameForm . 2 . email = {0}".format(email))

    def return_email(self):
        return email

class ApiFormInviteRequest(APIView):
    if (settings.DEBUG):
        permission_classes = (AllowAny,)

    def get(self, request, format=None):
        """ SAVE INVITE REQUEST INFO """

        form = FormInviteRequest()
        return render(request, 'invite/index.html', {'form':form});

    def post(self, request, format=None):
        """ SAVE INVITE REQUEST INFO """

        print("ApiUserInviteRequest . POST . 1")

        form = "Nope."
        return render(request, 'invite/index.html', {'form':form});


    # def post(self, request, format=None):
    #     """ SAVE INVITE REQUEST INFO """
    #
    #     print("ApiUserInviteRequest . POST . 1")
    #
    #     if request.method == 'POST':
    #         #will handle the request later
    #         print("ApiUserInviteRequest . POST . 1.1")
    #
    #     else:
    #         #creating a new form
    #         form = FormInviteRequest()
    #
    #     #returning form
    #     return render(request, 'invite.html', {'form':form});



""" THESE FUNCTIONS HAVE NO CLASS. AHEM. """

def rejectIfCodeIsBogus(secret_timecode):

    if len(secret_timecode) < 20:
        return False

    print("secret_timecode = {0}".format(secret_timecode))

    actual_secret_a = secret_timecode[8]
    actual_secret_b = secret_timecode[18]

    if actual_secret_a.isdigit() and actual_secret_b.isdigit():
        answer = int(actual_secret_a) + int(actual_secret_b)
        #print("rejectIfCodeIsBogus . actual_secret_a({0}) + actual_secret_b({1}) = {2}".format(actual_secret_a, actual_secret_b, answer))
        if answer == 8:
            return False
        else:
            return True
    else:
        #print("rejectIfCodeIsBogus . actual_secret_a({0}) + actual_secret_b({1})".format(actual_secret_a, actual_secret_b))
        return True

def rejectIfAllDataIsNotReady(userDictionary):

    user_username = userDictionary.get('user_username', None)
    user_facebook_id = userDictionary.get('fb_user_id', None)
    user_phone_number = userDictionary.get('fb_phone_number', None)

    print("user_username = {0}".format(user_username))
    print("user_facebook_id = {0}".format(user_facebook_id))
    print("user_phone_number = {0}".format(user_phone_number))

    if user_username and user_facebook_id and user_phone_number:
        return False
    else:
        return True

def rejectIfUsernameIsImproperLength(username):
    if len(username) <= 1:
        return True
    elif len(username) > 25:
        return True
    else:
        return False

def rejectIfUsernameIsNotAvailable(username):

    print("API_USER . rejectIfUsernameIsNotAvailable . 1")

    dynamo_session = boto3.session.Session(aws_access_key_id=settings.AWS_DYNAMO_KEY, aws_secret_access_key=settings.AWS_DYNAMO_PUBLIC)
    dynamo_db = dynamo_session.resource('dynamodb', region_name='us-east-1')
    table = dynamo_db.Table('USERNAMES')
    USERNAME_ACTUAL = username.upper()
    USERNAME_LETTER = username[0].upper()

    try:response = table.query(KeyConditionExpression=Key('USERNAME_LETTER').eq(USERNAME_LETTER) & Key('USERNAME_ACTUAL').eq(USERNAME_ACTUAL))
    except ClientError as e:
        return True
    else:
        items = response['Items']
        if items:
            return True
        else:
            return False

def rejectIfUsernameIsWacky(username):
    ALLOWED = frozenset(string.ascii_letters + string.digits + '_' + '-' + '.')
    if all(c in ALLOWED for c in username):
        return False
    else:
        return True

def writeUsernameToDynamoDB(username):

    dynamo_session = boto3.session.Session(aws_access_key_id=settings.AWS_DYNAMO_KEY, aws_secret_access_key=settings.AWS_DYNAMO_PUBLIC)
    dynamo_db = dynamo_session.resource('dynamodb', region_name='us-east-1')
    table = dynamo_db.Table('USERNAMES')

    USERNAME_ACTUAL = username.upper()
    USERNAME_LETTER = username[0].upper()

    response = table.put_item(Item={'USERNAME_LETTER': USERNAME_LETTER, 'USERNAME_ACTUAL': USERNAME_ACTUAL})

    print("ApiCreateUser . writeUsernameToDynamoDB . response = {0}".format(response))

def addFollower(follow_dictionary):

    print("ApiUserFollowers > addFollower . 1")

    dynamo_session = boto3.session.Session(aws_access_key_id=settings.AWS_DYNAMO_KEY, aws_secret_access_key=settings.AWS_DYNAMO_PUBLIC)
    dynamo_db = dynamo_session.resource('dynamodb', region_name='us-east-1')
    table = dynamo_db.Table('FOLLOWERS')

    publisher_id = follow_dictionary['publisher_id']
    new_subscriber_id = follow_dictionary['subscriber_id']

    print("ApiUserFollowers > addFollower . 2")

    try:result = table.update_item(
            Key={'PUBLISHER_ID': publisher_id},
            UpdateExpression="SET SUBSCRIBERS = list_append(if_not_exists(SUBSCRIBERS, :empty_list), :i)",
            ExpressionAttributeValues={
                ':i': [new_subscriber_id],
                ":empty_list":[],
            },
            ReturnValues="UPDATED_NEW"
        )
    except ClientError as e:
        print("ApiUserFollowers > addFollower . POST . 3. FAILURE = ClientError: {0}".format(e.response['Error']['Message']))
        responseDictionary = {"success":"0"}
        return Response(json.dumps(responseDictionary, indent=0))
    else:
        print("ApiUserFollowers > addFollower . POST . 3 . SUCCESS")
        responseDictionary = {"success":"1"}
        return Response(json.dumps(responseDictionary, indent=0))

def removeFollower(follow_dictionary):

    print("ApiUserFollowers > removeFollower . 1")

    dynamo_session = boto3.session.Session(aws_access_key_id=settings.AWS_DYNAMO_KEY, aws_secret_access_key=settings.AWS_DYNAMO_PUBLIC)
    dynamo_db = dynamo_session.resource('dynamodb', region_name='us-east-1')
    table = dynamo_db.Table('FOLLOWERS')

    publisher_id = follow_dictionary['publisher_id']
    old_subscriber_id = follow_dictionary['subscriber_id']

    print("ApiUserFollowers > removeFollower . 2")

    try:response = table.get_item(Key={'PUBLISHER_ID': publisher_id})
    except ClientError as e:
        print("ApiUserFollowers > removeFollower . POST . 3 . FAILURE = ClientError: {0}".format(e.response['Error']['Message']))
        responseDictionary = {"success":"0"}
        return Response(json.dumps(responseDictionary, indent=0))
    else:
        print("ApiUserFollowers > removeFollower . POST . 3 . SUCCESS . = {0}".format(response['Item']))

        FOLLOWERS = response['Item']
        SUBSCRIBERS = FOLLOWERS["SUBSCRIBERS"]
        SUBSCRIBERS.remove(old_subscriber_id)

        try:result = table.update_item(
                Key={'PUBLISHER_ID': publisher_id},
                UpdateExpression="SET SUBSCRIBERS = :i",
                ExpressionAttributeValues={':i': SUBSCRIBERS,},
                ReturnValues="UPDATED_NEW")
        except ClientError as e:
            print("ApiUserFollowers > removeFollower . POST . 4. FAILURE = ClientError: {0}".format(e.response['Error']['Message']))
            responseDictionary = {"success":"0"}
            return Response(json.dumps(responseDictionary, indent=0))
        else:
            print("ApiUserFollowers > removeFollower . POST . 4 . SUCCESS")
            responseDictionary = {"success":"1"}
            return Response(json.dumps(responseDictionary, indent=0))

""" ________ ________ ________ ________ ________ ________ ________ ________ ________ ________ ________ ________ ________ ________ """

def gather_subscription_headers(publisher_id):

    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('EDITIONS')

    try:editionDictionary = table.get_item(Key={'PUBLISHER_ID': publisher_id})
    except ClientError as e:
        print("PUBLISHER_ID ERROR: {0}".format(e.response['Error']['Message']))
        pass
    else:
        return editionDictionary


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)
