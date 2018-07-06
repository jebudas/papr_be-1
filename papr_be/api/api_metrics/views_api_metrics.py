# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.shortcuts import render

from django.conf.urls import url
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
# DRF
from rest_framework.views import APIView
from rest_framework.response import Response
# BOTO
import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
# OTHER
import json


class ApiMetricsAF(APIView):

    def post(self, request, format=None):
        """ PUBLISH Papr """

        print("ApiMetricsAF . POST . 1")
