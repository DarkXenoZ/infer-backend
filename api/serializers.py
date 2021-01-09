from rest_framework import serializers
from .models import *



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
        fields = ('name', 'data','is_verified')


class OnlyUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username','first_name')


class UserLogSerializer(serializers.ModelSerializer):
    logs = LogSerializer(many=True)

    class Meta:
        model = User
        fields = ('username', 'logs',)


class UserProjectSerializer(serializers.ModelSerializer):
    users = OnlyUserSerializer(many=True)

    class Meta:
        model = Project
        fields = ('name','description','pipeline','users')


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ('name','description','pipeline')

class DicomProjectSerializer(serializers.ModelSerializer):
    dicoms = DicomSerializer(many=True)

    class Meta:
        model = Project
        fields = ('name','description','pipeline','dicoms')

class UserSerializer(serializers.ModelSerializer):
    projects = ProjectSerializer(many=True)
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name','email','projects')


class PipelineSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Pipeline
        fields = ('name','pipeline_id')

class ResultSerializer(serializers.ModelSerializer):
    project = ProjectSerializer(many=False)
    dicoms = DicomSerializer(many=True)
    diag = DiagSerializer(many=False)

    class Meta:
        model = Result
        fields = ('project','dicoms','diag')