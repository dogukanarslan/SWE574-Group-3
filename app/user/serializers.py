from rest_framework.serializers import ModelSerializer, SerializerMethodField
from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from rest_framework import serializers
from rest_framework.fields import CharField
from rest_framework.response import Response
from django.contrib.auth.models import Group
from rest_framework.exceptions import ValidationError
from rest_framework_jwt.settings import api_settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from user.models import User, Friends, FriendRequest, Badge


JWT_PAYLOAD_HANDLER = api_settings.JWT_PAYLOAD_HANDLER
JWT_ENCODE_HANDLER = api_settings.JWT_ENCODE_HANDLER


class UserRegisterSerializer(ModelSerializer):
    password2 = serializers.CharField(required=True, write_only=True)

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "password",
            "password2",
            "description",
        ]
        extra_kwargs = {"password": {"write_only": True}, "email": {"required": True}}

    def validate(self, data):
        if data["password"] != data["password2"]:
            raise serializers.ValidationError("Passwords do no match!")
        return data

    def create(self, validated_data):
        email = validated_data.get("email")
        username = validated_data.get("email")
        first_name = validated_data.get("first_name", "")
        last_name = validated_data.get("last_name", "")
        password = validated_data.get("password")
        description = validated_data.get("description","")

        user_obj = User(
            email=email,
            username=username,
            first_name=first_name,
            last_name=last_name,
            description=description,
        )
        user_obj.set_password(password)
        user_obj.save()

        data = user_obj
        return data


class UserListSerializer(serializers.ModelSerializer):
    badge = serializers.SerializerMethodField('assign_badge')
    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "description",
            "badge"
        ]
        read_only_fields = ("id",)        
    
    def assign_badge(self,obj):
        try:
            friend_list = Friends.objects.filter(friend_list=obj)
        except Friends.DoesNotExist:
            friend_list = []        
        follower_count = len(friend_list)
        if follower_count >= 3:
            badge = Badge.objects.get(level=3) # Gold Badge
        elif follower_count >= 2:
            badge = Badge.objects.get(level=2) # Silver Badge
        elif follower_count >= 1:
            badge = Badge.objects.get(level=1) # Bronz Badge
        else:
            badge = None
            
        obj.badge = badge        
        obj.save()
        return obj.badge

class UserLoginListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "description",
        ]
        read_only_fields = ("id",)        

class UserLoginSerializer(ModelSerializer):
    token = CharField(allow_blank=True, read_only=True)
    email = CharField(write_only=True, required=True)
    user = UserLoginListSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "email",
            "password",
            "token",
            "user",
        ]
        extra_kwargs = {"password": {"write_only": True, "required": False}}

    def validate(self, data):
        password = data.get("password")
        email = data.get("email")
        user = User.objects.filter(email=email).distinct()
        if user.exists():
            user_obj = user.first()
        else:
            raise ValidationError("Incorrect credential")
        if user_obj:
            if not user_obj.check_password(password):
                raise ValidationError({"detail": "Incorrect credential"})
        payload = JWT_PAYLOAD_HANDLER(user_obj)
        token = JWT_ENCODE_HANDLER(payload)
        data["token"] = token
        data["user"] = UserLoginListSerializer(user_obj).data
        return data

class BadgeSerializer(serializers.ModelSerializer):
    user_badges=UserListSerializer()
    class Meta:
        model = Badge
        fields = [
            "id",
            "user_badges",
            "name",
            "description",
            "level",
        ]
        read_only_fields = ("id",)
        
class FriendRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = FriendRequest
        fields = [
            "id",
            "sender",
            "receiver",
        ]
        read_only_fields = ("id",)

class FriendRequestListSerializer(serializers.ModelSerializer):
    sender = UserListSerializer()
    receiver = UserListSerializer()
    class Meta:
        model = FriendRequest
        fields = [
            "id",
            "sender",
            "receiver",
        ]
        read_only_fields = ("id",)

class FriendsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Friends
        fields = [
            "id",
            "owner",
            "friend_list",
        ]
        read_only_fields = ("id",)

class FriendsListSerializer(serializers.ModelSerializer):
    owner = UserListSerializer()
    friend_list = UserListSerializer(many=True)
    class Meta:
        model = Friends
        fields = [
            "id",
            "owner",
            "friend_list",
        ]
        read_only_fields = ("id",)