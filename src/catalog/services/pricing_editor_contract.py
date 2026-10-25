"""Presentation choices for both editors; validation remains in PricingPlan."""
from catalog.models import Place, PricingPlan
from catalog.services.pricing_plans import MAX_PRICING_PLANS


def build_pricing_editor_contract():
    def choices(values):
        return [[code, str(label)] for code, label in values]
    return {
        'max_plans': MAX_PRICING_PLANS,
        'max_lengths': {field.name:field.max_length for field in PricingPlan._meta.fields if field.max_length},
        'product_types': choices(PricingPlan.PRODUCT_CHOICES),
        'price_kinds': choices(PricingPlan.PRICE_KIND_CHOICES),
        'billing_modes': choices(PricingPlan.BILLING_MODE_CHOICES),
        'intervals': choices(PricingPlan.INTERVAL_CHOICES),
        'quantity_units': choices(PricingPlan.QUANTITY_UNIT_CHOICES),
        'audiences': choices(PricingPlan.AUDIENCE_CHOICES),
        'day_types': choices(PricingPlan.DAY_TYPE_CHOICES),
        'lesson_formats': choices(PricingPlan.LESSON_FORMAT_CHOICES),
        'price_modes': choices(Place.PRICE_MODE_CHOICES),
    }
