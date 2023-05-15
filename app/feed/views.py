from django.shortcuts import render
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from rest_framework.decorators import action
from rest_framework.decorators import api_view
from rest_framework import mixins
from rest_framework.generics import UpdateAPIView, DestroyAPIView


from .serializers import *
from .models import *
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from user.permissions import IsSpaceOwnerPermission, IsModeratorPermission
from user.models import User
from app.settings import DOMAIN_URL
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import textAnnotation, Post
from django_filters.rest_framework import DjangoFilterBackend
import uuid
import re
import random

import requests
from django.http import JsonResponse

# Create your views here.

class WikidataViewSet(viewsets.ViewSet):
    def list(self, request):
        label = request.GET.get("label")
        if label:
            url = f"https://www.wikidata.org/w/api.php?action=wbsearchentities&format=json&language=en&type=item&search={label}"
            response = requests.get(url)
            if response.ok:
                data = response.json()
                suggestions = []                
                for result in data["search"]:
                    suggestions.append(result)
                    print(result)
                return JsonResponse(suggestions, safe=False)
        return JsonResponse([], safe=False)

class SpaceViewSet(viewsets.ModelViewSet):
    serializer_class = SpaceCreateSerializer
    queryset = Space.objects.all()

    def create(self, request, *args, **kwargs):
        request.data._mutable = True
        user = User.objects.filter(id=request.user.id).first()
        request.data["owner"] = user
        private_check_box = request.data.get("private_check_box")
        if private_check_box:
            request.data["is_private"]="True"
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        spaces = Space.objects.all().order_by("-id")
        user = User.objects.get(id=request.user.id)
        user_data = UserListSerializer(user).data
        # return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        return render(
            request,
            "spaces.html",
            {
                "spaces": spaces,
                "user_data":user_data,
                "owner": user.first_name + " " + user.last_name,
                "DOMAIN_URL": DOMAIN_URL,
            },
        )

    @action(detail=False, methods=["get"], name="Own Spaces")
    def own_spaces(self, request, pk=None):
        user = User.objects.filter(id=request.user.id).first()
        spaces = Space.objects.filter(owner=user.id).order_by("-id")
        # return Response({"detail":"Liked succesfully"},status=200)
        return render(
            request,
            "yourSpaces.html",
            {
                "spaces": spaces,
                "owner": user.first_name + " " + user.last_name,
                "DOMAIN_URL": DOMAIN_URL,
            },
        )
    @action(detail=True, methods=["get"], name="Own Spaces")
    def person_spaces(self, request, pk=None):
        user = request.user
        person = User.objects.get(id=pk)
        person_data = UserListSerializer(person).data
        spaces = Space.objects.filter(owner=person.id).order_by("-id")
        # return Response({"detail":"Liked succesfully"},status=200)
        following_friends=Friends.objects.get(owner=user.id)
        followings=UserListSerializer(following_friends.friend_list.all(),many=True).data
        return render(
            request,
            "personSpaces.html",
            {
                "spaces": spaces,
                "person":person,
                "person_data":person_data,
                "followings":followings,
                "owner": user.first_name + " " + user.last_name,
                "DOMAIN_URL": DOMAIN_URL,
            },
        )
    
    @action(detail=True, methods=["get"], name="Add Moderator")
    def space_settings_form(self, request, pk=None):
        space = self.get_object()
        space_data = SpaceListSerializer(space).data
        pending_moderator_requests =SpaceModeratorRequestListSerializer(SpaceModeratorRequest.objects.filter(space=space,status="Pending"),many=True).data
        user=request.user
        return render(
                request,
                "spaceSettings.html",
                {
                    "space": space_data,
                    "pending_moderator_requests":pending_moderator_requests,
                    "owner": user.first_name + " " + user.last_name,
                    "DOMAIN_URL": DOMAIN_URL,
                },
            )
    
    @action(detail=True, methods=["post"], name="Add Moderator")
    def search_moderator(self, request, pk=None):
        space = self.get_object()
        space_data = SpaceListSerializer(space).data
        user=request.user
        search_keyword = request.data["search_keyword"]
        print(search_keyword)
        user_data=UserListSerializer(User.objects.filter(
                Q(first_name__icontains=search_keyword)
                | Q(last_name__icontains=search_keyword)).distinct(),many=True).data
        print(user_data)
        return render(
                request,
                "spaceSettings.html",
                {
                    "space": space_data,
                    "user_data":user_data,
                    "owner": user.first_name + " " + user.last_name,
                    "DOMAIN_URL": DOMAIN_URL,
                },
            )      

    @action(detail=True, methods=["get"], name="Add Moderator")
    def send_moderator_request(self, request, pk=None):
        space = self.get_object()
        space_data = SpaceListSerializer(space).data
        user=request.user
        user_id = request.GET.get("value")
        user_obj = User.objects.get(id=user_id)
        space_moderator_request = SpaceModeratorRequest.objects.create(owner=user_obj, space=space)
        pending_moderator_requests =SpaceModeratorRequestListSerializer(SpaceModeratorRequest.objects.filter(space=space,status="Pending"),many=True).data

        return render(
                request,
                "spaceSettings.html",
                {
                    "space": space_data,
                    "pending_moderator_requests":pending_moderator_requests,
                    "owner": user.first_name + " " + user.last_name,
                    "DOMAIN_URL": DOMAIN_URL,
                },
            )
    @action(detail=True, methods=["get"], name="Add Moderator")
    def delete_moderator_request(self, request, pk=None):
        space = self.get_object()
        space_data = SpaceListSerializer(space).data
        user=request.user
        user_id = request.GET.get("value")
        print(user_id)
        print(space.id)
        user_obj = User.objects.get(id=user_id)
        space_moderator_request = SpaceModeratorRequest.objects.get(owner=user_obj.id, space=space.id)
        space_moderator_request.delete()
        pending_moderator_requests =SpaceModeratorRequestListSerializer(SpaceModeratorRequest.objects.filter(space=space,status="Pending"),many=True).data

        return render(
                request,
                "spaceSettings.html",
                {
                    "space": space_data,
                    "pending_moderator_requests":pending_moderator_requests,
                    "owner": user.first_name + " " + user.last_name,
                    "DOMAIN_URL": DOMAIN_URL,
                },
            )
    @action(detail=True, methods=["get"], name="Delete Post")
    def delete_post(self, request, pk=None):
        return Response("Deleted successfully from the space.", status=200)
    
    @action(detail=True, methods=["get"], name="Approve User")
    def send_member_request_to_space(self, request, pk=None):
        user = request.user
        user_obj = User.objects.get(id=user.id)
        space = self.get_object()
        if space.is_private:
            space_join_request= SpaceMemberRequest.objects.create(owner=user_obj, space=space)
        else:
            space.member.add(user_obj)
            space.save()
        spaces = Space.objects.all().order_by("-id")
        space_data = SpaceListSerializer(spaces,many=True).data
        user_data = UserListSerializer(user_obj).data
        return render(
                request,
                "spaces.html",
                {
                    "spaces": space_data,
                    "user_data":user_data,
                    "owner": user.first_name + " " + user.last_name,
                    "DOMAIN_URL": DOMAIN_URL,
                },
            )
    @action(detail=True, methods=["get"], name="Approve User")
    def left_space(self, request, pk=None):
        user = request.user
        user_obj = User.objects.get(id=user.id)
        space = self.get_object()
        space.member.remove(user_obj)
        space.save()
        spaces = Space.objects.all().order_by("-id")
        space_data = SpaceListSerializer(spaces,many=True).data
        user_data = UserListSerializer(user_obj).data
        return render(
                request,
                "spaces.html",
                {
                    "spaces": space_data,
                    "user_data":user_data,
                    "owner": user.first_name + " " + user.last_name,
                    "DOMAIN_URL": DOMAIN_URL,
                },
            )
    @action(detail=True, methods=["get"], name="Accept User")
    def accept_space_join_request(self, request, pk=None):
        space_join_request = SpaceMemberRequest.objects.get(id=self.kwargs['pk'])
        space_join_request.status = "Accepted"
        space_join_request.save()
        space = Space.objects.get(id=space_join_request.space.id)
        request_user = User.objects.get(id=space_join_request.owner.id)
        print(request_user)
        space.member.add(request_user)
        space.save()
        print(space.member.all())
        space_data = SpaceListSerializer(space).data
        user = User.objects.get(id=request.user.id)
        user_data = UserListSerializer(user).data
        space_join_requests=SpaceMemberRequest.objects.filter(space=space.id,status="Pending")
        space_join_request_data = SpaceMemberRequestListSerializer(space_join_requests,many=True).data
        space_members_data = UserListSerializer(space.member.all(),many=True).data
        return render(
                request,
                "spaceMemberRequest.html",
                {
                    "space": space_data,
                    "user_data":user_data,
                    "space_join_request_data":space_join_request_data,
                    "space_members_data":space_members_data,
                    "owner": user.first_name + " " + user.last_name,
                    "DOMAIN_URL": DOMAIN_URL,
                },
            )  
    @action(detail=True, methods=["get"], name="Reject User")
    def reject_space_join_request(self, request, pk=None):
        space_join_request = SpaceMemberRequest.objects.get(id=self.kwargs['pk'])
        space_join_request.status = "Rejected"
        space_join_request.save()
        space = Space.objects.get(id=space_join_request.space.id)
        space_data = SpaceListSerializer(space).data
        user = User.objects.get(id=request.user.id)
        user_data = UserListSerializer(user).data
        space_join_requests=SpaceMemberRequest.objects.filter(space=space.id,status="Pending")
        space_join_request_data = SpaceMemberRequestListSerializer(space_join_requests,many=True).data
        space_members_data = UserListSerializer(space.member,many=True).data
        return render(
                request,
                "spaceMemberRequest.html",
                {
                    "space": space_data,
                    "user_data":user_data,
                    "space_join_request_data":space_join_request_data,
                    "space_members_data":space_members_data,
                    "owner": user.first_name + " " + user.last_name,
                    "DOMAIN_URL": DOMAIN_URL,
                },
            )  
    @action(detail=True, methods=["get"], name="Reject User")
    def list_space_join_requests(self, request, pk=None):
        space = self.get_object()
        user = User.objects.get(id=request.user.id)
        user_data = UserListSerializer(user).data
        data = SpaceListSerializer(space).data
        space_join_requests=SpaceMemberRequest.objects.filter(space=space.id,status="Pending")
        space_join_request_data = SpaceMemberRequestListSerializer(space_join_requests,many=True).data
        space_members_data = UserListSerializer(space.member,many=True).data
        if user in space.moderator.all() or user.id == space.owner.id:
            print("testtt")
            return render(
                request,
                "spaceMemberRequest.html",
                {
                    "space": data,
                    "user_data":user_data,
                    "space_join_request_data":space_join_request_data,
                    "space_members_data":space_members_data,
                    "owner": user.first_name + " " + user.last_name,
                    "DOMAIN_URL": DOMAIN_URL,
                },
            )
        else:
            return render(
                request,
                "spaceMembers.html",
                {
                    "space": data,
                    "user_data":user_data,
                    "space_members_data":space_members_data,
                    "owner": user.first_name + " " + user.last_name,
                    "DOMAIN_URL": DOMAIN_URL,
                },
            )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response("Deleted successfully", status=200)

    def list(self, request, *args, **kwargs):
        spaces = Space.objects.all().order_by("-id")
        spaces_data = SpaceListSerializer(spaces,many=True).data

        if request.user.is_anonymous == False:
            user = User.objects.get(id=request.user.id)
            user_data = UserListSerializer(user).data
            return render(
                request,
                "spaces.html",
                {
                    "spaces": spaces_data,
                    "user_data":user_data,
                    "owner": user.first_name + " " + user.last_name,
                    "DOMAIN_URL": DOMAIN_URL,
                },
            )
        else:
            return render(
                request, "spaces.html", {"spaces": spaces, "DOMAIN_URL": DOMAIN_URL}
            )

    @action(detail=False, methods=["get"], name="Reject User")
    def list_moderator_requests(self, request, *args, **kwargs):
        user_obj=User.objects.get(id=request.user.id)
        user_data=UserListSerializer(user_obj).data
        moderator_requests = SpaceModeratorRequest.objects.filter(owner=user_obj,status="Pending")
        moderator_requests_data = SpaceModeratorRequestListSerializer(moderator_requests,many=True).data
        return render(
                request,
                "moderatorUserRequests.html",
                {
                    "moderator_requests_data": moderator_requests_data,
                    "user_data":user_data,
                    "owner": user_obj.first_name + " " + user_obj.last_name,
                    "DOMAIN_URL": DOMAIN_URL,
                },
            )
    @action(detail=True, methods=["get"], name="Accept User")
    def accept_space_moderator_request(self, request, pk=None):
        space_join_request = SpaceModeratorRequest.objects.get(id=self.kwargs['pk'])
        space_join_request.status = "Accepted"
        space_join_request.save()
        space = Space.objects.get(id=space_join_request.space.id)
        user = User.objects.get(id=space_join_request.owner.id)
        user_data=UserListSerializer(user).data
        space.moderator.add(user)
        space.member.add(user)
        space.save()
        moderator_requests = SpaceModeratorRequest.objects.filter(owner=user,status="Pending")
        moderator_requests_data = SpaceModeratorRequestListSerializer(moderator_requests,many=True).data
        return render(
                request,
                "moderatorUserRequests.html",
                {
                    "moderator_requests_data": moderator_requests_data,
                    "user_data":user_data,
                    "owner": user.first_name + " " + user.last_name,
                    "DOMAIN_URL": DOMAIN_URL,
                },
            )    
    @action(detail=True, methods=["get"], name="Reject User")
    def reject_space_moderator_request(self, request, pk=None):
        space_join_request = SpaceModeratorRequest.objects.get(id=self.kwargs['pk'])
        space_join_request.status = "Rejected"
        space_join_request.save()
        user = User.objects.get(id=space_join_request.owner.id)
        space = Space.objects.get(id=space_join_request.space.id)
        user_data=UserListSerializer(User.objects.get(id=request.user.id)).data
        moderator_requests = SpaceModeratorRequest.objects.filter(owner=user,status="Pending")
        moderator_requests_data = SpaceModeratorRequestListSerializer(moderator_requests,many=True).data
        return render(
                request,
                "moderatorUserRequests.html",
                {
                    "moderator_requests_data": moderator_requests_data,
                    "user_data":user_data,
                    "owner": user.first_name + " " + user.last_name,
                    "DOMAIN_URL": DOMAIN_URL,
                },
            )  
    @action(detail=True, methods=["get"], name="Add Moderator")
    def remove_moderator(self, request, pk=None):
        space = self.get_object()
        user=request.user
        user_id = request.GET.get("value")
        user_obj = User.objects.get(id=user_id)
        space.moderator.remove(user_obj)
        space.save()
        space_data = SpaceListSerializer(space).data

        return render(
                request,
                "spaceSettings.html",
                {
                    "space": space_data,
                    "owner": user.first_name + " " + user.last_name,
                    "DOMAIN_URL": DOMAIN_URL,
                },
            )

    @action(detail=True, methods=["get"], name="Add Moderator")
    def delete_post_from_space(self, request, pk=None):
        space = self.get_object()
        post_id = request.GET.get("value")
        post_obj = Post.objects.get(id=post_id)
        post_obj.space=None
        post_obj.save()
        user = User.objects.get(id=request.user.id)
        user_data = UserListSerializer(user).data
        user_liked_posts = PostListSerializer(Post.objects.filter(liked_by__id=user.id),many=True).data
        user_bookmarked_posts = PostListSerializer(Post.objects.filter(bookmarked_by__id=user.id),many=True).data 
        labels = Label.objects.all()
        space_data = SpaceListSerializer(space).data
        return render(
            request,
            "spacePosts.html",
            {
                "space": space_data,
                "user_liked_posts":user_liked_posts,
                "user_data":user_data,
                "user_bookmarked_posts":user_bookmarked_posts,
                "labels": labels,
                "owner": user.first_name + " " + user.last_name,
                "DOMAIN_URL": DOMAIN_URL,
            },
        )
    def retrieve(self, request, *args, **kwargs):
        space = self.get_object()
        data = SpaceListSerializer(space).data
        labels = Label.objects.all()
        if request.user.is_anonymous == False:
            user = User.objects.get(id=request.user.id)
            user_data = UserListSerializer(user).data
            user_liked_posts = PostListSerializer(Post.objects.filter(liked_by__id=user.id),many=True).data
            user_bookmarked_posts = PostListSerializer(Post.objects.filter(bookmarked_by__id=user.id),many=True).data            
            return render(
                request,
                "spacePosts.html",
                {
                    "space": data,
                    "user_liked_posts":user_liked_posts,
                    "user_data":user_data,
                    "user_bookmarked_posts":user_bookmarked_posts,
                    "labels": labels,
                    "owner": user.first_name + " " + user.last_name,
                    "DOMAIN_URL": DOMAIN_URL,
                },
            )
        else:
            return render(
                request, "mainPosts.html", {"space": data, "DOMAIN_URL": DOMAIN_URL, "UNPROTECTED_ROUTE": True}
            )

    def get_serializer_class(self, *args, **kwargs):
        if self.action == "retrieve" or self.action == "list":
            return SpaceListSerializer
        else:
            return SpaceCreateSerializer

    def get_permissions(self):
        if self.action == "retrieve" or self.action == "list":
            permission_classes = [AllowAny]
        elif self.action == "add_moderator":
            permission_classes = [IsSpaceOwnerPermission]
        elif self.action in ['delete_post','approve_user','reject_user']:
            permission_classes = [IsSpaceOwnerPermission,IsModeratorPermission]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]


class LabelViewSet(viewsets.ModelViewSet):
    serializer_class = LabelSerializer
    queryset = Label.objects.all()

    def create(self, request, *args, **kwargs):
        name = request.data.get('name')
        if not name:
            return Response({'name': 'This field is required.'}, status=400)

        # check if name is a valid Wikidata query ID
        if re.match(r'^Q\d+$', name):
            label = Label.objects.create(name=name)
            serializer = LabelSerializer(label)
            return Response(serializer.data, status=201)
        else:
            # generate random QID
            qid = '{}'.format(random.randint(1, 1000000000))
            label = Label.objects.create(name=name, qid=qid)
            serializer = LabelSerializer(label)
            return Response(serializer.data, status=201)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response("Deleted successfully", status=200)

    def get_permissions(self):
        if self.action == "retrive" or self.action == "list":
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]


class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostCreateSerializer
    queryset = Post.objects.all()
    paginate_by = 2

    def create(self, request, *args, **kwargs):
        request.data._mutable = True
        print(request.data)
        post_link = request.data.get("post_link")
        existing_post = Post.objects.filter(post_link=post_link).first()
        is_confirmed = request.data.get("is_confirmed")
        user = User.objects.filter(id=request.user.id).first()
        request.data["owner"] = user.id
        user_liked_posts = PostListSerializer(Post.objects.filter(liked_by__id=user.id),many=True).data
        user_bookmarked_posts = PostListSerializer(Post.objects.filter(bookmarked_by__id=user.id),many=True).data     
        if existing_post and not is_confirmed:
            data = Post.objects.all().order_by("-id")
            posts = PostListSerializer(data, many=True).data
            return render(
                request,
                "posts.html",
                {
                    "posts": posts,
                    "user_liked_posts":user_liked_posts,
                    "user_bookmarked_posts":user_bookmarked_posts,
                    "owner": user.first_name + " " + user.last_name,
                    "DOMAIN_URL": DOMAIN_URL,
                    "title": request.data.get("title"),
                    "description": request.data.get("description"),
                    "platform": request.data.get("platform"),
                    "post_link": request.data.get("post_link"),
                    "selected_semantic_tags": request.data.get("selected_semantic_tags"),
                    "selected_non_semantic_tags": request.data.get("selected_non_semantic_tags"),
                    "confirmation_modal": True
                },
            )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        data = Post.objects.all().order_by("-id")
        posts = PostListSerializer(data, many=True).data
        headers = self.get_success_headers(serializer.data)
        created_post_obj = Post.objects.get(id=serializer.data["id"])
        if request.data.get("selected_semantic_tags") is not None and request.data.get("selected_semantic_tags")!='':
            labels=request.data.get("selected_semantic_tags").split("item:")
            print(labels)
            for label in labels:
                if label is not None and label!="":
                    information = label.split("|")
                    name=information[0]
                    description=information[1]
                    qid=information[2]
                    print(name,description)
                    try:
                        label = Label.objects.get(name=name,description=description,label_type="Semantic",qid=qid)
                        print("try",label)
                    except:
                        label=Label.objects.create(name=name,description=description,label_type="Semantic",qid=qid)
                        print("except",label)
                    created_post_obj.label.add(label.id)
                    print("created_post_obj",created_post_obj.label.all())

        if request.data.get("selected_non_semantic_tags") is not None and request.data.get("selected_non_semantic_tags")!='':
            labels=request.data.get("selected_non_semantic_tags").split(",")
            for label in labels:
                if label is not None and label!="":
                    name=label
                    qid=str(uuid.uuid4())
                    try:
                        label = Label.objects.get(name=name,label_type="Non-Semantic",qid=qid)
                    except:
                        label=Label.objects.create(name=name,label_type="Non-Semantic",qid=qid)
                    created_post_obj.label.add(label.id)
        # return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        return render(
            request,
            "posts.html",
            {
                "posts": posts,
                "user_liked_posts":user_liked_posts,
                "user_bookmarked_posts":user_bookmarked_posts,
                "owner": user.first_name + " " + user.last_name,
                "DOMAIN_URL": DOMAIN_URL,
            },
        )

    @action(detail=True, methods=["get"], name="Like Post")
    def like_post(self, request, pk=None):
        user = User.objects.filter(id=request.user.id).first()
        post = self.get_object()
        post.liked_by.add(user)
        post.save()
        data = Post.objects.all().order_by("-id")
        posts = PostListSerializer(data, many=True).data
        labels=Label.objects.all()

        user_liked_posts = PostListSerializer(Post.objects.filter(liked_by__id=user.id),many=True).data
        user_bookmarked_posts = PostListSerializer(Post.objects.filter(bookmarked_by__id=user.id),many=True).data
        if post.space:
            space_obj = Space.objects.get(id=post.space.id)
            space = SpaceListSerializer(space_obj).data
            return render(
                request,
                "spacePosts.html",
                {
                    "space":space,
                    "posts": posts,
                    "user_liked_posts":user_liked_posts,
                    "user_bookmarked_posts":user_bookmarked_posts,
                    "owner": user.first_name + " " + user.last_name,
                    "DOMAIN_URL": DOMAIN_URL,
                },
            )
        else:
            return render(
                request,
                "posts.html",
                {
                    "posts": posts,
                    "labels": labels,
                    "user_liked_posts":user_liked_posts,
                    "user_bookmarked_posts":user_bookmarked_posts,
                    "owner": user.first_name + " " + user.last_name,
                    "DOMAIN_URL": DOMAIN_URL,
                },
            )


    @action(detail=True, methods=["get"], name="Like Post")
    def undo_like_post(self, request, pk=None):
        user = User.objects.filter(id=request.user.id).first()
        post = self.get_object()
        post.liked_by.remove(user)
        post.save()
        data = Post.objects.filter(liked_by__id=user.id).order_by("-id")
        posts = PostListSerializer(data, many=True).data
        user_liked_posts = PostListSerializer(Post.objects.filter(liked_by__id=user.id),many=True).data
        user_bookmarked_posts = PostListSerializer(Post.objects.filter(bookmarked_by__id=user.id),many=True).data    
        # return Response({"detail":"Liked succesfully"},status=200)
        return render(
            request,
            "likedPosts.html",
            {
                "posts": posts,
                "user_liked_posts":user_liked_posts,
                "user_bookmarked_posts":user_bookmarked_posts,
                "owner": user.first_name + " " + user.last_name,
                "DOMAIN_URL": DOMAIN_URL,
            },
        )

    @action(detail=True, methods=["get"], name="Like Post")
    def bookmark_post(self, request, pk=None):
        user = User.objects.filter(id=request.user.id).first()
        post = self.get_object()
        post.bookmarked_by.add(user)
        post.save()
        labels=Label.objects.all()
        data = Post.objects.all().order_by("-id")
        posts = PostListSerializer(data, many=True).data
        user_liked_posts = PostListSerializer(Post.objects.filter(liked_by__id=user.id),many=True).data
        user_bookmarked_posts = PostListSerializer(Post.objects.filter(bookmarked_by__id=user.id),many=True).data
        if post.space:
            space_obj = Space.objects.get(id=post.space.id)
            space = SpaceListSerializer(space_obj).data
            return render(
                request,
                "spacePosts.html",
                {
                    "space":space,
                    "posts": posts,
                    "user_liked_posts":user_liked_posts,
                    "user_bookmarked_posts":user_bookmarked_posts,
                    "owner": user.first_name + " " + user.last_name,
                    "DOMAIN_URL": DOMAIN_URL,
                },
            )
        else:
            return render(
                request,
                "posts.html",
                {
                    "posts": posts,
                    "labels": labels,
                    "user_liked_posts":user_liked_posts,
                    "user_bookmarked_posts":user_bookmarked_posts,
                    "owner": user.first_name + " " + user.last_name,
                    "DOMAIN_URL": DOMAIN_URL,
                },
            )

    @action(detail=True, methods=["get"], name="Like Post")
    def undo_bookmark_post(self, request, pk=None):
        user = User.objects.filter(id=request.user.id).first()
        post = self.get_object()
        post.bookmarked_by.remove(user)
        post.save()
        data = Post.objects.filter(bookmarked_by__id=user.id).order_by("-id")
        posts = PostListSerializer(data, many=True).data
        user_liked_posts = PostListSerializer(Post.objects.filter(liked_by__id=user.id),many=True).data
        user_bookmarked_posts = PostListSerializer(Post.objects.filter(bookmarked_by__id=user.id),many=True).data    
        # return Response({"detail":"Liked succesfully"},status=200)
        return render(
            request,
            "bookmarkedPosts.html",
            {
                "posts": posts,
                "user_liked_posts":user_liked_posts,
                "user_bookmarked_posts":user_bookmarked_posts,
                "owner": user.first_name + " " + user.last_name,
                "DOMAIN_URL": DOMAIN_URL,
            },
        )

    @action(detail=False, methods=["get"], name="Liked Posts")
    def liked_posts(self, request, pk=None):
        user = User.objects.filter(id=request.user.id).first()
        data = Post.objects.filter(liked_by__id=user.id).order_by("-id")
        posts = PostListSerializer(data, many=True).data
        user_liked_posts = PostListSerializer(Post.objects.filter(liked_by__id=user.id),many=True).data
        user_bookmarked_posts = PostListSerializer(Post.objects.filter(bookmarked_by__id=user.id),many=True).data  
        # return Response({"detail":"Liked succesfully"},status=200)
        return render(
            request,
            "likedPosts.html",
            {
                "posts": posts,
                "user_liked_posts":user_liked_posts,
                "user_bookmarked_posts":user_bookmarked_posts,
                "owner": user.first_name + " " + user.last_name,
                "DOMAIN_URL": DOMAIN_URL,
            },
        )
    @action(detail=False, methods=["get"], name="Liked Posts")
    def bookmarked_posts(self, request, pk=None):
        user = User.objects.filter(id=request.user.id).first()
        data = Post.objects.filter(bookmarked_by__id=user.id).order_by("-id")
        posts = PostListSerializer(data, many=True).data
        user_liked_posts = PostListSerializer(Post.objects.filter(liked_by__id=user.id),many=True).data
        user_bookmarked_posts = PostListSerializer(Post.objects.filter(bookmarked_by__id=user.id),many=True).data  
        # return Response({"detail":"Liked succesfully"},status=200)
        return render(
            request,
            "bookmarkedPosts.html",
            {
                "posts": posts,
                "user_liked_posts":user_liked_posts,
                "user_bookmarked_posts":user_bookmarked_posts,
                "owner": user.first_name + " " + user.last_name,
                "DOMAIN_URL": DOMAIN_URL,
            },
        )

    @action(detail=False, methods=["get"], name="Liked Posts")
    def own_posts(self, request, pk=None):
        user = User.objects.filter(id=request.user.id).first()
        data = Post.objects.filter(owner=user.id).order_by("-id")
        posts = PostListSerializer(data, many=True).data

        # return Response({"detail":"Liked succesfully"},status=200)
        return render(
            request,
            "yourPosts.html",
            {
                "posts": posts,
                "owner": user.first_name + " " + user.last_name,
                "DOMAIN_URL": DOMAIN_URL,
            },
        )

    @action(detail=False, methods=["get"], name="Search Form")
    def search_form(self, request, pk=None):
        posts = None
        spaces = None
        user = request.user
        return render(
            request,
            "search.html",
            {
                "posts": posts,
                "spaces": spaces,
                "owner": user.first_name + " " + user.last_name,
                "DOMAIN_URL": DOMAIN_URL,
            },
        )

    @action(detail=False, methods=["post"], name="Search Request")
    def search_request(self, request, pk=None):
        user = request.user
        data = request.data
        search_keyword = data["search_keyword"]
        space_check_box = data.get("space_check_box")
        post_check_box = data.get("post_check_box")
        user_check_box = data.get("user_check_box")

        if space_check_box and not (post_check_box and user_check_box):
            space_data = Space.objects.filter(
            Q(title__icontains=search_keyword) | Q(description__contains=search_keyword)
        ).distinct()
            post_data=None
            user_data=None

        elif post_check_box and not (space_check_box and user_check_box):
            post_data = Post.objects.filter(
                Q(title__icontains=search_keyword)
                | Q(description__icontains=search_keyword)
                | Q(platform__icontains=search_keyword)
                | Q(link__icontains=search_keyword)
                | Q(space__title__icontains=search_keyword)
                | Q(label__name__icontains=search_keyword)
            ).distinct()
            space_data=None
            user_data=None
        elif user_check_box and not (space_check_box and post_check_box):
            user_data=User.objects.filter(
                Q(first_name__icontains=search_keyword)
                | Q(last_name__icontains=search_keyword)).distinct()
            
            space_data=None
            post_data=None

        else:
            space_data = Space.objects.filter(
            Q(title__contains=search_keyword) | Q(description__contains=search_keyword)
            ).distinct()
            post_data = Post.objects.filter(
                Q(title__icontains=search_keyword)
                | Q(description__icontains=search_keyword)
                | Q(platform__icontains=search_keyword)
                | Q(link__icontains=search_keyword)
                | Q(space__title__icontains=search_keyword)
                | Q(label__name__icontains=search_keyword)
            ).distinct()
            user_data=User.objects.filter(
                Q(first_name__icontains=search_keyword)
                | Q(last_name__icontains=search_keyword)
                | Q(description__icontains=search_keyword)).distinct()

        posts = PostListSerializer(post_data, many=True).data
        spaces = SpaceListSerializer(space_data, many=True).data
        users = UserListSerializer(user_data, many=True).data

        # return Response({"detail":"Liked succesfully"},status=200)
        return render(
            request,
            "search.html",
            {
                "posts": posts,
                "spaces": spaces,
                "users": users,
                "owner": user.first_name + " " + user.last_name,
                "DOMAIN_URL": DOMAIN_URL,
            },
        )

    def retrieve(self, request, *args, **kwargs):
        post_obj = self.get_object()
        print(post_obj)
        post = PostListSerializer(post_obj).data
        comments = Comment.objects.filter(post=post_obj.id)
        annotations = textAnnotation.objects.filter(source=post_obj.id)
        comments_data = CommentListSerializer(comments,many=True).data
        annotations_data = TextAnnotationSerializer(annotations, many=True).data

        comments_of_posts = Comment.objects.filter(post=post_obj.id).first()
        text_annotations_of_posts = textAnnotation.objects.filter(source=post_obj.id).first()
        image_annotations_of_posts = ImageAnnotation.objects.filter(source=post_obj.id).first()
        is_delete_allowed=False
        if not comments_of_posts and not text_annotations_of_posts and not image_annotations_of_posts:
            is_delete_allowed=True
        if request.user.is_anonymous == False:
            user = request.user
            user_liked_posts = PostListSerializer(Post.objects.filter(liked_by__id=user.id),many=True).data
            user_bookmarked_posts = PostListSerializer(Post.objects.filter(bookmarked_by__id=user.id),many=True).data
            return render(
                request,
                "postDetail.html",
                {
                    "is_delete_allowed":is_delete_allowed,
                    "is_post_owner": user.id ==post_obj.owner.id,
                    "post": post,
                    "comments": comments_data,
                    "annotations": annotations_data,
                    "owner": user.first_name + " " + user.last_name,
                    "user_liked_posts": user_liked_posts,
                    "user_bookmarked_posts": user_bookmarked_posts,
                    "DOMAIN_URL": DOMAIN_URL
                },
            )
        else:
            return render(
                request, "mainPosts.html", {"space": data, "DOMAIN_URL": DOMAIN_URL, "UNPROTECTED_ROUTE": True}
            )

    @action(detail=True, methods=["post"], name="Like Post")
    def add_comment(self, request, pk=None):
        post = self.get_object()
        user = request.user
        comment = request.data.get("comment")
        user_obj = User.objects.get(id=user.id)
        Comment.objects.create(user=user_obj,post=post,comment=comment)

        return redirect('/feed/post/' + str(post.id) + '/')


    @action(detail=True, methods=["get"], name="Like Post")
    def delete(self, request, pk=None):
        post = self.get_object()
        user = request.user
        if user.id == post.owner.id:
            post_id = post.id
            post.delete()
        labels=Label.objects.all()
        user_liked_posts = PostListSerializer(Post.objects.filter(liked_by__id=user.id),many=True).data
        user_bookmarked_posts = PostListSerializer(Post.objects.filter(bookmarked_by__id=user.id),many=True).data
        posts = PostListSerializer(Post.objects.all().order_by("created_time"),many=True).data
        if post.space:
            space = SpaceListSerializer(Space.objects.get(id=post.space.id)).data
            data = PostListSerializer(Post.objects.filter(space=space["id"]),many=True).data
            return render(
                request,
                "spacePosts.html",
                {
                    "space":space,
                    "posts": data,
                    "labels":labels,
                    "user_liked_posts":user_liked_posts,
                    "user_bookmarked_posts":user_bookmarked_posts,
                    "owner": user.first_name + " " + user.last_name,
                    "DOMAIN_URL": DOMAIN_URL,
                },
            )
        else:
            return render(
                request,
                "posts.html",
                {
                    "posts": posts,
                    "labels": labels,
                    "user_liked_posts":user_liked_posts,
                    "user_bookmarked_posts":user_bookmarked_posts,
                    "owner": user.first_name + " " + user.last_name,
                    "DOMAIN_URL": DOMAIN_URL,
                },
            )
    @action(detail=True, methods=["get"], name="Like Post")
    def report(self, request, pk=None):
        post = self.get_object()
        user = request.user
        description = request.GET.get("value")
        print(description)
        user_obj = User.objects.get(id=user.id)
        report_obj = Report.objects.create(user=user_obj,post=post,description=description)
        user_liked_posts = PostListSerializer(Post.objects.filter(liked_by__id=user.id),many=True).data
        user_bookmarked_posts = PostListSerializer(Post.objects.filter(bookmarked_by__id=user.id),many=True).data 
        if post.space:
            space = SpaceListSerializer(Space.objects.get(id=post.space.id)).data
            data = PostListSerializer(Post.objects.filter(space=space["id"]),many=True).data
            return render(
                request,
                "spacePosts.html",
                {
                    "space":space,
                    "posts": data,
                    "user_liked_posts":user_liked_posts,
                    "user_bookmarked_posts":user_bookmarked_posts,
                    "owner": user.first_name + " " + user.last_name,
                    "DOMAIN_URL": DOMAIN_URL,
                },
            )
        else:
            posts=PostListSerializer(Post.objects.all(),many=True).data
            labels=Label.objects.all()
            return render(
                request,
                "posts.html",
                {
                    "posts": posts,
                    "user_liked_posts":user_liked_posts,
                    "user_bookmarked_posts":user_bookmarked_posts,
                    "labels": labels,
                    "owner": user.first_name + " " + user.last_name,
                    "DOMAIN_URL": DOMAIN_URL,
                },
            )
    @action(detail=True, methods=["get"], name="Like Post")
    def edit_form(self, request, pk=None):
        post_obj = self.get_object()
        print(post_obj)
        post = PostListSerializer(post_obj).data
        labels=Label.objects.all()
        post_labels = post_obj.label.all()
        if request.user.is_anonymous == False:
            user = request.user
            user_liked_posts = PostListSerializer(Post.objects.filter(liked_by__id=user.id),many=True).data
            user_bookmarked_posts = PostListSerializer(Post.objects.filter(bookmarked_by__id=user.id),many=True).data

            if user.id ==post_obj.owner.id:
                return render(
                    request,
                    "editPost.html",
                    {
                        "post": post,
                        "labels":labels,
                        "post_labels":post_labels,
                        "owner": user.first_name + " " + user.last_name,
                        "DOMAIN_URL": DOMAIN_URL,
                    },
                )
            else:
                return render(
                    request,
                    "postDetail.html",
                    {
                        "post": post,
                        "owner": user.first_name + " " + user.last_name,
                        "user_liked_posts": user_liked_posts,
                        "user_bookmarked_posts": user_bookmarked_posts,
                        "DOMAIN_URL": DOMAIN_URL,
                    },
                )
        else:
            return render(
                request, "mainPosts.html", {"space": data, "DOMAIN_URL": DOMAIN_URL, "UNPROTECTED_ROUTE": True}
            )
    @action(detail=True, methods=["post"], name="Like Post")
    def edit(self, request, pk=None):
        post = self.get_object()
        title= request.data.get("title")
        if title:
            post.title = title
        description= request.data.get("description")
        if description:
            post.description=description
        post_link= request.data.get("post_link")
        if post_link:
            post.post_link=post_link
        platform= request.data.get("platform")
        if platform:
            post.platform=platform
        image= request.data.get("image")
        if image:
            post.image=image
        label = request.data.get("label")
        if label:
            post.label.set(label)
        post.save()
        data = PostListSerializer(post).data

        user = request.user
        user_liked_posts = PostListSerializer(Post.objects.filter(liked_by__id=user.id),many=True).data
        user_bookmarked_posts = PostListSerializer(Post.objects.filter(bookmarked_by__id=user.id),many=True).data

        return render(
                request,
                "postDetail.html",
                {
                    "is_post_owner": user.id==post.owner.id,
                    "post": data,
                    "owner": user.first_name + " " + user.last_name,
                    "user_liked_posts": user_liked_posts,
                    "user_bookmarked_posts": user_bookmarked_posts,
                    "DOMAIN_URL": DOMAIN_URL,
                },
            )


    def list(self, request, *args, **kwargs):
        data = Post.objects.all().order_by("-id")
        labels = Label.objects.all()
        posts = PostListSerializer(data, many=True).data
        print('is_confirmed:', request.data.get("is_confirmed"))

        if request.user.is_anonymous == False:
            user = request.user
            user_liked_posts = PostListSerializer(Post.objects.filter(liked_by__id=user.id),many=True).data
            user_bookmarked_posts = PostListSerializer(Post.objects.filter(bookmarked_by__id=user.id),many=True).data 
            return render(
                request,
                "posts.html",
                {
                    "posts": posts,
                    "user_liked_posts":user_liked_posts,
                    "user_bookmarked_posts":user_bookmarked_posts,
                    "labels": labels,
                    "owner": user.first_name + " " + user.last_name,
                    "DOMAIN_URL": DOMAIN_URL,
                },
            )
        else:
            # return Response(PostListSerializer(posts,many=True).data,status=200)
            return render(
                request, "posts.html", {"posts": posts, "DOMAIN_URL": DOMAIN_URL}
            )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response("Deleted successfully", status=200)

    def get_serializer_class(self, *args, **kwargs):
        if self.action == "retrieve" or self.action == "list":
            return PostListSerializer
        else:
            return PostCreateSerializer

    def get_permissions(self):
        if self.action == "retrive" or self.action == "list":
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

class CreateTextAnnotationView(viewsets.ModelViewSet,generics.CreateAPIView,generics.ListAPIView):
    serializer_class = TextAnnotationSerializer
    
    def get_queryset(self):
        source = self.request.query_params.get('source')
        if source:
            queryset = textAnnotation.objects.filter(source=source)
        else:
            queryset = textAnnotation.objects.all()
        return queryset
    
    def create(self, request, *args, **kwargs, ):
        user = request.user
        source = request.data.get("source")
        post = Post.objects.get(id=source)
        start = request.data.get("start")
        body_description = request.data.get("body_description")
        end = request.data.get("end")
        type = request.data.get("type")
        selector_type = request.data.get("selector_type")
        user_obj = User.objects.get(id=user.id)

        textAnnotation.objects.create(source=post,start=start, end=end, type=type, selector_type=selector_type, created_by=user_obj, body_description=body_description)
        
        return redirect("/feed/post/" + str(source) + '/')


class CreateImagennotationView(viewsets.ModelViewSet,generics.CreateAPIView,generics.ListAPIView):
    serializer_class = ImageAnnotationSerializer
    
    def get_queryset(self):
        source = self.request.query_params.get('source')
        if source:
            queryset = ImageAnnotation.objects.filter(source=source)
        else:
            queryset = ImageAnnotation.objects.all()
        return queryset
    

    def create(self, request, *args, **kwargs, ):
        user = request.user
        source = request.data.get("source")
        post = Post.objects.get(id=source)
        start = request.data.get("start")
        body_description = request.data.get("body_description")
        end = request.data.get("end")
        type = request.data.get("type")
        selector_type = request.data.get("selector_type")
        user_obj = User.objects.get(id=user.id)

        textAnnotation.objects.create(source=post,start=start, end=end, type=type, selector_type=selector_type, created_by=user_obj, body_description=body_description)
        
        return redirect("/feed/post/" + str(source) + '/')
