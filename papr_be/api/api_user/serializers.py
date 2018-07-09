from . import models
from rest_framework import serializers

class UserAccountSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.UserAccount
        fields = ('id', 'email', 'user_username')
        extra_kwargs = {'password': {'write_only':True} }

    def create(self, validated_data):
        # create and return new user

        user = models.UserAccount(
            email = validated_data['email'],
            username = validated_data['user_username']
        )

        user.set_password(validated_data['password'])
        user.save()

        return user



class CreateUserSerializer(serializers.Serializer):
    # Serializes the return message

    authcode = serializers.CharField(max_length=400)
