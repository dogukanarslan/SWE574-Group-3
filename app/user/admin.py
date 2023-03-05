from django.contrib import admin
from .models import User, ResetPassword,Friends

# Register your models here.
admin.site.register(User)
admin.site.register(ResetPassword)
admin.site.register(Friends)
