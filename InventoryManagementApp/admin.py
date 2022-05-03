from django.contrib import admin

# Register your models here.
from .models import Profile
from .models import Food

admin.site.register(Profile)
