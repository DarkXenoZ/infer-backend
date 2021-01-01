from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator, \
    MinValueValidator, MaxValueValidator


    
class Dicom(models.Model):
    name = models.CharField(max_length=200)
    data = models.FileField()
    owner = models.ForeignKey(
        User,
        related_name='dicom',
        on_delete=models.PROTECT,
        )

class Log(models.Model):
    user = models.ForeignKey(
        User,
        related_name='logs',
        on_delete=models.SET_NULL,
        null=True,
    )
    desc = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True, blank=True, )

    def __str__(self):
        try:
            return '%s: %s' % (self.user.username, self.desc,)
        except:
            return '<Deleted>: %s' % (self.desc,)
