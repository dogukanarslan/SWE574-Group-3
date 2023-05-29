import datetime
from django.test import TestCase

from .models import Space, Label, Post,Annotation
from feed.serializers import AnnotationSerializer
from django.urls import reverse
from rest_framework.test import APIClient
from user.models import User



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