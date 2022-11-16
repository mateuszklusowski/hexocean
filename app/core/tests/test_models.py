import os
import tempfile
import shutil

from PIL import Image as pillow_image

from unittest.mock import patch

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.files.uploadedfile import InMemoryUploadedFile

from core import models


def sample_user(**params):
    return get_user_model().objects.create_user(**params)


def sample_thumbnail(**params):
    return models.Thumbnail.objects.create(**params)


def sample_tier(**params):
    return models.Tier.objects.create(**params)


def sample_binary_image_link(**params):
    return models.BinaryImageLink.objects.create(**params)


def sample_image(**params):
    return models.Image.objects.create(**params)


class ModelTests(TestCase):
    def tearDown(self):
        path = "/vol/web/media/uploads/user"
        if os.path.exists(path):
            shutil.rmtree(path)

    def test_create_user_model(self):
        params = {
            "email": "testuser@email.com",
            "username": "user",
            "password": "testpassword",
        }
        user = sample_user(**params)

        for key in params.keys():
            if key == "password":
                self.assertTrue(user.check_password(params[key]))
                continue
            self.assertEqual(getattr(user, key), params[key])

    def test_normalize_email(self):
        params = {
            "email": "testuser@EMAIL.com",
            "username": "user",
            "password": "testpassword",
        }
        user = sample_user(**params)

        self.assertEqual(user.email, params["email"].lower())

    def test_create_user_without_username(self):
        with self.assertRaises(ValueError):
            params = {
                "email": "testuser@email.com",
                "username": None,
                "password": "testpassword",
            }

            sample_user(**params)

    def test_thumbnail_model(self):
        params = {"value": 400}
        thumbnail = sample_thumbnail(**params)

        self.assertEqual(thumbnail.value, params["value"])

    def test_tier_model(self):
        params = {
            "name": "testtier",
        }
        tier = sample_tier(**params)
        thumbnails = (sample_thumbnail(value=i) for i in range(2))
        tier.thumbnails.set(thumbnails)

        for key in params.keys():
            self.assertEqual(getattr(tier, key), params[key])

        for thumbnail in thumbnails:
            self.assertIn(thumbnail, tier.thumbnails.all())

        self.assertFalse(tier.can_create_link)

    @patch("core.models.uuid4")
    def test_user_binary_images_file_path(self, mock_uuid):
        user = sample_user(username="user", password="testpassword")
        binary = sample_binary_image_link(user=user, exist_seconds=300)

        uuid = "testing-uuid"
        mock_uuid.return_value = uuid
        file_path = models.user_binary_images_file_path(binary, "test.jpg")

        self.assertEqual(
            file_path, f"uploads/{binary.user.username}/binary/{uuid}.jpg"
        )

    def test_bianry_image_link_model(self):
        user = sample_user(username="user", password="testpassword")
        with tempfile.NamedTemporaryFile(suffix=".png") as image_file:
            img = pillow_image.new("RGB", (1, 1))
            img.save(image_file, "png")
            image_file.seek(0)

            image = InMemoryUploadedFile(
                image_file,
                "image",
                "image.png",
                "png",
                image_file.tell(),
                None,
            )

            binary = sample_binary_image_link(
                user=user, exist_seconds=300, binary_image=image
            )

        self.assertTrue(binary.binary_image)
        self.assertTrue(os.path.exists(binary.binary_image.path))
        self.assertEqual(binary.user, user)
        self.assertEqual(binary.date_created.day, timezone.now().day)
        self.assertEqual(binary.date_created.minute, timezone.now().minute)

    @patch("core.models.uuid4")
    def test_user_images_file_path(self, mock_uuid):
        user = sample_user(username="user", password="testpassword")
        image = sample_image(user=user)
        uuid = "testing-uuid"
        mock_uuid.return_value = uuid
        file_path = models.user_images_file_path(image, "test.jpg")

        self.assertEqual(
            file_path, f"uploads/{image.user.username}/{uuid}.jpg"
        )

    def test_image_model(self):
        user = sample_user(username="user", password="testpassword")
        with tempfile.NamedTemporaryFile(suffix=".png") as image_file:
            img = pillow_image.new("RGB", (1, 1))
            img.save(image_file, "png")
            image_file.seek(0)

            img = InMemoryUploadedFile(
                image_file,
                "image",
                "image.png",
                "png",
                image_file.tell(),
                None,
            )
            image = models.Image.objects.create(user=user, image=img)

        self.assertTrue(image.image)
        self.assertTrue(os.path.exists(image.image.path))
        self.assertTrue(image.user, user)
