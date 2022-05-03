from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from django.contrib.auth.models import User
from PIL import Image

# Create your models here.
class Food(models.Model):
    name = models.CharField(max_length=100)
    amount = models.CharField(max_length=100)
    expiration = models.CharField(max_length=100)
    address = models.CharField(max_length=1000, default='Carnegie Mellon')
    key = models.CharField(max_length=1200, default='asdf')
    phone = PhoneNumberField(unique = True, null = False, blank = False)


# Extending User Model Using a One-To-One Link
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    avatar = models.ImageField(default='default.jpg', upload_to='profile_images')
    bio = models.TextField()

    def __str__(self):
        return self.user.username

    # resizing images
    def save(self, *args, **kwargs):
        super().save()

        img = Image.open(self.avatar.path)

        if img.height > 100 or img.width > 100:
            new_img = (100, 100)
            img.thumbnail(new_img)
            img.save(self.avatar.path)
