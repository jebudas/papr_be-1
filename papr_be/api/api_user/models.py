# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.models import BaseUserManager
from jsonfield import JSONField


class UserAccountManager(BaseUserManager):

    # inherits from BaseUserManager,
    # helps django work with our custom user model (below)

    def create_user(self, email, user_username, password):

        # create a new user Profile object

        if not email:
            raise ValueError('Users Need An Email Address!')

        print("UserAccountManager . create_user . 1")
        email = self.normalize_email(email)
        print("UserAccountManager . create_user . 2")
        user = self.model(email = email, user_username = user_username)
        print("UserAccountManager . create_user . 3")

        # Encrypt the password!
        user.set_password(password)

        user.save(using=self._db)

        return user

    def create_superuser(self, email, user_username, password):

        user = self.create_user(email, user_username, password)

        user.is_staff = True
        user.is_superuser = True

        user.save(using=self._db)

        return user

class UserAccount(AbstractBaseUser, PermissionsMixin):

    # represents a user profile inside our system

    email = models.EmailField(max_length=100, unique=True)
    user_username = models.CharField(max_length=25, default="ILLEGAL", unique=True)
    user_fb_id = models.CharField(max_length=100, default="ILLEGAL", unique=True)
    user_fb_phone = models.CharField(max_length=25, default="ILLEGAL", unique=True)
    user_subscriptions = models.CharField(max_length=10000, default="")
    user_creation_date = models.DateTimeField(blank=False, verbose_name='CREATION_DATE'),
    user_image_url = models.CharField(max_length=125, default="")
    user_profile = JSONField(max_length=1000, default="")
    user_settings = JSONField(max_length=1000, default="")
    user_location = JSONField(max_length=1000, default="")
    is_active = models.BooleanField(default=True)
    is_private = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    objects = UserAccountManager()

    USERNAME_FIELD = 'user_username'
    REQUIRED_FIELDS = ['email']

    def get_user_username(self):
        return self.user_username

    def get_short_name(self):
        return self.user_username

    def __str__(self):
        return self.email



'''




breathe




'''
