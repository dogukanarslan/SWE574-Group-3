from rest_framework.permissions import BasePermission
from rest_framework.exceptions import ValidationError
from rest_framework import exceptions
from django.utils.translation import gettext_lazy as _
from feed.models import Space

"""
There are 3 different user groups: 
1. Space Owner:
- Can assign moderator to his/her space
- Can delete posts of the space
- Can approve or reject the request of user to join space

2. Space Moderator:
- Can delete posts of the space
- Can approve or reject the request of user to join space
"""


class IsSpaceOwnerPermission(BasePermission):

    """
    Only for the operations that "Space Owner" can, i.e., for assigning moderator to his/her space.
    """

    def has_permission(self, request, view):
        if Space.objects.get(id=int(request.parser_context['kwargs'].get('pk'))).owner.id == request.user.id:
            return True
        return False

class IsModeratorPermission(BasePermission):

    """
    Only for the operations that "Moderator" can, i.e., for deleting posts.
    """

    def has_permission(self, request, view):
        if Space.objects.get(id=int(request.parser_context['kwargs'].get('pk'))).moderator.id == request.user.id:
            return True
        return False