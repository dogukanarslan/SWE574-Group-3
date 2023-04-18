from .models import *
from rest_framework import serializers
from user.models import User
from user.serializers import *
import json
from rest_framework.exceptions import ValidationError




class SpaceCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Space
        fields = "__all__"


class LabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Label
        fields = "__all__"

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = "__all__"




class PostCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = "__all__"

class CommentListSerializer(serializers.ModelSerializer):
    user = UserListSerializer()
    class Meta:
        model = Comment
        fields = "__all__"

class PostListSerializer(serializers.ModelSerializer):
    owner = UserListSerializer()
    liked_by = UserListSerializer(many=True)
    label = LabelSerializer(many=True)
    post_review = CommentSerializer(many=True)
    created_time = serializers.SerializerMethodField('convert_date')

    class Meta:
        model = Post
        fields = "__all__"
    
    def convert_date(self, obj):
        return obj.created_time


class SpaceListSerializer(serializers.ModelSerializer):
    owner = UserListSerializer()
    space_posts = PostListSerializer(many=True)

    class Meta:
        model = Space
        fields = "__all__"


class TextAnnotationSerializer(serializers.ModelSerializer):
    class Meta:
        model = textAnnotation
        fields = ('id', 'source', 'type', 'body_description', 'created_by', 'created_time', 'selector_type', 'start', 'end')
