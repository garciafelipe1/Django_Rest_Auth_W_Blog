from django.db import models
import uuid
from django.conf import settings
from ckeditor.fields import RichTextField
from djoser.signals import user_registered, user_activated


User= settings.AUTH_USER_MODEL

class UserProfile(models.Model):
    id = models.UUIDField( default=uuid.uuid4, unique=True, primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    profile_banner = models.ImageField(upload_to='profile_banners/', null=True, blank=True)

    biography =RichTextField()
    birthday= models.DateField(null=True, blank=True)
    
    website= models.URLField(blank=True,null=True)
    facebook= models.URLField(blank=True,null=True)
    twitter= models.URLField(blank=True,null=True)
    instagram= models.URLField(blank=True,null=True)
    github= models.URLField(blank=True,null=True)
    linkedin= models.URLField(blank=True,null=True)
    youtube= models.URLField(blank=True,null=True)
    tiktok= models.URLField(blank=True,null=True)
    snapchat= models.URLField(blank=True,null=True)


      
# def post_user_registered(user,*args,**kwargs):
#     print("user registered")
    
def post_user_activated(user, *args, **kwargs):
    profile=UserProfile.objects.create(user=user)
    
# user_registered.connect(post_user_registered)
user_activated.connect(post_user_activated)
        