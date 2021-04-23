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
    MODEL_CHOICES = (
    ('CLARA', 'CLARA'),
    ('NON CLARA', 'NON CLARA'),
    )

    name = models.CharField(max_length=50)
    pipeline_id = models.CharField(max_length=40,null=True,blank=True)
    operator =  models.CharField(max_length=50,null=True,blank=True)
    model_name = models.CharField(max_length=100,null=True,blank=True)
    model_type = models.CharField(max_length=10,choices=MODEL_CHOICES)
    netInputname = models.CharField(max_length=50,null=True,blank=True)
    netOutputname = models.CharField(max_length=50,null=True,blank=True)
    description = models.CharField(max_length=500,default='')
    clara_pipeline_name = models.CharField(max_length=50,null=True,blank=True,default='empty')
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
        unique_together = ('pipeline_id','model_name')

    
class Image(models.Model):
    name = models.CharField(max_length=50)
    data = models.FileField(upload_to='image3D/')
    patient_name = models.CharField(max_length=50)
    patient_id = models.CharField(max_length=12)
    patient_age = models.IntegerField(validators=[MinValueValidator(0), ])
    content_date = models.DateField()
    physician_name = models.CharField(max_length=50)
    status = models.IntegerField(default=0) # 0:uploaded 1:in process 2:Annotated 3:verified
    actual_class =ArrayField(models.CharField(max_length=50),blank=True,null=True)
    predclass = models.CharField(max_length=50,null=True,blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, )
    verify_by = models.CharField(max_length=100,blank=True)
    note = models.CharField(max_length=300,null=True,blank=True,default=" ")
    project = models.ForeignKey(
        Project,
        related_name='images',
        default=None,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    
    def __str__(self):
        return self.data.name

class Image3D(models.Model):
    name = models.CharField(max_length=50)
    data = ArrayField(models.FileField(upload_to='image8/'))
    patient_name = models.CharField(max_length=50)
    patient_id = models.CharField(max_length=12)
    patient_age = models.IntegerField(validators=[MinValueValidator(0), ])
    content_date = models.DateField()
    physician_name = models.CharField(max_length=50)
    status = models.IntegerField(default=0) # 0:uploaded 1:in process 2:Annotated 3:verified
    actual_class =ArrayField(models.CharField(max_length=50),blank=True,null=True)
    predclass = models.CharField(max_length=50,null=True,blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, )
    verify_by = models.CharField(max_length=100,blank=True)
    note = models.CharField(max_length=300,null=True,blank=True,default=" ")
    project = models.ForeignKey(
        Project,
        related_name='images3d',
        default=None,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )

    

class PredictResult(models.Model):
    gradcam = models.FileField(upload_to='imagegrad/',null=True,blank=True)
    predicted_class = models.JSONField(null=True,blank=True)
    predicted_mask = ArrayField(models.FileField(upload_to='mask/',null=True,blank=True),null=True,blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, )
    pipeline = models.ForeignKey(
        Pipeline,
        related_name='result',
        null=True,
        on_delete=models.CASCADE,
    )
    image = models.ForeignKey(
        Image,
        related_name='result',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    image3D = models.ForeignKey(
        Image3D,
        related_name='result',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    class Meta:
        unique_together = ('pipeline','image')
    
class Queue(models.Model):
    #JOB_ID Queue
    job= models.CharField(max_length=50,null=True,blank=True)
    project = models.ForeignKey(
        Project,
        related_name='queue',
        null=True,
        on_delete=models.SET_NULL,
    )
    pipeline = models.ForeignKey(
        Pipeline,
        related_name='queue',
        null=True,
        on_delete=models.SET_NULL,
    )
    image = models.ForeignKey(
        Image,
        related_name='queue',
        null=True,
        on_delete=models.SET_NULL,
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
