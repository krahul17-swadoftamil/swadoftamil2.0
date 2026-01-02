from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Inspect PreparedItem recipes by name'

    def add_arguments(self, parser):
        parser.add_argument('--name', required=True, help='PreparedItem name')

    def handle(self, *args, **options):
        name = options['name']
        from menu.models import PreparedItem

        try:
            pi = PreparedItem.objects.prefetch_related('recipes__ingredient').get(name=name)
        except PreparedItem.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"PreparedItem '{name}' not found"))
            return

        self.stdout.write(self.style.SUCCESS(f"PreparedItem: {pi.name} id={pi.id} unit={pi.unit} serving_size={getattr(pi, 'serving_size', None)} cost_price={getattr(pi, 'cost_price', None)}"))
        for r in pi.recipes.all():
            ing = r.ingredient
            self.stdout.write(f"RECIPE: id={r.id} ingredient={ing.name} qty={r.quantity} qty_unit={r.quantity_unit or '(base)'} ingredient.unit={ing.unit} ingredient.cost_per_unit={ing.cost_per_unit} ingredient.stock_qty={ing.stock_qty}")
