from rest_framework import serializers
from .models import *



class DiagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Diag
        fields = ('id','name',)


class LogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Log
        fields = ('desc', 'timestamp',)


class DicomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dicom
        fields = ('id','name', 'data')


class OnlyUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username','first_name')


class UserLogSerializer(serializers.ModelSerializer):
    logs = LogSerializer(many=True)

    class Meta:
        model = User
        fields = ('username', 'logs',)


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ('id','name','description')

class ResultSerializer(serializers.ModelSerializer):
    project = ProjectSerializer(many=False)
    dicoms = DicomSerializer(many=False)
    diag = DiagSerializer(many=False)

    class Meta:
        model = Result
        fields = ('project','dicoms','diag')

class ResultNoProjectSerializer(serializers.ModelSerializer):
    dicoms = DicomSerializer(many=False)
    diag = DiagSerializer(many=False)

    class Meta:
        model = Result
        fields = ('dicoms','diag')

class DicomProjectSerializer(serializers.ModelSerializer):
    result = ResultNoProjectSerializer(many=True)

    class Meta:
        model = Project
        fields = ('id','name','description','pipeline','result')

class UserSerializer(serializers.ModelSerializer):
    projects = ProjectSerializer(many=True)
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name','email','projects')


class PipelineSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Pipeline
        fields = ('id','name','pipeline_id')

class UserProjectSerializer(serializers.ModelSerializer):
    users = OnlyUserSerializer(many=True)
    pipelines =PipelineSerializer(many=True)
    class Meta:
        model = Project
        fields = ('id','name','description','pipelines','users')