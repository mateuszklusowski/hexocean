import os
import shutil
import tempfile
from datetime import timedelta

from PIL import Image as pillow_image

from rest_framework import status
from rest_framework.test import APITestCase

from django.urls import reverse
from django.test import override_settings
from django.core.files.uploadedfile import InMemoryUploadedFile

from core.models import Image, BinaryImageLink
from .test_models import sample_user, sample_tier, sample_thumbnail

IMAGES_LIST_URL = reverse("core:images-list")
IMAGE_UPLOAD_URL = reverse("core:images-image-upload")


def create_binary_link_url(image_pk):
    return reverse("core:create-link", args=[image_pk])


def get_binary_link_url(binary_image_pk):
    return reverse("core:get-binary-link", args=[binary_image_pk])


@override_settings(
    CACHES={
        "default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}
    }
)
class ImagesAPITests(APITestCase):
    def setUp(self):
        thumbnail1 = sample_thumbnail(value=100)
        thumbnail1.save()
        thumbnail2 = sample_thumbnail(value=300)
        thumbnail2.save()

        self.basic_tier = sample_tier(name="Basic")
        self.basic_tier.save()
        self.basic_tier.thumbnails.add(thumbnail1)

        self.premium_tier = sample_tier(name="Premium")
        self.premium_tier.save()
        self.premium_tier.thumbnails.set((thumbnail1, thumbnail2))

        self.enterprise_tier = sample_tier(
            name="Enterprise", can_create_link=True
        )
        self.enterprise_tier.save()
        self.enterprise_tier.thumbnails.set((thumbnail1, thumbnail2))

        self.user = sample_user(
            email="testuser@email.com",
            username="user",
            password="testpassword",
        )

    def tearDown(self):
        paths = ("/vol/web/media/uploads/user", "/vol/web/media/cache")
        for path in paths:
            if os.path.exists(path):
                shutil.rmtree(path)

    def test_retrieve_images_list_unauthorized(self):
        res = self.client.get(IMAGES_LIST_URL)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_images_list_without_tier(self):
        self.client.force_authenticate(user=self.user)

        res = self.client.get(IMAGES_LIST_URL)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_images_list(self):
        self.user.tier = self.basic_tier
        self.user.save()
        self.client.force_authenticate(user=self.user)

        res = self.client.get(IMAGES_LIST_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_upload_image_unauthorized(self):
        with tempfile.NamedTemporaryFile(suffix=".png") as image_file:
            img = pillow_image.new("RGB", (200, 200))
            img.save(image_file, "png")
            image_file.seek(0)
            payload = {"image": image_file}
            res = self.client.post(
                IMAGE_UPLOAD_URL, payload, format="multipart"
            )

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.user.image_set.count(), 0)

    def test_upload_image_without_tier(self):
        self.client.force_authenticate(user=self.user)

        with tempfile.NamedTemporaryFile(suffix=".png") as image_file:
            img = pillow_image.new("RGB", (200, 200))
            img.save(image_file, "png")
            image_file.seek(0)
            payload = {"image": image_file}
            res = self.client.post(
                IMAGE_UPLOAD_URL, payload, format="multipart"
            )

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.user.image_set.count(), 0)

    def test_upload_image_with_basic_tier(self):
        self.user.tier = self.basic_tier
        self.user.save()
        self.client.force_authenticate(user=self.user)

        with tempfile.NamedTemporaryFile(suffix=".png") as image_file:
            img = pillow_image.new("RGB", (200, 200))
            img.save(image_file, "png")
            image_file.seek(0)
            payload = {"image": image_file}
            res = self.client.post(
                IMAGE_UPLOAD_URL, payload, format="multipart"
            )

        self.assertEqual(res.status_code, status.HTTP_302_FOUND)
        self.assertEqual(self.user.image_set.count(), 1)

        res = self.client.get(IMAGES_LIST_URL)
        self.assertIn("thumbnails", res.data[0])

        thumbnail_values = {}
        for data in res.data[0]["thumbnails"]:
            thumbnail_values.update(data)

        for thumbnail in self.user.tier.thumbnails.all():
            self.assertIn(thumbnail.value, thumbnail_values)

        self.assertNotIn("binary_image_link", res.data[0])
        self.assertNotIn("image", res.data[0])

    def test_upload_image_with_premium_tier(self):
        self.user.tier = self.premium_tier
        self.user.save()
        self.client.force_authenticate(user=self.user)

        with tempfile.NamedTemporaryFile(suffix=".png") as image_file:
            img = pillow_image.new("RGB", (200, 200))
            img.save(image_file, "png")
            image_file.seek(0)
            payload = {"image": image_file}
            res = self.client.post(
                IMAGE_UPLOAD_URL, payload, format="multipart"
            )

        self.assertEqual(res.status_code, status.HTTP_302_FOUND)
        self.assertEqual(self.user.image_set.count(), 1)

        res = self.client.get(IMAGES_LIST_URL)
        self.assertIn("thumbnails", res.data[0])

        thumbnail_values = {}
        for data in res.data[0]["thumbnails"]:
            thumbnail_values.update(data)

        for thumbnail in self.user.tier.thumbnails.all():
            self.assertIn(thumbnail.value, thumbnail_values)

        self.assertIn("image", res.data[0])
        self.assertNotIn("binary_image_link", res.data[0])

    def test_upload_image_with_enterprise_tier(self):
        self.user.tier = self.enterprise_tier
        self.user.save()
        self.client.force_authenticate(user=self.user)

        with tempfile.NamedTemporaryFile(suffix=".png") as image_file:
            img = pillow_image.new("RGB", (200, 200))
            img.save(image_file, "png")
            image_file.seek(0)
            payload = {"image": image_file}
            res = self.client.post(
                IMAGE_UPLOAD_URL, payload, format="multipart"
            )

        self.assertEqual(res.status_code, status.HTTP_302_FOUND)
        self.assertEqual(self.user.image_set.count(), 1)

        res = self.client.get(IMAGES_LIST_URL)
        self.assertIn("thumbnails", res.data[0])

        thumbnail_values = {}
        for data in res.data[0]["thumbnails"]:
            thumbnail_values.update(data)

        for thumbnail in self.user.tier.thumbnails.all():
            self.assertIn(thumbnail.value, thumbnail_values)

        self.assertIn("image", res.data[0])
        self.assertIn("binary_image_link", res.data[0])

    def test_create_binary_link_unauthorized(self):
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

            image = Image.objects.create(user=self.user, image=img)

        url = create_binary_link_url(image.pk)
        payload = {"exist_seconds": 300}

        res = self.client.post(url, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.user.binaryimagelink_set.count(), 0)

    def test_create_binary_link_without_tier(self):
        self.client.force_authenticate(user=self.user)

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

            image = Image.objects.create(user=self.user, image=img)

        url = create_binary_link_url(image.pk)
        payload = {"exist_seconds": 300}

        res = self.client.post(url, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.user.binaryimagelink_set.count(), 0)

    def test_create_binary_link_without_right_tier(self):
        self.user.tier = self.premium_tier
        self.user.save()
        self.client.force_authenticate(user=self.user)

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

            image = Image.objects.create(user=self.user, image=img)

        url = create_binary_link_url(image.pk)
        payload = {"exist_seconds": 300}

        res = self.client.post(url, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.user.binaryimagelink_set.count(), 0)

    def test_create_binary_link(self):
        self.user.tier = self.enterprise_tier
        self.user.save()
        self.client.force_authenticate(user=self.user)

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

            image = Image.objects.create(user=self.user, image=img)

        url = create_binary_link_url(image.pk)
        payload = {"exist_seconds": 300}

        res = self.client.post(url, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.user.binaryimagelink_set.count(), 1)

    def test_create_binary_link_with_lower_than_300_sec(self):
        self.user.tier = self.enterprise_tier
        self.user.save()
        self.client.force_authenticate(user=self.user)

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

            image = Image.objects.create(user=self.user, image=img)

        url = create_binary_link_url(image.pk)
        payload = {"exist_seconds": 299}

        res = self.client.post(url, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.user.binaryimagelink_set.count(), 0)

    def test_create_binary_link_with_greater_than_30000_sec(self):
        self.user.tier = self.enterprise_tier
        self.user.save()
        self.client.force_authenticate(user=self.user)

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

            image = Image.objects.create(user=self.user, image=img)

        url = create_binary_link_url(image.pk)
        payload = {"exist_seconds": 30001}

        res = self.client.post(url, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.user.binaryimagelink_set.count(), 0)

    def test_get_binary_link(self):
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

            binary = BinaryImageLink.objects.create(
                user=self.user, exist_seconds=300, binary_image=image
            )

        url = get_binary_link_url(binary.id)

        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_get_binary_link_expired(self):
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

            binary = BinaryImageLink.objects.create(
                user=self.user, exist_seconds=300, binary_image=image
            )

        time_created = binary.date_created
        exist_seconds = timedelta(seconds=binary.exist_seconds)
        final_time = time_created - exist_seconds
        binary.date_created = final_time
        binary.save()

        url = get_binary_link_url(binary.id)

        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
