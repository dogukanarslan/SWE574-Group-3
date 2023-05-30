import datetime
from django.test import TestCase

from .models import Space, Label, Post,Annotation
from feed.serializers import AnnotationSerializer
from django.urls import reverse
from rest_framework.test import APIClient
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



class AnnotationViewTest(TestCase):
    databases = {'default'}

    def setUp(self):
        self.client = APIClient()
        self.test_user = User.objects.using("default").create(
            first_name="John",
            last_name="Doe",
            email="john.doe@test.com",
            username="john.doe@test.com",
            password="1234qwer",
        )

        # Set up test TextAnnotations
        self.test_annotation_1 = Annotation.objects.using("default").create(
            id=3,
            context="http://www.w3.org/ns/anno.jsonld",
            type="Annotation",
            target={
                "source": "http://127.0.0.1:8000/1/",
                "selector": {
                    "end": 117,
                    "type": "TextPositionSelector",
                    "start": 97
                }
            },
            body={
                "type": "TextualBody",
                "value": "also Lucid Motors is one the clean energy car company!"
            }
        )

        self.test_annotation_2 = Annotation.objects.using("default").create(
            id=4,
            context="http://www.w3.org/ns/anno.jsonld",
            type="Annotation",
            target={
                "id": "http://13.48.149.195:8000/static/default_post_image.png",
                "type": "Image",
                "source": "http://127.0.0.1:8000/1/",
            },
            body={
                "type": "TextualBody",
                "value": "model s or model y?"
            }
        )
        self.view_url = reverse('feed:annotation-list') 


    def test_get_queryset(self):
        # Send a GET request to the view
        response_1 = self.client.get(self.view_url + '?source=1&text=true')
        response_2 = self.client.get(self.view_url + '?source=1&image=true')

        # Check that the status code is 200 (OK)
        self.assertEqual(response_1.status_code, 200)
        self.assertEqual(response_2.status_code, 200)


    def test_create(self):
        # Prepare the POST data
        data_1 = {
            "id": 3,
            "type": "Annotation",
            "created": "2023-05-27T11:20:26.275258Z",
            "body": {
                "type": "TextualBody",
                "value": "also Lucid Motors is one the clean energy car company!"
            },
            "target": {
                "source": "http://127.0.0.1:8000/1/",
                "selector": {
                    "end": 117,
                    "type": "TextPositionSelector",
                    "start": 97
                }
            },
            "@context": "http://www.w3.org/ns/anno.jsonld"
        }

        data_2 = {
            "id": 4,
            "type": "Annotation",
            "created": "2023-05-27T11:21:10.367183Z",
            "body": {
                "type": "TextualBody",
                "value": "model s or model y?"
            },
            "target": {
                "id": "http://13.48.149.195:8000/static/default_post_image.png",
                "type": "Image",
                "source": "http://127.0.0.1:8000/1/",
            },
            "@context": "http://www.w3.org/ns/anno.jsonld"
        }

        # Send POST requests to the view
        response_1 = self.client.post(self.view_url, json=data_1)
        response_2 = self.client.post(self.view_url, json=data_2)

        # Check that the status code is 201 (Created)
        self.assertEqual(response_1.status_code, 201)
        self.assertEqual(response_2.status_code, 201)

        # Check that the response message is correct
        self.assertEqual(response_1.data, "Annotation saved")
        self.assertEqual(response_2.data, "Annotation saved")

        # Check that the new annotations were created
        self.assertTrue(Annotation.objects.using("default").filter(body=data_1['body'], target=data_1['target']).exists())
        self.assertTrue(Annotation.objects.using("default").filter(body=data_2['body'], target=data_2['target']).exists())