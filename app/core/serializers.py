from rest_framework import serializers

from django.utils.translation import gettext_lazy as _
from django.urls import reverse

import core.models

from sorl.thumbnail import get_thumbnail


def image_ext_validator(image):
    ext = ("jpg", "png", "jpeg", "JPG", "PNG", "JPEG")
    image_ext = image.name.split(".")[-1]

    if image_ext not in ext:
        msg = _(f"{image_ext} extension is not supported.")
        raise serializers.ValidationError(msg)


class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        fields = kwargs.pop("fields", None)
        super().__init__(*args, **kwargs)

        if fields is not None:
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class ImagesSerializer(DynamicFieldsModelSerializer):
    thumbnails = serializers.SerializerMethodField()
    binary_image_link = serializers.SerializerMethodField()
    image = serializers.ImageField(
        validators=(image_ext_validator,), required=True
    )

    class Meta:
        model = core.models.Image
        exclude = ("user", "id")

    def get_thumbnails(self, obj):
        request = self.context.get("request")
        thumbnailed_photos = []

        for thumbnail in obj.user.tier.thumbnails.all():
            height = f"x{thumbnail.value}"
            url = request.build_absolute_uri(
                get_thumbnail(obj.image, height, crop="center", quality=99).url
            )
            thumbnailed_photos.append({thumbnail.value: url})

        return thumbnailed_photos

    def get_binary_image_link(self, obj):
        request = self.context.get("request")
        url = reverse("core:create-link", args=[obj.id])

        return request.build_absolute_uri(url)

    def validate(self, data):
        data.update({"user": self.context.get("view").get_object()})

        return data


class ExistSecondsSerializer(serializers.Serializer):
    exist_seconds = serializers.IntegerField(min_value=300, max_value=30000)
