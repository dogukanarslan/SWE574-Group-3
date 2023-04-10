from django.shortcuts import render
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from rest_framework.decorators import action
from .serializers import *
from .models import *
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from user.permissions import IsSpaceOwnerPermission, IsModeratorPermission
from user.models import User
from app.settings import DOMAIN_URL
from django.db.models import Q

# Create your views here.


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
        space = Space.objects.get(id=serializer.data["id"])
        
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
    def space_settings_form(self, request, pk=None):
        space = self.get_object()
        space_data = SpaceListSerializer(space).data
        user=request.user
        return render(
                request,
                "spaceSettings.html",
                {
                    "space": space_data,
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
    def add_moderator(self, request, pk=None):
        space = self.get_object()
        space_data = SpaceListSerializer(space).data
        user=request.user
        user_id = request.GET.get("value")
        user_obj = User.objects.get(id=user_id)
        space.moderator.add(user_obj)
        space.save()
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


    @action(detail=True, methods=["get"], name="Approve User")
    def send_join_request_to_space(self, request, pk=None):
        user = request.user
        spaces = Space.objects.all().order_by("-id")
        user_obj = User.objects.get(id=user.id)
        space = self.get_object()
        space_join_request= SpaceJoinRequest.objects.create(owner=user_obj, space=space)
        return render(
                request,
                "spaces.html",
                {
                    "spaces": spaces,
                    "owner": user.first_name + " " + user.last_name,
                    "DOMAIN_URL": DOMAIN_URL,
                },
            )
    @action(detail=True, methods=["get"], name="Accept User")
    def accept_space_join_request(self, request, pk=None):
        space_join_request = SpaceJoinRequest.objects.get(id=self.kwargs['pk'])
        space_join_request.status = "Accepted"
        space_join_request.save()
        space = Space.objects.get(id=space_join_request.space.id)
        user = User.objects.get(id=space_join_request.owner.id)
        space.member.add(user)
        space.save()
        space_data = SpaceListSerializer(space).data
        return Response(space_data, status=200)

    @action(detail=True, methods=["get"], name="Reject User")
    def reject_space_join_request(self, request, pk=None):
        space_join_request = SpaceJoinRequest.objects.get(id=self.kwargs['pk'])
        space_join_request.status = "Rejected"
        space_join_request.save()
        space = Space.objects.get(id=space_join_request.space.id)
        space_data = SpaceListSerializer(space).data
        return Response(space_data, status=200)

    @action(detail=True, methods=["get"], name="Reject User")
    def list_space_join_requests(self, request, pk=None):
        space = self.get_object()
        user=request.user
        user_data = UserListSerializer(request.user).data
        data = SpaceListSerializer(space).data
        space_join_requests=SpaceJoinRequest.objects.filter(space=space.id,status="Pending")
        space_join_request_data = SpaceJoinRequestListSerializer(space_join_requests,many=True).data
        space_members_data = UserListSerializer(space.member,many=True).data
        if request.user.id in space.moderator.all() or request.user.id == space.owner.id:
            user = request.user
            return render(
                request,
                "spaceJoinRequest.html",
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
            user = request.user
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
            user = request.user
            user_data = UserListSerializer(user).data
            owner_or_member_space_data = SpaceListSerializer(Space.objects.filter(Q(member__id__exact=user.id)| Q(owner=user.id)),many=True).data
            spaces_data_array = []
            owner_or_member_spaces_data_array = []
            recommanded_spaces = []
            
            for space_data in spaces_data:
                space_dict={}
                space_dict["id"]=space_data["id"]
                space_dict["owner"]=space_data["owner"]["id"]
                space_dict["words_of_description"]=space_data["description"].split()
                spaces_data_array.append(space_dict)

            for owner_or_member in owner_or_member_space_data:
                space_dict={}
                space_dict["id"]=owner_or_member["id"]
                space_dict["owner"]=space_data["owner"]["id"]
                space_dict["words_of_description"]=owner_or_member["description"].split()
                owner_or_member_spaces_data_array.append(space_dict)
                            
            for element_space in spaces_data_array:
                for element_owner_or_member_space in owner_or_member_spaces_data_array:
                    if element_space["id"] != element_owner_or_member_space["id"] and element_space["owner"] != element_owner_or_member_space["owner"] :
                        print("after",element_space["owner"], element_owner_or_member_space["owner"])
                        if common_data(element_owner_or_member_space["words_of_description"],element_space["words_of_description"]):
                            if SpaceListSerializer(Space.objects.get(id=element_space["id"])).data not in recommanded_spaces:
                                recommanded_spaces.append(SpaceListSerializer(Space.objects.get(id=element_space["id"])).data)
            return render(
                request,
                "spaces.html",
                {
                    "spaces": spaces_data,
                    "user_data":user_data,
                    "recommanded_spaces":recommanded_spaces,
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
            user_data = UserListSerializer(user).data
            user_liked_posts = PostListSerializer(Post.objects.filter(liked_by__id=user.id),many=True).data
            user_bookmarked_posts = PostListSerializer(Post.objects.filter(bookmarked_by__id=user.id),many=True).data            
            return render(
                request,
                "spacePosts.html",
                {
                    "space": data,
                    "user_data":user_data,
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
            if user.id ==post_obj.owner.id or user.id==post_obj.space.owner.id or post_obj.space.moderator.filter(id=user.id):
                return render(
                    request,
                    "ownPostDetail.html",
                    {
                        "post": post,
                        "comments": comments_data,
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
                        "comments": comments_data,

                        "owner": user.first_name + " " + user.last_name,
                        "DOMAIN_URL": DOMAIN_URL,
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
        comment_obj = Comment.objects.create(user=user_obj,post=post,comment=comment)
        comments = Comment.objects.filter(post=post.id)
        print(comments)
        comment_data = CommentListSerializer(comments,many=True).data
        data = PostListSerializer(post).data
        user = request.user
        if user.id ==post.owner.id:        
            return render(
            request,
            "ownPostDetail.html",
            {
                "posts": data,
                "comments": comment_data,
                "owner": user.first_name + " " + user.last_name,
                "DOMAIN_URL": DOMAIN_URL,
            },
        )
        else:
            return render(
                    request,
                    "postDetail.html",
                    {
                        "comments": comment_data,
                        "post": data,
                        "owner": user.first_name + " " + user.last_name,
                        "DOMAIN_URL": DOMAIN_URL,
                    },
                )

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
        if user.id ==post.owner.id:
            return render(
                    request,
                    "ownPostDetail.html",
                    {
                        "post": data,
                        "owner": user.first_name + " " + user.last_name,
                        "DOMAIN_URL": DOMAIN_URL,
                    },
                )
        else:
            return render(
                    request,
                    "postDetail.html",
                    {
                        "post": data,
                        "owner": user.first_name + " " + user.last_name,
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

def common_data(list1, list2):
    result = False
    for x in list1:
        for y in list2:
            if x == y:
                result = True
                return result    
    return result
