from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.


class User(User):
    description = models.CharField(
        max_length=300, blank=True, null=True, unique=False, default=""
    )
    avatar= models.FileField(upload_to='avatar', blank=True, null=True)
    phone_number = models.BigIntegerField(
        "phone number",
        blank=True,
        unique=True,
        null=True,
        validators=[MinValueValidator(1000000), MaxValueValidator(10000000000 - 1)],
    )





class ResetPassword(models.Model):
    code = models.CharField(
        max_length=300, blank=False, null=False, unique=False, default=""
    )
    email = models.CharField(
        max_length=300, blank=False, null=False, unique=False, default=""
    )

class FriendRequest(models.Model):
    receiver = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE, related_name="friend_request_receiver")
    sender = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE, related_name="friend_request_sender")

class Friends(models.Model):
    owner = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE, related_name="friend_list_owner")
    friend_list = models.ManyToManyField(User, blank=True, null=True, related_name="friend_list")


