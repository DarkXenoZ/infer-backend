from django.db import models
from django.contrib.postgres.fields import ArrayField,JSONField
from django.contrib.auth.models import User
from django.core.validators import RegexValidator, \
    MinValueValidator, MaxValueValidator

# Class project
class Project(models.Model):
    TASK_CHOICES = (
    ('2D Segmentation', '2D Segmentation'),
    ('2D Classification', '2D Classification'),
    ('3D Segmentation', '3D Segmentation'),
    ('3D Classification', '3D Classification'),
    )

    cover = models.ImageField(upload_to='cover/',null=True)
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=500)
    task = models.CharField(max_length=20,choices=TASK_CHOICES)
    predclasses = ArrayField(models.CharField(max_length=50))
    timestamp = models.DateTimeField(auto_now_add=True, )
    users = models.ManyToManyField(
        User,
        related_name='projects',
        blank=True,
    )

    def __str__(self):
        return self.name

    
    class Meta:
        unique_together = ('name',)

class Pipeline(models.Model):
    name = models.CharField(max_length=50)
    pipeline_id = models.CharField(max_length=40,default="Empty")
    operator =  models.CharField(max_length=50)
    accuracy = models.FloatField(blank=True,default=0.0)
    description = models.CharField(max_length=500,default='')
    model_name = models.CharField(max_length=50,default="no name")
    project = models.ForeignKey(
        Project,
        related_name='pipeline',
        default=None,
        blank=True,
        on_delete=models.CASCADE,
    )
    def __str__(self):
        return self.name
    
    class Meta:
        unique_together = ('pipeline_id',)

class Pair(models.Model):
    x = models.FloatField()
    y = models.FloatField()

    def __str__(self):
        return (self.x,self.y)
    
class Image(models.Model):
    name = models.CharField(max_length=50)
    data8 = models.FileField(upload_to='image8/')
    data16 = models.FileField(upload_to='image16/')
    patient_name = models.CharField(max_length=50)
    patient_id = models.CharField(max_length=12)
    patient_age = models.IntegerField(validators=[MinValueValidator(0), ])
    content_date = models.DateField()
    physician_name = models.CharField(max_length=50)
    status = models.IntegerField(default=0) # 0:uploaded 1:in process 2:Annotated 3:verified
    actual_class =ArrayField(models.CharField(max_length=50,blank=True,null=True))
    predclass = models.CharField(max_length=50,null=True,blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, )
    verify_by = models.CharField(max_length=100,blank=True)
    project = models.ForeignKey(
        Project,
        related_name='images',
        default=None,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    
    def __str__(self):
        return self.data8.name

    

class PredictResult(models.Model):
    predicted_class = models.JSONField()
    predicted_mask = models.BinaryField(blank=True,null=True)
    predicted_polygon = ArrayField(ArrayField(models.FloatField(),size=2),null=True)
    timestamp = models.DateTimeField(auto_now_add=True, )
    pipeline = models.ForeignKey(
        Pipeline,
        related_name='result',
        on_delete=models.CASCADE,
    )
    image = models.ForeignKey(
        Image,
        related_name='result',
        on_delete=models.CASCADE,
    )
    class Meta:
        unique_together = ('pipeline','image')
    
class Queue(models.Model):
    #JOB_ID Queue
    job= models.CharField(max_length=50)
    project = models.ForeignKey(
        Project,
        related_name='queue',
        on_delete=models.CASCADE,
    )
    pipeline = models.ForeignKey(
        Pipeline,
        related_name='queue',
        on_delete=models.CASCADE,
    )
    image = models.ForeignKey(
        Image,
        related_name='queue',
        on_delete=models.CASCADE,
    )

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
