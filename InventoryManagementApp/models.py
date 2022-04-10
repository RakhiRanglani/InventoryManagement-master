from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


# Create your models here.
class Food(models.Model):
    name = models.CharField(max_length=100)
    amount = models.CharField(max_length=100)
    expiration = models.CharField(max_length=100)
    address = models.CharField(max_length=1000, default='Carnegie Mellon')
    key = models.CharField(max_length=1200, default='asdf')
    phone = PhoneNumberField(unique = True, null = False, blank = False)
