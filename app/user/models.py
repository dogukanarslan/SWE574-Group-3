from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.
class Badge(models.Model):
    LEVEL_CHOICES = (
        (1, "Bronze"),
        (2, "Silver"),
        (3, "Gold"),
    )
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=200)
    level = models.IntegerField(choices=LEVEL_CHOICES)

    def __str__(self):
        return self.name

    def level_text(self):
        return self.get_level_display()

    def level_number(self):
        return self.level

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
    badge = models.ForeignKey(
    Badge,
    blank=True,
    null=True,
    on_delete=models.CASCADE,
    related_name="user_badges",
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


