from io import BytesIO
from datetime import timedelta

from PIL import Image as pillow_image

from rest_framework import viewsets, status, mixins, generics, views
from rest_framework.decorators import action
from rest_framework.response import Response

from django.urls import reverse
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .models import Image, BinaryImageLink
from .serializers import ImagesSerializer, ExistSecondsSerializer
from .permissions import DoesUserHaveTier, IsAuthenticated, CanUserCreateLink


class ImageListViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = (IsAuthenticated, DoesUserHaveTier)
    serializer_class = ImagesSerializer

    def get_queryset(self):
        queryset = Image.objects.select_related("user").filter(
            user=self.get_object()
        ).order_by('id')
        return queryset

    def get_object(self):
        return self.request.user

    @action(detail=False, methods=["post"], name="image-upload")
    def image_upload(self, request):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            serializer.save()
            msg = {'image': _('Successfuly created.')}
            return Response(msg, status=status.HTTP_201_CREATED)

    def list(self, request):
        queryset = self.paginate_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)

        if self.get_object().tier.name == "Basic":
            serializer = self.get_serializer(
                queryset, fields=("thumbnails",), many=True
            )

        if self.get_object().tier.name == "Premium":
            serializer = self.get_serializer(
                queryset, fields=("image", "thumbnails"), many=True
            )
        return self.get_paginated_response(serializer.data)


class CreateBinaryLinkView(generics.CreateAPIView):
    permission_classes = (IsAuthenticated, DoesUserHaveTier, CanUserCreateLink)
    serializer_class = ExistSecondsSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            image = Image.objects.get(pk=kwargs["image_pk"]).image

            with pillow_image.open(image) as binary_img:
                io_img = BytesIO()

                binary_img = binary_img.convert("L")
                binary_img.save(io_img, "png", quality="kepp")
                binary_img = InMemoryUploadedFile(
                    io_img, "image", "image.png", "PNG", io_img.tell(), None
                )

                binary_link = BinaryImageLink.objects.create(
                    binary_image=binary_img,
                    exist_seconds=serializer.data["exist_seconds"],
                    user=self.request.user,
                )
                binary_link.save()

            pattern = reverse("core:get-binary-link", args=[binary_link.id])
            url = self.request.build_absolute_uri(pattern)

        return Response({"link": url}, status=status.HTTP_201_CREATED)


class RetrieveBinaryLinkView(views.APIView):
    def get(self, request, **kwargs):

        try:
            binary_link = BinaryImageLink.objects.get(id=kwargs["binary_pk"])
        except BinaryImageLink.DoesNotExist:
            msg = _("Link expired")
            return Response({"image": msg}, status=status.HTTP_400_BAD_REQUEST)

        time_created = binary_link.date_created
        exist_seconds = timedelta(seconds=binary_link.exist_seconds)
        final_time = time_created + exist_seconds

        if final_time < timezone.now():
            binary_link.delete()
            msg = _("Link expired")
            return Response({"image": msg}, status=status.HTTP_400_BAD_REQUEST)

        url = self.request.build_absolute_uri(binary_link.binary_image.url)

        return Response({"image": url}, status=status.HTTP_200_OK)
