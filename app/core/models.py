import os

from uuid import uuid4

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin, UserManager
from django.contrib.auth.validators import ASCIIUsernameValidator
from django.db import models
from django.utils import timezone

from sorl.thumbnail import ImageField


def user_images_file_path(instance, filename):
    ext = os.path.splitext(filename)[1]
    filename = f"{uuid4()}{ext}"

    return os.path.join("uploads", instance.user.username, filename)


def user_binary_images_file_path(instance, filename):
    ext = os.path.splitext(filename)[1]
    filename = f"{uuid4()}{ext}"

    return os.path.join("uploads", instance.user.username, "binary", filename)


class User(AbstractBaseUser, PermissionsMixin):
    username_validator = ASCIIUsernameValidator()

    username = models.CharField(
        max_length=150, unique=True, validators=[username_validator]
    )
    email = models.EmailField(unique=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    tier = models.ForeignKey(
        "Tier", on_delete=models.CASCADE, null=True, blank=True
    )

    objects = UserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)


class Thumbnail(models.Model):
    value = models.SmallIntegerField(unique=True)

    def __str__(self):
        return str(self.value)


class Tier(models.Model):
    name = models.CharField(max_length=150, unique=True)
    thumbnails = models.ManyToManyField(Thumbnail)
    can_create_link = models.BooleanField(default=False)

    def clean(self):
        super().clean()
        self.name = self.name.capitalize()

    def __str__(self):
        return self.name


class BinaryImageLink(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    binary_image = models.ImageField(upload_to=user_binary_images_file_path)
    exist_seconds = models.SmallIntegerField()
    date_created = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(User, on_delete=models.CASCADE)


class Image(models.Model):
    image = ImageField(upload_to=user_images_file_path)
    user = models.ForeignKey("User", on_delete=models.CASCADE)
