from rest_framework import serializers
from .models import *


class LogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Log
        fields = ("desc", "timestamp",)

class MaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mask
        fields = ("mask",)

class GradcamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gradcam
        fields = ("predclass","gradcam",)

class PredictResultSerializer(serializers.ModelSerializer):
    predicted_class = serializers.JSONField()
    pipeline_name = serializers.CharField(
        source='pipeline.name'
    )
    predicted_mask = MaskSerializer(many=True)
    gradcams = GradcamSerializer(many=True)
    class Meta:
        model = PredictResult
        fields = ("pipeline_name","predicted_class","predicted_mask","timestamp","gradcams")

class ImageSerializer(serializers.ModelSerializer):
    result = PredictResultSerializer(many=True)
    class Meta:
        model = Image
        fields = (
            "id","name","data",
            "patient_name","patient_id",
            "patient_age","content_date",
            "physician_name","status",
            "actual_class","actual_mask","predclass",
            "verify_by","timestamp","result"
            )

class Image3DSerializer(serializers.ModelSerializer):
    result = PredictResultSerializer(many=True)
    class Meta:
        model = Image3D
        fields = (
            "id","name","data",
            "patient_name","patient_id",
            "patient_age","content_date",
            "physician_name","status",
            "actual_class","actual_mask","predclass",
            "verify_by","timestamp","result"
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



class UserSerializer(serializers.ModelSerializer):
    projects = ProjectSerializer(many=True)
    class Meta:
        model = User
        fields = ("username", "first_name", "last_name","email","projects", "is_staff")


class PipelineSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Pipeline
        fields = ("id","name","pipeline_id","operator","description","clara_pipeline_name","model_name","model_type")

class UserProjectSerializer(serializers.ModelSerializer):
    users = OnlyUserSerializer(many=True)
    pipeline = PipelineSerializer(many=True)
    class Meta:
        model = Project
        fields = ("id","name","description","pipeline","users","task","cover","predclasses")

class UploadImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ("project","name","data","encryption","patient_name","patient_id","patient_age","content_date","physician_name","status")
class UploadImage3DSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image3D
        fields = ("project","name","data","encryption","patient_name","patient_id","patient_age","content_date","physician_name","status")

class ImageProjectSerializer(serializers.ModelSerializer):
    images = ImageSerializer(many=True)
    class Meta:
        model = Project
        fields = ("id","name","images")
class Image3DProjectSerializer(serializers.ModelSerializer):
    images = Image3DSerializer(many=True,source='images3d')
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
            "id","name","data",
            "patient_name","patient_id",
            "patient_age","content_date",
            "physician_name","status","note",
            "actual_class","actual_mask","verify_by","predclass","timestamp",
            "project_name","project_task","project_predclasses"
            )

class ProjectImage3DSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(
        source='project.name'
    )
    project_task = serializers.CharField(
        source='project.task'
    )
    project_predclasses = serializers.ListField(child=serializers.CharField(),source='project.predclasses')
    class Meta:
        model = Image3D
        fields = (
            "id","name","data",
            "patient_name","patient_id",
            "patient_age","content_date",
            "physician_name","status","note",
            "actual_class","actual_mask","verify_by",
            "predclass","timestamp","project_name",
            "project_task","project_predclasses"
            )

class ExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Export
        fields = ("id","timestamp","project","zip_file")