from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import connection
from django.test import RequestFactory, TestCase
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from catalog.context_processors import _account_navigation_context
from catalog.models import Category, Organization, OrganizationGrant, OwnerTeamMembership, Place
from catalog.services.business_team import accessible_place_ids
from catalog.services.staff_roles import VOLUNTEER_GROUP
from catalog.views.common import _build_managed_places_summary


class AccountPlaceAccessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.actor = get_user_model().objects.create_user(username="account-member")
        cls.owner = get_user_model().objects.create_user(username="account-owner")
        cls.category, _ = Category.objects.get_or_create(code="EDU", defaults={"name": "Education"})
        cls.org = Organization.objects.create(owner=cls.owner, name_az="Network")
        cls.grant = OrganizationGrant.objects.create(
            organization=cls.org, member=cls.actor, owner=cls.owner,
            actions=["place.view", "place.reviews.reply"], scope="selected_places",
            base_ownership_version=cls.org.ownership_version,
        )

    def place(self, name, **fields):
        return Place.objects.create(name_az=name, category=self.category, **fields)

    def branch(self, name):
        place = self.place(name, owner=self.owner)
        Place.objects.filter(pk=place.pk).update(
            organization=self.org, organization_relationship_kind="business",
            organization_join_place_ownership_version=place.ownership_version,
            organization_join_org_ownership_version=self.org.ownership_version,
        )
        return place

    def test_summary_and_sidebar_queries_do_not_grow_with_view_only_branches(self):
        request = RequestFactory().get("/account/")
        request.user = self.actor
        sizes = (1, 8)
        counts = {}
        places = []
        for size in sizes:
            for index in range(len(places), size):
                place = self.branch(f"Branch {index}")
                places.append(place.pk)
                self.grant.selected_places.add(place)
            with CaptureQueriesContext(connection) as ids_queries:
                ids = accessible_place_ids(user=self.actor)
            self.assertCountEqual(ids, places)
            with CaptureQueriesContext(connection) as summary_queries:
                summary = _build_managed_places_summary(self.actor)
            self.assertEqual(summary["managed_places_count"], size)
            self.assertFalse(summary["can_edit_managed_places"])
            with CaptureQueriesContext(connection) as sidebar_queries:
                sidebar = _account_navigation_context(request)
            self.assertEqual(sidebar["managed_places_count"], size)
            counts[size] = (len(ids_queries), len(summary_queries), len(sidebar_queries))
        self.assertEqual(counts[1], counts[8], f"ACL, summary, sidebar queries by place count: {counts}")

    def test_scopes_permissions_and_revocations_are_read_fresh(self):
        direct = self.place("Direct", owner=self.actor)
        creator = self.place("Creator", created_by=self.actor)
        self.place("Transferred", created_by=self.actor, owner=self.owner)
        team = self.place("Team", owner=self.owner)
        membership = OwnerTeamMembership.objects.create(
            place=team, member=self.actor, owner=self.owner, role="EDITOR",
        )
        selected = self.branch("Selected")
        other = self.branch("Other")
        self.grant.selected_places.add(selected)

        def check(action, *places):
            self.assertCountEqual(accessible_place_ids(user=self.actor, action=action), [p.pk for p in places])

        check("place.view", direct, creator, team, selected)
        check("place.edit", direct, creator, team)
        check("place.team.manage", direct, creator)
        check("ownership.transfer", direct)
        check("place.reviews.reply", direct, creator, selected)
        check("place.reviews.report", direct, creator)
        check("place.reviews.moderate")
        check("place.publish")
        check("organization.edit")
        self.grant.selected_places.set([other])
        check("place.reviews.reply", direct, creator, other)
        OrganizationGrant.objects.filter(pk=self.grant.pk).update(scope="all_network")
        check("place.reviews.reply", direct, creator, selected, other)
        Place.objects.filter(pk=selected.pk).update(organization_relationship_kind="informational")
        check("place.reviews.reply", direct, creator, other)
        Place.objects.filter(pk=other.pk).update(ownership_version=2)
        check("place.reviews.reply", direct, creator)
        Place.objects.filter(pk=creator.pk).update(owner=self.owner)
        Place.objects.filter(pk=direct.pk).update(deleted_at=timezone.now())
        OwnerTeamMembership.objects.filter(pk=membership.pk).update(actions=["place.reviews.report"])
        check("place.view")
        check("place.reviews.report", team)
        OwnerTeamMembership.objects.filter(pk=membership.pk).update(base_ownership_version=2)
        check("place.reviews.report")
        OwnerTeamMembership.objects.filter(pk=membership.pk).update(base_ownership_version=None, actions=None)
        check("place.edit", team)
        self.actor.groups.add(Group.objects.get_or_create(name=VOLUNTEER_GROUP)[0])
        check("place.edit")
        self.actor.groups.clear()
        get_user_model().objects.filter(pk=self.actor.pk).update(is_active=False)
        check("place.edit")

    def test_network_ownership_grant_versions_and_platform_actions(self):
        branch = self.branch("Network branch")
        standalone = self.place("Standalone", owner=self.actor)
        self.grant.selected_places.add(branch)
        self.assertCountEqual(accessible_place_ids(user=self.actor), [branch.pk, standalone.pk])
        OrganizationGrant.objects.filter(pk=self.grant.pk).update(base_ownership_version=2)
        self.assertEqual(accessible_place_ids(user=self.actor), [standalone.pk])
        OrganizationGrant.objects.filter(pk=self.grant.pk).update(base_ownership_version=1, is_active=False)
        self.assertEqual(accessible_place_ids(user=self.actor), [standalone.pk])
        Place.objects.filter(pk=branch.pk).update(owner=None)
        self.assertEqual(accessible_place_ids(user=self.owner), [branch.pk])
        Organization.objects.filter(pk=self.org.pk).update(archived_at=timezone.now())
        self.assertEqual(accessible_place_ids(user=self.owner), [])
        get_user_model().objects.filter(pk=self.actor.pk).update(is_staff=True, is_superuser=True)
        for action in ("place.publish", "place.reviews.moderate"):
            self.assertEqual(accessible_place_ids(user=self.actor, action=action), [standalone.pk])

    def test_place_and_network_grants_combine_only_for_the_same_member(self):
        peer = get_user_model().objects.create_user(username="other-team-member")
        first = self.branch("First")
        second = self.branch("Second")
        self.grant.selected_places.add(first)
        peers_grant = OrganizationGrant.objects.create(
            organization=self.org, member=peer, owner=self.owner, scope="selected_places",
            actions=["place.view", "place.stats.view"], base_ownership_version=self.org.ownership_version,
        )
        peers_grant.selected_places.add(second)
        OwnerTeamMembership.objects.create(place=first, member=peer, owner=self.owner, role="MANAGER")
        OwnerTeamMembership.objects.create(
            place=first, member=self.actor, owner=self.owner, actions=["place.reviews.report"],
        )
        self.assertEqual(accessible_place_ids(user=self.actor), [first.pk])
        self.assertEqual(accessible_place_ids(user=self.actor, action="place.reviews.reply"), [first.pk])
        self.assertEqual(accessible_place_ids(user=self.actor, action="place.reviews.report"), [first.pk])
        self.assertEqual(accessible_place_ids(user=self.actor, action="place.stats.view"), [])
