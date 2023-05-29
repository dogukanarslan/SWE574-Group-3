from django.test import TestCase
from feed.models import Post
from .models import *
from django.contrib.auth import authenticate

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
class BadgeAssignTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            first_name="John",
            last_name="Doe",
            email="john.doe@test.com",
            username="john.doe@test.com",
            password="1234qwer",
        )
        self.friend = Friends.objects.create(
            owner = self.user,
        )
        user_2 = User.objects.create_user(
            first_name="Miray",
            last_name="Iyidogan",
            email="miray@test.com",
            username="miray@test.com",
            password="1234qwer",
        )
        post = Post.objects.create(
            title="Post 1",
            description="Description",
            #post_link = "https://github.com/dogukanarslan/SWE574-Group-3",
            owner=self.user,
            platform="Platform",
        )

        post.liked_by.add(user_2) 
        self.friend.friend_list.set([user_2])
        self.user.save()

    def test_assign_badge(self):      
        self.user.refresh_from_db()
        badge = self.user.badge
        self.assertEqual('1', badge.level)