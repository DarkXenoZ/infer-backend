from rest_framework import serializers
from .models import *


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ('name','description','users')


class DiagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Diag
        fields = ('name')


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
        fields = ('username', 'first_name', 'last_name','email')


class UserLogSerializer(serializers.ModelSerializer):
    logs = LogSerializer(many=True)

    class Meta:
        model = User
        fields = ('username', 'logs',)
