from django.db import models
from django.contrib.postgres.fields import ArrayField,JSONField
from django.contrib.auth.models import User
from django.contrib.gis.db.models import PolygonField
from django.core.validators import RegexValidator, \
    MinValueValidator, MaxValueValidator

# Class project
class Project(models.Model):
    TASK_CHOICES = (
    ('Segmentation', 'Segmentation'),
    ('Classification', 'Classification'),
    )
    cover = models.ImageField(upload_to='cover/',null=True)
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=500)
    # เปลี่ยน task เป็นchoice
    task = models.CharField(max_length=1,choices=TASK_CHOICES)
    predclasses = ArrayField(models.CharField(max_length=50))
    timestamp = models.DateTimeField(auto_now_add=True, )
    users = models.ManyToManyField(
        User,
        related_name='projects',
        blank=True,
    )

    def __str__(self):
        return self.name

    def check_task(self,task):
        valid_task = ['Classification','Segmentation']
        if task in valid_task:
            return True
        return False
    
    class Meta:
        unique_together = ('name',)

class Pipeline(models.Model):
    name = models.CharField(max_length=50)
    pipeline_id = models.CharField(max_length=40,default="Empty")
    accuracy = models.FloatField(blank=True,default=0.0)
    description = models.CharField(max_length=500)
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


class PredictResult(models.Model):
    predicted_class = JSONField()
    predicted_mask = models.BinaryField(blank=True,null=True)
    predicted_polygon = PolygonField(blank=True,null=True)
    timestamp = models.DateTimeField(auto_now_add=True, )
    pipeline = models.ForeignKey(
        Pipeline,
        related_name='result',
        on_delete=models.CASCADE,
    )
    image = models.ForeignKey(
        Pipeline,
        related_name='result',
        on_delete=models.CASCADE,
    )
    

class Image(models.Model):
    data = models.ImageField(upload_to='image/')
    patient_name = models.CharField(max_length=50)
    patient_id = models.CharField(max_length=12)
    patient_age = models.IntegerField(validators=[MinValueValidator(0), ])
    content_date = models.DateField()
    physician_name = models.CharField(max_length=50)
    status = models.IntegerField(default=0)
    actual_class = models.CharField(max_length=50,default='')
    timestamp = models.DateTimeField(auto_now_add=True, )
    project = models.ForeignKey(
        Project,
        related_name='images',
        default=None,
        blank=True,
        on_delete=models.CASCADE,
    )
    
    def __str__(self):
        return self.data.name
    

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
