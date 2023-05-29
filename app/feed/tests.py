from django.test import TestCase

from .models import Space, Label, Post
from user.models import User


class LabelModelTest(TestCase):
    @classmethod
    def setUp(cls):
        Label.objects.create(name="Label 1")

    def test_name(self):
        label = Label.objects.get(id=1)
        expected_object_name = f"{label.name}"
        self.assertEqual(str(label), expected_object_name)


class SpaceModelTest(TestCase):
    @classmethod
    def setUp(cls):
        user = User.objects.create_user(
            first_name="John",
            last_name="Doe",
            email="john.doe@test.com",
            username="john.doe@test.com",
            password="1234qwer",
        )

        moderator = User.objects.create_user(
            first_name="Joe",
            last_name="Doe",
            email="joe.doe@test.com",
            username="joe.doe@test.com",
            password="1234qwer",
        )

        member = User.objects.create_user(
            first_name="Alex",
            last_name="Davis",
            email="alex.davis@test.com",
            username="alex.davis@test.com",
            password="1234qwer",
        )
        moderator_default = User.objects.create_user(
            first_name="Mary",
            last_name="Brown",
            email="mary.brown@test.com",
            username="mary.brown@test.com",
            password="1234qwer",
        )

        member_default = User.objects.create_user(
            first_name="Robert",
            last_name="Williams",
            email="robert.williams@test.com",
            username="robert.williams@test.com",
            password="1234qwer",
        )

        space_obj = Space.objects.create(title="Space 1", description="Description", owner=user)
        space_obj.moderator.add(moderator_default)
        space_obj.member.add(member_default)

    def test_name(self):
        space = Space.objects.get(id=1)
        expected_object_name = f"{space.title}"
        self.assertEqual(str(space), expected_object_name)

    def test_owner(self):
        space = Space.objects.get(id=1)
        user = User.objects.get(id=1)
        expected_owner = user
        self.assertEqual(space.owner, expected_owner)

    def test_adding_moderator(self):
        space = Space.objects.get(id=1)
        moderator = User.objects.get(id=2)
        space.moderator.add(moderator)
        self.assertTrue(space.moderator.filter(id=moderator.id).exists())

    def test_adding_member(self):
        space = Space.objects.get(id=1)
        member = User.objects.get(id=3)
        space.member.add(member)
        self.assertTrue(space.member.filter(id=member.id).exists())

    def test_moderator(self):
        space = Space.objects.get(id=1)
        moderator = User.objects.get(id=4)
        expected_moderator = moderator
        self.assertEqual(space.moderator.filter(id=moderator.id).first(), expected_moderator)

    def test_member(self):
        space = Space.objects.get(id=1)
        member = User.objects.get(id=5)
        expected_member= member
        self.assertEqual(space.member.filter(id=member.id).first(), expected_member)


class PostModelTest(TestCase):
    @classmethod
    def setUp(cls):
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
        space = Space.objects.create(
            title="Space 1", description="Description", owner=user
        )
        post = Post.objects.create(
            title="Space 1",
            description="Description",
            owner=user,
            platform="Platform",
            space=space,
        )
        post.liked_by.add(user_2)

    def test_name(self):
        post = Post.objects.get(id=1)
        expected_object_name = f"{post.title}"
        self.assertEqual(str(post), expected_object_name)

    def test_owner(self):
        post = Post.objects.get(id=1)
        user = User.objects.get(id=1)
        expected_owner = user
        self.assertEqual(post.owner, expected_owner)

    def test_liked_by(self):
        post = Post.objects.get(id=1)
        user = User.objects.get(id=2)
        self.assertEqual(post.liked_by.filter(email=user.email).exists(), True)
