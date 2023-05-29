from django.test import TestCase
# Create your tests here.
from .models import *
from django.contrib.auth import authenticate, login, logout
from feed.models import Post
from .serializers import UserListSerializer


class UserLoginTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            first_name="John",
            last_name="Doe",
            email="john.doe@test.com",
            username="john.doe@test.com",
            password="1234qwer",
        )
        self.user.save()

    def test_login_user(self):
        user = authenticate(username="john.doe@test.com", password="1234qwer")
        self.assertTrue((user is not None) and user.is_authenticated)

    def test_wrong_username(self):
        user = authenticate(username="wrong", password="1234qwer")
        self.assertFalse(user is not None and user.is_authenticated)

    def test_wrong_password(self):
        user = authenticate(username="john.doe@test.com", password="wrong")
        self.assertFalse(user is not None and user.is_authenticated)

    def test_login_user_with_request(self):
        response = self.client.post(
            "/user/login/", {"email": "john.doe@test.com", "password": "1234qwer"}
        )
        print("response", response)
        self.assertTrue(response.status_code == 302)

    def test_wrong_password_with_request(self):
        response = self.client.post(
            "/user/login/", {"email": "john.doe@test.com", "password": "wrong"}
        )
        self.assertFalse(response.status_code == 302)

class BadgeTestCase(TestCase):
    def setUp(self):
        user = User.objects.create_user(
            first_name="John",
            last_name="Doe",
            email="john.doe@test.com",
            username="john.doe@test.com",
            password="1234qwer",
        )
        user_2 = User.objects.create_user(
            first_name="Joe",
            last_name="Doe",
            email="joe.doe@test.com",
            username="joe.doe@test.com",
            password="1234qwer",
        )
        friends = Friends.objects.create(owner = user_2)
        post = Post.objects.create(
                title="Post 1",
                description="Description",
                owner=user,
                platform="Platform",
            )
        post.liked_by.add(user_2.id)
        friends.friend_list.add(user.id)

    def test_assign_badge(self):
        user = User.objects.get(id=1)
        user_data = UserListSerializer(user).data
        self.assertEqual(1,user_data["badge"].id)