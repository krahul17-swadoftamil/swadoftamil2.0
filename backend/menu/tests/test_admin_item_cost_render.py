from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

from menu.models import Combo, PreparedItem, ComboItem

ZERO = Decimal("0.00")


class AdminInlineRenderTests(TestCase):
    def setUp(self):
        User = get_user_model()
        username_field = getattr(User, 'USERNAME_FIELD', 'username')
        creds = {username_field: 'admin', 'email': 'admin@example.com', 'password': 'pass'}
        # create_superuser may require username or different signature across projects
        try:
            self.admin = User.objects.create_superuser(**creds)
        except TypeError:
            # fallback: try positional args
            self.admin = User.objects.create_superuser('admin', 'admin@example.com', 'pass')

        self.client = Client()
        self.client.force_login(self.admin)

    def test_combo_change_page_renders_with_zero_serving_size(self):
        # PreparedItem with serving_size 0 (edge case)
        pi = PreparedItem.objects.create(name='Test Item Zero', unit='ml', serving_size=Decimal('0'))

        combo = Combo.objects.create(name='Test Combo', selling_price=Decimal('100.00'))
        ComboItem.objects.create(combo=combo, prepared_item=pi, quantity=1, item_type='combo')

        url = f"/admin/menu/combo/{combo.pk}/change/"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        # ensure page contains combo name
        self.assertIn(combo.name, resp.content.decode())

    def test_combo_change_page_renders_with_no_recipes(self):
        # PreparedItem with no recipes -> cost_price == 0
        pi = PreparedItem.objects.create(name='No Recipe Item', unit='pcs', serving_size=Decimal('1'))
        combo = Combo.objects.create(name='Test Combo 2', selling_price=Decimal('50.00'))
        ComboItem.objects.create(combo=combo, prepared_item=pi, quantity=2, item_type='combo')

        url = f"/admin/menu/combo/{combo.pk}/change/"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(combo.name, resp.content.decode())
