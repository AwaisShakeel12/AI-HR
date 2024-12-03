from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.

class User(AbstractUser):
    name = models.CharField(max_length=100)
    email = models.CharField(max_length=100)
    app_password = models.CharField(max_length=300)


    REQUIRED_FIELDS = []


class JobDescription(models.Model):
    description = models.TextField()
    
    
class InterviewDate(models.Model):
    date = models.CharField(max_length=100)    
    time = models.CharField(max_length=100)    
    
class Interview(models.Model):
    email = models.CharField(max_length=100)
    time = models.CharField(max_length=100)
    date = models.CharField(max_length=100)
    
        