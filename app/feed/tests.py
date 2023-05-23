from django.test import TestCase


from .models import Space, Label, Post, TextAnnotation
from user.models import User

from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from .serializers import TextAnnotationSerializer


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
        Space.objects.create(title="Space 1", description="Description", owner=user)

    def test_name(self):
        space = Space.objects.get(id=1)
        expected_object_name = f"{space.title}"
        self.assertEqual(str(space), expected_object_name)

    def test_owner(self):
        space = Space.objects.get(id=1)
        user = User.objects.get(id=1)
        expected_owner = user
        self.assertEqual(space.owner, expected_owner)


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

class TextAnnotationViewTest(TestCase):
    databases = {'annotation_db'}
    def setUp(self):
        self.client = APIClient()
        self.test_user = User.objects.create_user(
            first_name="John",
            last_name="Doe",
            email="john.doe@test.com",
            username="john.doe@test.com",
            password="1234qwer",
        )

        # Set up a test TextAnnotation
        self.test_annotation = TextAnnotation.objects.create(
            context="http://www.w3.org/ns/anno.jsonld",
            type="Annotation",
            target={"source": "http://127.0.0.1:8000/feed/post/1/"},
            body={"unit test"},
        )
        self.view_url = reverse('textannotation-list')  

    def test_get_queryset(self):
        # Send a GET request to the view
        response = self.client.get(self.view_url + '?source=testsource')

        # Check that the status code is 200 (OK)
        self.assertEqual(response.status_code, 200)

        # Check that the response data matches the test annotation
        serializer = TextAnnotationSerializer(self.test_annotation)
        self.assertEqual(response.data[0], serializer.data)

    def test_create(self):
        # Prepare the POST data
        data = {
            "id": 1,
            "type": "Annotation",
            "created": "2023-05-21T10:04:06.333370Z",
            "target" : {"source": "http://127.0.0.1:8000/feed/post/1/"},
            "body" : {"unit test"},
            "@context": "http://www.w3.org/ns/anno.jsonld"
    }

        # Send a POST request to the view
        response = self.client.post(self.view_url, data)

        # Check that the status code is 201 (Created)
        self.assertEqual(response.status_code, 201)

        # Check that the response message is correct
        self.assertEqual(response.data, "Annotation saved")

        # Check that the new annotation was created
        self.assertTrue(TextAnnotation.objects.filter(body=data['body'], target=data['target']).exists())
