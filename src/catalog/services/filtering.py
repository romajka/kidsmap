from dataclasses import dataclass
from datetime import timedelta

from django.db.models import Q
from django.utils import timezone


@dataclass
class PlaceListFilters:
    category: str = ""
    query: str = ""
    district: str = ""
    metro: str = ""
    age: str = ""
    age_from: str = ""
    age_to: str = ""
    price_from: str = ""
    price_to: str = ""
    price_max: str = ""
    min_rating: str = ""
    sort: str = "new"
    days: str = "30"
    with_photo: str = ""
    verified_only: str = ""
    view_mode: str = "grid"
    force_new_only: bool = False

    @classmethod
    def from_request(cls, request, force_new_only=False):
        data = cls(
            category=(request.GET.get("category") or "").strip(),
            query=(request.GET.get("q") or "").strip(),
            district=(request.GET.get("district") or "").strip(),
            metro=(request.GET.get("metro") or "").strip(),
            age=(request.GET.get("age") or "").strip(),
            age_from=(request.GET.get("age_from") or "").strip(),
            age_to=(request.GET.get("age_to") or "").strip(),
            price_from=(request.GET.get("price_from") or "").strip(),
            price_to=(request.GET.get("price_to") or "").strip(),
            price_max=(request.GET.get("price_max") or "").strip(),
            min_rating=(request.GET.get("min_rating") or "").strip(),
            sort=(request.GET.get("sort") or "new").strip(),
            days=(request.GET.get("days") or "30").strip(),
            with_photo=(request.GET.get("with_photo") or "").strip(),
            verified_only=(request.GET.get("verified") or "").strip(),
            view_mode=(request.GET.get("view") or "grid").strip(),
            force_new_only=force_new_only,
        )
        if data.view_mode not in {"grid", "list"}:
            data.view_mode = "grid"
        if data.force_new_only:
            data.sort = "new"
            if data.days not in {"7", "14", "30"}:
                data.days = "30"
        return data

    def _int_or_none(self, value):
        return int(value) if str(value).isdigit() else None

    def _normalized_age_bounds(self):
        age_from = self.age_from
        age_to = self.age_to

        if not age_from and not age_to and self.age.isdigit():
            age_from = self.age
            age_to = self.age

        age_from_int = self._int_or_none(age_from)
        age_to_int = self._int_or_none(age_to)

        if age_from_int is not None and age_to_int is not None and age_from_int > age_to_int:
            age_from_int, age_to_int = age_to_int, age_from_int

        return age_from_int, age_to_int

    def _normalized_price_bounds(self):
        price_from_int = self._int_or_none(self.price_from)
        price_to_int = self._int_or_none(self.price_to)

        if price_to_int is None:
            price_to_int = self._int_or_none(self.price_max)

        if price_from_int is not None and price_to_int is not None and price_from_int > price_to_int:
            price_from_int, price_to_int = price_to_int, price_from_int

        return price_from_int, price_to_int

    def apply(self, qs, created_after=None):
        if self.force_new_only:
            recent_cutoff = timezone.now() - timedelta(days=int(self.days))
            qs = qs.filter(created_at__gte=recent_cutoff)
        elif created_after is not None:
            qs = qs.filter(created_at__gte=created_after)

        if self.category:
            qs = qs.filter(category=self.category)

        if self.query:
            qs = qs.filter(
                Q(name_ru__icontains=self.query)
                | Q(name_en__icontains=self.query)
                | Q(name_az__icontains=self.query)
                | Q(name__icontains=self.query)
                | Q(description_ru__icontains=self.query)
                | Q(description_en__icontains=self.query)
                | Q(description_az__icontains=self.query)
                | Q(subcategory__icontains=self.query)
                | Q(address__icontains=self.query)
            )

        if self.district:
            qs = qs.filter(district__iexact=self.district)

        if self.min_rating:
            try:
                min_rating_value = float(self.min_rating.replace(",", "."))
            except ValueError:
                min_rating_value = None
            if min_rating_value is not None:
                min_rating_value = max(0, min(5, min_rating_value))
                qs = qs.filter(rating_avg__gte=min_rating_value)

        if self.force_new_only:
            if self.with_photo == "1":
                qs = qs.exclude(
                    (Q(cover_photo="") | Q(cover_photo__isnull=True))
                    & (Q(photo="") | Q(photo__isnull=True))
                )
            if self.verified_only == "1":
                qs = qs.filter(is_verified=True)

        if self.metro:
            qs = qs.filter(metro__iexact=self.metro)

        age_from_int, age_to_int = self._normalized_age_bounds()
        if age_from_int is not None:
            qs = qs.filter(Q(age_to__isnull=True) | Q(age_to__gte=age_from_int))
        if age_to_int is not None:
            qs = qs.filter(Q(age_from__isnull=True) | Q(age_from__lte=age_to_int))

        price_from_int, price_to_int = self._normalized_price_bounds()
        if price_from_int is not None:
            qs = qs.filter(Q(price_to__isnull=True) | Q(price_to__gte=price_from_int))
        if price_to_int is not None:
            qs = qs.filter(Q(price_from__isnull=True) | Q(price_from__lte=price_to_int))

        if self.sort == "price_asc" and not self.force_new_only:
            return qs.order_by("price_from", "-created_at")
        if self.sort == "price_desc" and not self.force_new_only:
            return qs.order_by("-price_from", "-created_at")
        if self.sort == "reviews_desc" and not self.force_new_only:
            return qs.order_by("-rating_count", "-rating_avg", "-created_at")
        self.sort = "new"
        return qs.order_by("-created_at")

    def selected(self):
        age_from_int, age_to_int = self._normalized_age_bounds()
        price_from_int, price_to_int = self._normalized_price_bounds()
        return {
            "category": self.category,
            "q": self.query,
            "district": self.district,
            "metro": self.metro,
            "age": self.age,
            "age_from": str(age_from_int if age_from_int is not None else self.age_from),
            "age_to": str(age_to_int if age_to_int is not None else self.age_to),
            "price_from": str(price_from_int if price_from_int is not None else self.price_from),
            "price_to": str(price_to_int if price_to_int is not None else self.price_to),
            "min_rating": self.min_rating,
            "sort": self.sort,
            "days": self.days,
            "with_photo": self.with_photo,
            "verified": self.verified_only,
            "view": self.view_mode,
        }


def build_new_page_stats(qs):
    return {
        "places": qs.count(),
        "districts": qs.exclude(district="").exclude(district__isnull=True).values("district").distinct().count(),
        "categories": qs.values("category").distinct().count(),
    }
