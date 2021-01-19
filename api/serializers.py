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


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ('id', 'data','patient_name','patient_id','patient_age','content_date','physician_name')


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
        fields = ('id','name','description','task')

class ResultSerializer(serializers.ModelSerializer):
    project = ProjectSerializer(many=False)
    images = ImageSerializer(many=False)
    diag = DiagSerializer(many=False)

    class Meta:
        model = Result
        fields = ('project','images','diag','note')

class ResultNoProjectSerializer(serializers.ModelSerializer):
    images = ImageSerializer(many=False)
    diag = DiagSerializer(many=False)

    class Meta:
        model = Result
        fields = ('images','diag')

class ImageProjectSerializer(serializers.ModelSerializer):
    result = ResultNoProjectSerializer(many=True)

    class Meta:
        model = Project
        fields = ('id','name','description','result')

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
        fields = ('id','name','description','pipelines','users','task')

class ImageDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ('id', 'data','patient_name','patient_id','patient_age','physician_name','content_date')