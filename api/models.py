from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator, \
    MinValueValidator, MaxValueValidator

# Class disease
class Diag(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        unique_together = ('name',)


class Pipeline(models.Model):
    name = models.CharField(max_length=100)
    pipeline_id = models.CharField(max_length=40,null=True)
    class Meta:
        unique_together = ('pipeline_id',)

class Dicom(models.Model):
    name = models.CharField(max_length=100)
    data = models.FileField(upload_to='image/')
    is_verified = models.BooleanField(default=False)
    class Meta:
        unique_together = ('name',)
# Class project
class Project(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=300)
    users = models.ManyToManyField(
        User,
        related_name='projects',
        blank=True,
    )
    pipeline = models.ForeignKey(
        Pipeline,
        related_name='project',
        on_delete=models.PROTECT,
        default=None
    )
    dicoms = models.ManyToManyField(
        Dicom,
        related_name='projects',
        blank=True,
    )
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
        default=None
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
