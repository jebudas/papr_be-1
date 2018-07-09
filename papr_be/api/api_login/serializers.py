from . import models
from rest_framework import serializers

class AuthCodeSerializer(serializers.Serializer):
    # Serializes the authcode field

    authcode = serializers.CharField(max_length=400)
