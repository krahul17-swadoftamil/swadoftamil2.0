from io import BytesIO

from django.test import override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase, APIClient

from menu.models import PreparedItem, Combo, ComboItem

try:
    from PIL import Image
except Exception:
    Image = None


@override_settings(MEDIA_ROOT="/tmp/django_test_media")
class ComboDisplayFieldsTest(APITestCase):
    def setUp(self):
        # Create an in-memory image if PIL is available; otherwise leave image empty.
        upload = None
        if Image:
            img = Image.new("RGB", (800, 800), color=(255, 255, 255))
            buf = BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            upload = SimpleUploadedFile("test.png", buf.read(), content_type="image/png")

        self.pi = PreparedItem.objects.create(
            name="Test Sambar",
            unit="ml",
            serving_size=100,
            main_image=upload,
        )

        self.combo = Combo.objects.create(name="Test Combo", selling_price=100, serve_person=1)
        ComboItem.objects.create(combo=self.combo, prepared_item=self.pi, quantity=1)

    def test_combo_item_display_fields(self):
        client = APIClient()
        resp = client.get("/api/combos/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(len(data) > 0)
        items = data[0].get("items", [])
        self.assertTrue(len(items) > 0)
        it = items[0]

        # Assert serializer returns display_quantity, unit, and image key
        self.assertIn("display_quantity", it)
        self.assertIn("unit", it)
        self.assertIn("image", it)

        # display_quantity should be non-null and numeric > 0 when serving_size and quantity exist
        self.assertIsNotNone(it["display_quantity"])
        try:
            self.assertGreater(float(it["display_quantity"]), 0.0)
        except Exception:
            self.fail("display_quantity is not a numeric string")

        # unit must be present and match expected choices
        self.assertIn(it["unit"], ["pcs", "ml", "gm"])

        # image can be None when PIL not available; if present, should be a string
        if it["image"] is not None:
            self.assertIsInstance(it["image"], str)
