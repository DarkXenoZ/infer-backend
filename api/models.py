from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator, \
    MinValueValidator, MaxValueValidator

# Class project
class Project(models.Model):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=500)
    task = models.CharField(max_length=50)
    users = models.ManyToManyField(
        User,
        related_name='projects',
        blank=True,
    )

    def __str__(self):
        return self.name

    def check_task(self,task):
        valid_task = ['classification','segmentation']
        if task in valid_task:
            return True
        return False
    
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
    name = models.CharField(max_length=50)
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

class Image(models.Model):
    data = models.FileField(upload_to='image/')
    patient_name = models.CharField(max_length=50)
    patient_id = models.CharField(max_length=12)
    patient_age = models.IntegerField(validators=[MinValueValidator(0), ])
    content_date = models.DateField()
    physician_name = models.CharField(max_length=50)
    project = models.ForeignKey(
        Project,
        related_name='images',
        on_delete=models.PROTECT,
        default=None,
        null=True,
        blank=True,
    )
    def __str__(self):
        return self.data.name
    

    

class Result(models.Model):
    project = models.ForeignKey(
        Project,
        related_name='result',
        on_delete=models.CASCADE,
        default=None
    )
    images = models.ForeignKey(
        Image,
        related_name='result',
        on_delete=models.CASCADE,
        default=None,
    )
    diag = models.ForeignKey(
        Diag,
        related_name='result',
        on_delete=models.CASCADE,
        default=None,
    )
    is_verified = models.IntegerField(default=0) # 0:in process , 1: AI-Annotated , 2: Verified
    note = models.CharField(blank=True,max_length=300)
    def __str__(self):
        return f"Project: {project.name}, Image: {images.name},Diag: {diag.name} " 
    

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
