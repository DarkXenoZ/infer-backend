from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator, \
    MinValueValidator, MaxValueValidator

# Class disease
class Diag(models.Model):
    name = models.CharField(max_length=100)

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
    class Meta:
        unique_together = ('name',)



class Dicom(models.Model):
    name = models.CharField(max_length=100)
    data = models.CharField(max_length=300)
    owner = models.ForeignKey(
        Project,
        related_name='dicom',
        on_delete=models.PROTECT,
    )
    class Meta:
        unique_together = ('name',)

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
