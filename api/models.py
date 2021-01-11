from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator, \
    MinValueValidator, MaxValueValidator

# Class project
class Project(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=300)
    users = models.ManyToManyField(
        User,
        related_name='projects',
        blank=True,
    )

    def __str__(self):
        return self.name
    
    class Meta:
        unique_together = ('name',)

# Class disease
class Diag(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    
    class Meta:
        unique_together = ('name',)
    


class Pipeline(models.Model):
    name = models.CharField(max_length=100)
    pipeline_id = models.CharField(max_length=40,default="Empty")
    accuracy = models.FloatField(blank=True,default=0.0)
    project = models.ForeignKey(
        Project,
        related_name='pipelines',
        on_delete=models.PROTECT,
        default=None,
        null=True,
        blank=True,
    )
    def __str__(self):
        return self.name
    
    class Meta:
        unique_together = ('pipeline_id',)

class Dicom(models.Model):
    name = models.CharField(max_length=100)
    data = models.FileField(upload_to='dicom/')
    is_verified = models.BooleanField(null=True, default=False)
    project = models.ForeignKey(
        Project,
        related_name='dicoms',
        on_delete=models.PROTECT,
        default=None,
        null=True,
        blank=True,
    )
    def __str__(self):
        return self.name
    
    class Meta:
        unique_together = ('name',)
    

class Result(models.Model):
    project = models.ForeignKey(
        Project,
        related_name='result',
        on_delete=models.CASCADE,
        default=None
    )
    dicoms = models.ForeignKey(
        Dicom,
        related_name='result',
        on_delete=models.CASCADE,
        default=None
    )
    diag = models.ForeignKey(
        Diag,
        related_name='result',
        on_delete=models.CASCADE,
        default=None,
        null=True,
        blank=True,
    )
    def __str__(self):
        return f"Project: {project.name}, Dicom: {dicoms.name},Diag: {diag.name} " 
    

class Log(models.Model):
    user = models.ForeignKey(
        User,
        related_name='logs',
        on_delete=models.SET_NULL,
        null=True,
    )
    desc = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True, )

    def __str__(self):
        try:
            return '%s: %s' % (self.user.username, self.desc,)
        except:
            return '<Deleted>: %s' % (self.desc,)
