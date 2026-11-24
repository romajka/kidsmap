from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from catalog.interfaces.repositories import IAccountRepository, IUserProfileRepository
from catalog.repositories.django_repositories import DjangoAccountRepository, DjangoUserProfileRepository


@dataclass(slots=True)
class AccountController:
    account_repository: IAccountRepository
    profile_repository: IUserProfileRepository

    @classmethod
    def build_default(cls) -> "AccountController":
        return cls(
            account_repository=DjangoAccountRepository(),
            profile_repository=DjangoUserProfileRepository(),
        )

    def ensure_profile(self, *, user):
        return self.profile_repository.get_or_create_for_user(user)

    def build_favorites_context(self, *, user) -> dict:
        from catalog.models import PlaceSpecialistMove
        from catalog.services.public_presentation import prepare_cards

        saved = {}
        places = []
        for like in self.account_repository.list_user_favorite_likes(user=user):
            if not like.place_id or like.place_id in saved:
                continue
            saved[like.place_id] = like
            if like.place.is_active:
                like.place.is_liked = True
                places.append(like.place)

        favorite_places = prepare_cards(places)
        entries = {
            place.pk: {"place": place, "target": place, "name": place.name_i18n()}
            for place in favorite_places
        }
        hidden_place_ids = saved.keys() - entries.keys()
        if hidden_place_ids:
            moves = PlaceSpecialistMove.objects.public_targets().filter(
                place_id__in=hidden_place_ids
            ).select_related("specialist")
            for move in moves:
                entries[move.place_id] = {
                    "specialist": move.specialist,
                    "target": move.specialist,
                    "name": move.specialist.name,
                    "like_id": saved[move.place_id].pk,
                }

        return {
            "favorite_places": favorite_places,
            "favorite_entries": [entries[pk] for pk in saved if pk in entries],
            "has_moved_favorites": len(entries) > len(favorite_places),
            "favorites_count": len(entries),
        }

    def build_history_context(self, *, user, limit: int = 12) -> dict:
        events = list(self.account_repository.list_recent_place_open_events(user=user, limit=max(limit * 5, 30)))
        history_events: list[dict] = []
        seen_place_ids: set[int] = set()
        category_counter: Counter[str] = Counter()
        from catalog.models import Category
        category_labels = {c.code: c.name_i18n() for c in Category.objects.all()}

        for event in events:
            if event.place_id is None or event.place is None or event.place_id in seen_place_ids:
                continue
            seen_place_ids.add(event.place_id)
            category_counter[event.place.category] += 1
            history_events.append(
                {
                    "place": event.place,
                    "opened_at": event.created_at,
                }
            )
            if len(history_events) >= limit:
                break

        top_categories = [
            {
                "code": code,
                "label": category_labels.get(code, code),
                "hits": hits,
            }
            for code, hits in category_counter.most_common(3)
        ]

        return {
            "history_events": history_events,
            "history_count": len(history_events),
            "top_interest_categories": top_categories,
        }

    def build_user_reviews_context(self, *, user) -> dict:
        from catalog.services.account_review_feeds import review_page, written_queries

        page = review_page(written_queries(user), page_size=10)
        return {"user_reviews": page.object_list, "user_reviews_count": page.paginator.count}

    def build_dashboard_context(self, *, user) -> dict:
        profile = self.ensure_profile(user=user)
        favorites_context = self.build_favorites_context(user=user)
        history_context = self.build_history_context(user=user, limit=8)
        reviews_context = self.build_user_reviews_context(user=user)

        return {
            "profile_model": profile,
            **favorites_context,
            **history_context,
            **reviews_context,
        }

