from rest_framework import serializers
from .models import *





class LogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Log
        fields = ("desc", "timestamp",)


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = (
            "id","name","data8","data16",
            "patient_name","patient_id",
            "patient_age","content_date",
            "physician_name","status",
            "actual_class","predclass","verify_by","timestamp"
            )


class OnlyUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("username","first_name")


class UserLogSerializer(serializers.ModelSerializer):
    logs = LogSerializer(many=True)

    class Meta:
        model = User
        fields = ("username", "logs",)


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ("id","name","description","task","cover","predclasses")

class createProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ("id","name","description","task","cover","predclasses")

class PredictResultSerializer(serializers.ModelSerializer):
    predicted_class = serializers.JSONField()
    pipeline_name = serializers.CharField(
        source='pipeline.name'
    )
    class Meta:
        model = PredictResult
        fields = ("gradcam","pipeline_name","predicted_class","timestamp")

class UserSerializer(serializers.ModelSerializer):
    projects = ProjectSerializer(many=True)
    class Meta:
        model = User
        fields = ("username", "first_name", "last_name","email","projects")


class PipelineSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Pipeline
        fields = ("id","name","pipeline_id","operator","description","clara_pipeline_name")

class UserProjectSerializer(serializers.ModelSerializer):
    users = OnlyUserSerializer(many=True)
    pipeline = PipelineSerializer(many=True)
    class Meta:
        model = Project
        fields = ("id","name","description","pipeline","users","task","cover","predclasses")

class UploadImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ("project","name","data8","data16","patient_name","patient_id","patient_age","content_date","physician_name","status")


class ImageProjectSerializer(serializers.ModelSerializer):
    images = ImageSerializer(many=True)
    class Meta:
        model = Project
        fields = ("id","name","images")


class ProjectImageSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(
        source='project.name'
    )
    project_task = serializers.CharField(
        source='project.task'
    )
    project_predclasses = serializers.ListField(child=serializers.CharField(),source='project.predclasses')
    class Meta:
        model = Image
        fields = (
            "id","name","data8","data16",
            "patient_name","patient_id",
            "patient_age","content_date",
            "physician_name","status","note",
            "actual_class","verify_by","predclass","timestamp",
            "project_name","project_task","project_predclasses"
            )