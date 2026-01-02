from django.core.management.base import BaseCommand
from PIL import Image
from io import BytesIO


class Command(BaseCommand):
    help = 'Report image dimensions and HQ compliance for menu-related images'

    def handle(self, *args, **options):
        from menu.models import (
            Combo,
            ComboImage,
            ComboItem,
            PreparedItemImage,
        )

        checks = [
            (Combo, 'main_image', 800, 800),
            (ComboImage, 'image', 800, 800),
            (ComboItem, 'image', 600, 600),
            (PreparedItemImage, 'image', 600, 600),
        ]

        total = 0
        failed = 0

        for model, fieldname, minw, minh in checks:
            qs = model.objects.all()
            for obj in qs:
                field = getattr(obj, fieldname, None)
                if not field:
                    continue
                total += 1
                try:
                    f = field.file
                    img = Image.open(f)
                    w, h = img.size
                    ok = (w >= minw and h >= minh)
                    status = 'OK' if ok else 'TOO_SMALL'
                    if not ok:
                        failed += 1
                    self.stdout.write(f"{model.__name__}({obj.pk}) {fieldname}: {w}x{h} -> {status}")
                except Exception as e:
                    failed += 1
                    self.stdout.write(f"{model.__name__}({obj.pk}) {fieldname}: ERROR {e}")

        self.stdout.write(self.style.SUCCESS(f"Checked {total} images, {failed} failing."))
