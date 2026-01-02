from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from menu.models import PreparedItem
from django.core.files.uploadedfile import SimpleUploadedFile


class PreparedItemImageTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.pi = PreparedItem.objects.create(name="Test Item", unit="pcs", serving_size=Decimal("1.000"))

    def test_image_field_exists_and_can_store(self):
        # upload a tiny in-memory file
        img = SimpleUploadedFile("test.png", b"PNGDATA", content_type="image/png")
        self.pi.image = img
        self.pi.save()

        pi = PreparedItem.objects.get(pk=self.pi.pk)
        self.assertTrue(pi.image)

    def test_admin_change_form_shows_file_input(self):
        # login superuser
        from django.contrib.auth import get_user_model
        User = get_user_model()
        admin = User.objects.create_superuser("admin", "a@a.com", "pass")
        self.client.force_login(admin)
        url = reverse("admin:menu_prepareditem_change", args=[self.pi.pk])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        # should contain file input for image upload
        self.assertIn("type=\"file\"", resp.content.decode())
