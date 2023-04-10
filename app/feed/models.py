from django.db import models
from user.models import User
from django.urls import reverse

# Create your models here.


class Space(models.Model):
    title = models.CharField(
        max_length=300, blank=False, null=False, unique=False, default=""
    )
    description = models.CharField(
        max_length=300, blank=True, null=True, unique=False, default=""
    )
    created_time = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(
        User,
        related_name="own_spaces",
        null=True,
        unique=False,
        on_delete=models.CASCADE,
    )
    moderator = models.ManyToManyField(
        User, blank=True, null=True, related_name="moderator_of_spaces"
    )
    
    def __str__(self):
        return self.title


class Label(models.Model):
    name = models.CharField(
        max_length=300, blank=False, null=False, unique=False, default=""
    )

    def __str__(self):
        return self.name


class Post(models.Model):
    title = models.CharField(
        max_length=300, blank=False, null=False, unique=False, default=""
    )
    description = models.CharField(
        max_length=300, blank=True, null=True, unique=False, default=""
    )
    platform = models.CharField(
        max_length=300, blank=False, null=False, unique=False, default=""
    )
    link = models.CharField(
        max_length=300, blank=False, null=False, unique=False, default=""
    )
    post_link = models.URLField(
        max_length=300, blank=False, null=False, unique=False, default=""
    )
    label = models.ManyToManyField(Label, blank=True, null=True)
    image = models.FileField(upload_to="posts", blank=True, null=True, unique=False)
    is_private = models.BooleanField(null=True, blank=True, default=False)
    created_time = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(
        User,
        related_name="own_posts",
        null=True,
        unique=False,
        on_delete=models.CASCADE,
    )
    space = models.ForeignKey(
        Space,
        related_name="space_posts",
        null=True,
        unique=False,
        on_delete=models.CASCADE,
    )
    liked_by = models.ManyToManyField(
        User, blank=True, null=True, related_name="liked_posts"
    )
    bookmarked_by = models.ManyToManyField(
        User, blank=True, null=True, related_name="vookmarked_posts"
    )

    def __str__(self):
        return self.title



class Comment(models.Model):

    post = models.ForeignKey(Post, related_name='post_review', null=True, blank=True, on_delete=models.CASCADE)
    user = models.ForeignKey(User, blank=False, null=True, on_delete=models.CASCADE, related_name="reviewer")
    comment = models.CharField( max_length=1000, blank=True, null=True)
    created_time = models.DateTimeField(auto_now_add=True)

class textAnnotation(models.Model):
    id=models.CharField(blank=False,null=False,unique=True, max_length=300,primary_key=True)
    source = models.ForeignKey(Post, related_name='post_annotation', null=False, blank=False, on_delete=models.CASCADE)
    type=models.TextField(blank=False,null=False)
    body_description=models.TextField(blank=False,null=False,unique=True)
    created_by = models.ForeignKey(User, blank=False, null=False, on_delete=models.CASCADE, related_name="created_by")
    created_time = models.DateTimeField(auto_now_add=True)
    selector_type=models.IntegerField(blank=False,null=False)
    start=models.IntegerField(blank=False,null=False)
    end=models.IntegerField(blank=False,null=False)

    def get_absolute_url(self):
        return reverse('annotation_detail', kwargs={'pk': self.pk})

    def __str__(self):
        return f"{self.type} annotation on {self.source.title}"

    


