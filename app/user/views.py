from django.shortcuts import render, redirect
from django.template.response import TemplateResponse
import re
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import *
from .serializers import *
from django.contrib.auth import authenticate, login, logout
from .sendEmail import sendEmail
from django.db.models.signals import post_save
from django.dispatch import receiver

EMAIL_FORMAT_REGEX = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
import uuid
from feed.models import Space
from app.settings import DOMAIN_URL

def index(request):
    print(request.user)
    spaces = Space.objects.all()
    return render(request, "main.html", {"spaces": spaces, "DOMAIN_URL": DOMAIN_URL, "UNPROTECTED_ROUTE": True})

class UserViewSet(viewsets.ModelViewSet):
    User = get_user_model()
    queryset = User.objects.all()

    def create(self, request, *args, **kwargs):
        first_name = request.data.get("first_name")
        last_name = request.data.get("last_name")
        email = request.data.get("email")
        password = request.data.get("password")
        password2 = request.data.get("password2")

        if first_name is None or first_name == "":
            args = {}
            args["error"] = "First Name can not be empty."
            args["DOMAIN_URL"] = DOMAIN_URL
            return render(request, "error.html", args)

        if last_name is None or last_name == "":
            args = {}
            args["error"] = "Last Name can not be empty."
            args["DOMAIN_URL"] = DOMAIN_URL
            return render(request, "error.html", args)

        if email is None or email == "":
            args = {}
            args["error"] = "Email can not be empty."
            args["DOMAIN_URL"] = DOMAIN_URL
            return render(request, "error.html", args)

        if password is None or password == "":
            args = {}
            args["error"] = "Password can not be empty."
            args["DOMAIN_URL"] = DOMAIN_URL
            return render(request, "error.html", args)

        if password2 is None or password2 == "":
            args = {}
            args["error"] = "Password Confimation can not be empty."
            args["DOMAIN_URL"] = DOMAIN_URL
            return render(request, "error.html", args)

        if re.fullmatch(EMAIL_FORMAT_REGEX, email) is None:
            args = {}
            args["error"] = "Email format is invalid."
            args["DOMAIN_URL"] = DOMAIN_URL
            return render(request, "error.html", args)

        user_exist = User.objects.filter(email=email).first()
        if user_exist:
            args = {}
            args["error"] = "There is already an account with this email."
            args["DOMAIN_URL"] = DOMAIN_URL
            return render(request, "error.html", args)
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            Friends.objects.create(owner=User.objects.get(email=email))
            return render(request, "login.html", {"DOMAIN_URL": DOMAIN_URL, "UNPROTECTED_ROUTE": True})
        else:
            args = {}
            args["error"] = "Passwords are not matched."
            args["DOMAIN_URL"] = DOMAIN_URL
            return render(request, "error.html", args)

    @action(detail=False, methods=["GET"])
    def register_form(self, request, *args, **kwargs):
        print(request.user)
        return render(request, "register.html", {"DOMAIN_URL": DOMAIN_URL, "UNPROTECTED_ROUTE": True})

    @action(detail=False, methods=["GET"])
    def login_form(self, request, *args, **kwargs):
        return render(request, "login.html", {"DOMAIN_URL": DOMAIN_URL, "UNPROTECTED_ROUTE": True})

    @action(detail=False, methods=["POST"])
    def login(self, request):
        data = request.data
        user = User.objects.filter(email=request.data.get("email")).first()
        if not user:
            args = {}
            args["error"] = "There is no account with this email."
            args["DOMAIN_URL"] = DOMAIN_URL
            return render(request, "error.html", args)

        serializer = UserLoginSerializer(data=data)
        if serializer.is_valid(raise_exception=True):
            res = {
                "success": "True",
                "status code": status.HTTP_200_OK,
                "message": "User logged in  successfully",
            }
            new_data = serializer.data
            res.update(new_data)
            # return Response(res,200)
            login(request, user)
            # return render (request=request, template_name="loginSuccess.html")
            spaces = Space.objects.all().order_by("-id")
            return redirect(
                "/feed/space/",
                {
                    "spaces": spaces,
                    "owner": user.first_name + " " + user.last_name,
                    "DOMAIN_URL": DOMAIN_URL,
                },
            )

    @action(detail=False, methods=["GET"])
    def logout(self, request, *args, **kwargs):
        logout(request)
        return redirect("/user/login_form/", {"DOMAIN_URL": DOMAIN_URL})

    @action(detail=False, methods=["get"], name="See Profile")
    def following(self, request, *args, **kwargs):
        user = User.objects.get(email=request.user.email)
        try:
            friends = Friends.objects.get(owner=user.id)
        except Friends.DoesNotExist:
            friends = None
        if friends:
            friend_list = friends.friend_list.all()
            users=UserListSerializer(friend_list,many=True).data
        else:
            users = []
        return render(
            request,
            "following.html",
            {
                "users": users,
                "owner": user.first_name + " " + user.last_name,
                "DOMAIN_URL": DOMAIN_URL,
            },
        )
    
    @action(detail=False, methods=["get"], name="See Profile")
    def possible_to_know(self, request, *args, **kwargs):
        user = request.user
        users = User.objects.exclude(id=request.user.id)
        user_data = UserListSerializer(users,many=True).data
        try:
            friends = Friends.objects.get(owner=user.id)
            followings = UserListSerializer(friends.friend_list.all(), many=True).data
        except Friends.DoesNotExist:
            followings = []
        return render(
            request,
            "possibleToKnow.html",
            {
                "users": user_data,
                "followings": followings,
                "owner": user.first_name + " " + user.last_name,
                "DOMAIN_URL": DOMAIN_URL,
            },
        )

    @action(detail=False, methods=["get"], name="See Profile")
    def followers(self, request, *args, **kwargs):
        user = request.user
        followers = []
        friends = Friends.objects.filter(friend_list=user)
        following_friends = Friends.objects.filter(owner=user).first()
        followings = []
        if following_friends:
            followings = UserListSerializer(following_friends.friend_list.all(), many=True).data
        for friend in friends:
            followers.append(UserListSerializer(friend.owner).data)
        return render(
            request,
            "follower.html",
            {
                "users":followers,
                "followings":followings,
                "owner": user.first_name + " " + user.last_name,
                "DOMAIN_URL": DOMAIN_URL,
            },
        )

    @action(detail=True, methods=["get"], name="See Profile")
    def follow(self, request, *args, **kwargs):
        user = request.user
        user_obj = User.objects.get(email=user.email)
        user_data=UserListSerializer(user_obj).data
        friends = Friends.objects.get(owner=user)
        follow_people = self.get_object()
        friends.friend_list.add(follow_people.id)
        friends.save()
        users = User.objects.exclude(id=request.user.id)
        user_data = UserListSerializer(users,many=True).data
        following_friends=Friends.objects.get(owner=user.id)
        followings=UserListSerializer(following_friends.friend_list.all(),many=True).data
        return render(
            request,
            "possibleToKnow.html",
            {
                "users":user_data,
                "followings":followings,
                "owner": user.first_name + " " + user.last_name,
                "DOMAIN_URL": DOMAIN_URL,
            },
        )
    @action(detail=True, methods=["get"], name="See Profile")
    def unfollow(self, request, *args, **kwargs):
        user = request.user
        friends = Friends.objects.get(owner=user)
        follow_people = self.get_object()
        friends.friend_list.remove(follow_people.id)
        friends.save()
        friends=Friends.objects.get(owner=user.id)
        user_data=UserListSerializer(friends.friend_list.all(),many=True).data
        return render(
            request,
            "following.html",
            {
                "users":user_data,
                "owner": user.first_name + " " + user.last_name,
                "DOMAIN_URL": DOMAIN_URL,
            },
        )
    @action(detail=False, methods=["get"], name="See Profile")
    def profile_form(self, request, *args, **kwargs):
        user = request.user
        user_obj = User.objects.get(email=user.email)
        user_data=UserListSerializer(user_obj).data
        return render(
            request,
            "profilePage.html",
            {
                "owner": user.first_name + " " + user.last_name,
                "DOMAIN_URL": DOMAIN_URL,
                "user_data": user_data,
            },
        )

    @action(detail=False, methods=["post"], name="Update Profile")
    def profile_update_request(self, request, *args, **kwargs):
        user = request.user
        user_obj = User.objects.get(email=user.email)
        user_data=UserListSerializer(user_obj).data
        if request.data["first_name"]:
            user.first_name = request.data["first_name"]
            user.save()
        if request.data["last_name"]:
            user.last_name = request.data["last_name"]
            user.save()
        if request.data["description"]:
            user_obj.description = request.data["description"]
            user_obj.save()
        return render(
            request,
            "profilePage.html",
            {
                "owner": user.first_name + " " + user.last_name,
                "DOMAIN_URL": DOMAIN_URL,
                "user_data": user_data,
            },
        )

    @action(detail=False, methods=["get"], name="Reset Password")
    def reset_password_form(self, request, *args, **kwargs):
        return render(request, "resetPasswordRequest.html", {"DOMAIN_URL": DOMAIN_URL, "UNPROTECTED_ROUTE": True})

    @action(detail=False, methods=["post"], name="Reset Password")
    def reset_password_request(self, request, *args, **kwargs):
        data = request.data
        email = data.get("email")
        code = uuid.uuid4()
        ResetPassword.objects.create(email=email, code=code)
        sendEmail(email, code)
        # return Response({"detail": "The code for resetting password is sent to your email address."})
        return render(request, "resetPassword.html", {"DOMAIN_URL": DOMAIN_URL})

    @action(detail=False, methods=["post"], name="Reset Password")
    def reset_password(self, request, *args, **kwargs):
        data = request.data
        print(request.data)
        email = data.get("email")
        code = data.get("code")
        user = User.objects.get(email=email)
        reset_password_obj = ResetPassword.objects.filter(email=email).first()
        if reset_password_obj:
            if reset_password_obj.code == code:
                if data["password"] != data["password2"]:
                    raise ValidationError({"error": "New passwords do not match"})
                else:
                    user.set_password(data["password"])
                    user.save()
                    reset_password_obj.delete()
                    # return Response({"detail": "Password is reset successfully"})
                    return render(request, "login.html", {"DOMAIN_URL": DOMAIN_URL})

            # return Response({"detail": "Incorrect Reset Code"})
            args = {}
            args["error"] = "Incorrect Reset Code."
            args["DOMAIN_URL"] = DOMAIN_URL
            return render(request, "error.html", args)

        # return Response({"detail": "Incorrect Credentials"})
        args = {}
        args["error"] = "Incorrect Credentials."
        args["DOMAIN_URL"] = DOMAIN_URL
        return render(request, "error.html", args)

    @action(detail=False, methods=["get"], name="Change Password Form")
    def change_password_form(self, request, pk=None):
        user = request.user
        return render(
            request,
            "changePassword.html",
            {
                "owner": user.first_name + " " + user.last_name,
                "DOMAIN_URL": DOMAIN_URL,
            },
        )

    @action(detail=False, methods=["post"], name="Change Password")
    def change_password_request(self, request, pk=None):
        data = request.data
        user = request.user
        if user is None:
            args = {}
            args["error"] = "There is no such user"
            args["DOMAIN_URL"] = DOMAIN_URL
            args["owner"] = user.first_name + " " + user.last_name

            return render(request, "changePassword.html", args)

        if user.check_password(data["old_password"]) == False:
            args = {}
            args["error"] = "The old password does not match"
            args["DOMAIN_URL"] = DOMAIN_URL
            args["owner"] = user.first_name + " " + user.last_name

            return render(request, "changePassword.html", args)

        if data["password"] != data["password2"]:
            args = {}
            args["error"] = "New passwords do not match"
            args["owner"] = user.first_name + " " + user.last_name
            args["DOMAIN_URL"] = DOMAIN_URL
            return render(request, "changePassword.html", args)

        user.set_password(data["password"])
        user.save()
        login(request, user)
        return render(
            request,
            "changePassword.html",
            {
                "owner": user.first_name + " " + user.last_name,
                "DOMAIN_URL": DOMAIN_URL,
            },
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)

        return Response("Deleted successfully", status=200)

    def get_serializer_class(self):
        if self.action == "create":
            return UserRegisterSerializer
        else:
            return UserListSerializer
