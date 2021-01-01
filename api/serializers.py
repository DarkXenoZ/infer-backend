from rest_framework import serializers
from .models import *




class LogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Log
        fields = ('desc', 'timestamp',)

class DicomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dicom
        fields = ('name', 'data',)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name',)


class UserLogSerializer(serializers.ModelSerializer):
    logs = LogSerializer(many=True)

    class Meta:
        model = User
        fields = ('username', 'logs',)


class ExtendedUserSerializer(serializers.HyperlinkedModelSerializer):
    ban_list = UserSerializer(many=True)
    username = serializers.CharField(
        source='base_user.username'
    )
    first_name = serializers.CharField(
        source='base_user.first_name'
    )
    last_name = serializers.CharField(
        source='base_user.last_name'
    )
    email = serializers.CharField(
        source='base_user.email'
    )
    is_staff = serializers.BooleanField(
        source='base_user.is_staff'
    )
    dicom = DicomSerializer(
        source='base_user.dicom', many=True
    )

    class Meta:
        model = ExtendedUser
        fields = ('username', 'first_name', 'last_name',
                  'email', 'ban_list', 'is_verified',
                  'phone_number', 'credit', 'is_staff',
                  'dicom',)

