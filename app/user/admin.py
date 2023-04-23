from django.contrib import admin
from .models import User,ResetPassword,Friends,Badge

# Register your models here.
admin.site.register(User)
admin.site.register(ResetPassword)
admin.site.register(Friends)
admin.site.register(Badge)
