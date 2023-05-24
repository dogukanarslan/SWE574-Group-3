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


class SpaceMemberRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpaceMemberRequest
        fields = "__all__"


class SpaceMemberRequestListSerializer(serializers.ModelSerializer):
    owner = UserListSerializer()
    space=SpaceCreateSerializer()
    class Meta:
        model = SpaceMemberRequest
        fields = "__all__"


class SpaceModeratorRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpaceModeratorRequest
        fields = "__all__"


class SpaceModeratorRequestListSerializer(serializers.ModelSerializer):
    owner = UserListSerializer()
    space = SpaceCreateSerializer()
    class Meta:
        model = SpaceModeratorRequest
        fields = "__all__"


class PostCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = "__all__"


class CommentListSerializer(serializers.ModelSerializer):
    user = UserListSerializer()
    created_time = serializers.SerializerMethodField('convert_date')

    class Meta:
        model = Comment
        fields = "__all__"
    
    def convert_date(self, obj):
        return obj.created_time


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
    space_member_request_space = SpaceMemberRequestListSerializer(many=True)
    member=UserListSerializer(many=True)
    moderator=UserListSerializer(many=True)
    class Meta:
        model = Space
        fields = "__all__"

class AnnotationSerializer(serializers.ModelSerializer):
    created = serializers.SerializerMethodField('convert_date')

    class Meta:
        model = Annotation
        fields = ('id', 'context', 'type', 'created', 'body', 'target')

    def convert_date(self, obj):
        return obj.created

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['@context'] = representation.pop('context')
        return representation


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = "__all__"

class ReportListSerializer(serializers.ModelSerializer):
    user = UserListSerializer()
    class Meta:
        model = Comment
        fields = "__all__"
