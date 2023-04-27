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


# Create your views here.

import requests
from django.http import JsonResponse

def wikidata_search(request):
    label = request.GET.get('label')
    if label:
        url = f"https://www.wikidata.org/w/api.php?action=wbsearchentities&format=json&language=en&type=item&search={label}"
        response = requests.get(url)
        if response.ok:
            data = response.json()
            print(data)
            suggestions = [result["label"] for result in data["search"]]
            return JsonResponse(suggestions, safe=False)
    return JsonResponse([], safe=False)


class SpaceViewSet(viewsets.ModelViewSet):
    serializer_class = SpaceCreateSerializer
    queryset = Space.objects.all()

    def create(self, request, *args, **kwargs):
        request.data._mutable = True
        user = User.objects.filter(id=request.user.id).first()
        request.data["owner"] = user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        spaces = Space.objects.all().order_by("-id")
        # return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        return render(
            request,
            "spaces.html",
            {
                "spaces": spaces,
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
    def add_moderator(self, request, pk=None):
        return Response("Added successfully", status=200)

    @action(detail=True, methods=["get"], name="Delete Post")
    def delete_post(self, request, pk=None):
        return Response("Deleted successfully from the space.", status=200)

    @action(detail=True, methods=["get"], name="Approve User")
    def approve_user(self, request, pk=None):
        return Response("Approved successfully.", status=200)

    @action(detail=True, methods=["get"], name="Reject User")
    def reject_user(self, request, pk=None):
        return Response("Rejected successfully.", status=200)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response("Deleted successfully", status=200)

    def list(self, request, *args, **kwargs):
        spaces = Space.objects.all().order_by("-id")
        if request.user.is_anonymous == False:
            user = request.user
            return render(
                request,
                "spaces.html",
                {
                    "spaces": spaces,
                    "owner": user.first_name + " " + user.last_name,
                    "DOMAIN_URL": DOMAIN_URL,
                },
            )
        else:
            return render(
                request, "spaces.html", {"spaces": spaces, "DOMAIN_URL": DOMAIN_URL}
            )

    def retrieve(self, request, *args, **kwargs):
        space = self.get_object()
        data = SpaceListSerializer(space).data
        labels = Label.objects.all()
        if request.user.is_anonymous == False:
            user = request.user
            user_liked_posts = PostListSerializer(Post.objects.filter(liked_by__id=user.id),many=True).data
            user_bookmarked_posts = PostListSerializer(Post.objects.filter(bookmarked_by__id=user.id),many=True).data            
            return render(
                request,
                "spacePosts.html",
                {
                    "space": data,
                    "user_liked_posts":user_liked_posts,
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
                    "confirmation_modal": True
                },
            )

        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        data = Post.objects.all().order_by("-id")
        posts = PostListSerializer(data, many=True).data
        headers = self.get_success_headers(serializer.data)
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
        data = Post.objects.all().order_by("-id")
        posts = PostListSerializer(data, many=True).data
        space_obj = Space.objects.get(id=post.space.id)
        space = SpaceListSerializer(space_obj).data
        user_liked_posts = PostListSerializer(Post.objects.filter(liked_by__id=user.id),many=True).data
        user_bookmarked_posts = PostListSerializer(Post.objects.filter(bookmarked_by__id=user.id),many=True).data
        # return Response({"detail":"Liked succesfully"},status=200)
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
        comments_data = CommentListSerializer(comments,many=True).data
        if request.user.is_anonymous == False:
            user = request.user
            user_liked_posts = PostListSerializer(Post.objects.filter(liked_by__id=user.id),many=True).data
            user_bookmarked_posts = PostListSerializer(Post.objects.filter(bookmarked_by__id=user.id),many=True).data

            return render(
                request,
                "postDetail.html",
                {
                    "is_post_owner": user.id ==post_obj.owner.id,
                    "post": post,
                    "comments": comments_data,
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
            space_id = post.space.id
            post_id = post.id
            post.delete()
        space = SpaceListSerializer(Space.objects.get(id=post.space.id)).data
        data = PostListSerializer(Post.objects.filter(space=space_id),many=True).data
        user_liked_posts = PostListSerializer(Post.objects.filter(liked_by__id=user.id),many=True).data
        user_bookmarked_posts = PostListSerializer(Post.objects.filter(bookmarked_by__id=user.id),many=True).data 
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
