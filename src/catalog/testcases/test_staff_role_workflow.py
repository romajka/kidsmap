from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import skipUnless
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core import mail
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, connections
from django.test import TestCase, TransactionTestCase
from django.urls import reverse

from catalog.models import Place, UserProfile


User = get_user_model()


class StaffRoleWorkflowTests(TestCase):
    def setUp(self):
        self.initiator = User.objects.create_superuser(
            username="role-initiator",
            email="initiator@example.test",
            password="password",
        )
        self.approver = User.objects.create_superuser(
            username="role-approver",
            email="approver@example.test",
            password="password",
        )
        self.target = User.objects.create_user(
            username="role-target",
            email="target@example.test",
            password="password",
            is_staff=True,
        )
        UserProfile.get_or_create_for_user(self.target)
        self.place = Place.objects.create(
            name="Role owner place",
            name_az="Role owner place",
            category="EDU",
            created_by=self.target,
            status=Place.STATUS_DRAFT,
            is_active=False,
        )

    def _set_permissions(self, user, codenames):
        user.user_permissions.set(Permission.objects.filter(
            content_type__app_label="catalog",
            codename__in=codenames,
        ))

    def test_assign_staff_role_replaces_the_previous_role_atomically(self):
        from catalog.services.staff_role_workflow import assign_staff_role
        from catalog.services.staff_roles import (
            ADMIN_ROLE_CONTENT_MANAGER,
            ADMIN_ROLE_MODERATOR,
            ADMIN_ROLE_VOLUNTEER,
            ADMIN_ROLE_PERMISSION_PRESETS,
            current_staff_role,
        )

        self._set_permissions(self.target, ADMIN_ROLE_PERMISSION_PRESETS[ADMIN_ROLE_MODERATOR])
        self.assertEqual(current_staff_role(self.target), ADMIN_ROLE_MODERATOR)

        assign_staff_role(actor=self.initiator, target_id=self.target.pk, role=ADMIN_ROLE_VOLUNTEER)
        self.target.refresh_from_db()
        self.assertEqual(current_staff_role(self.target), ADMIN_ROLE_VOLUNTEER)
        self.assertEqual(set(self.target.groups.values_list("name", flat=True)), {"KidsMap Volunteers"})
        self.assertFalse(self.target.user_permissions.exists())

        assign_staff_role(actor=self.initiator, target_id=self.target.pk, role=ADMIN_ROLE_CONTENT_MANAGER)
        self.target.refresh_from_db()
        self.assertEqual(current_staff_role(self.target), ADMIN_ROLE_CONTENT_MANAGER)
        self.assertFalse(self.target.groups.exists())
        self.assertEqual(
            set(self.target.user_permissions.values_list("codename", flat=True)),
            ADMIN_ROLE_PERMISSION_PRESETS[ADMIN_ROLE_CONTENT_MANAGER],
        )

    def test_superadmin_changes_existing_admin_to_volunteer_without_deleting_user(self):
        from catalog.models import StaffRoleAudit
        from catalog.services.staff_role_workflow import assign_staff_role
        from catalog.services.staff_roles import ADMIN_ROLE_VOLUNTEER

        target_pk = self.target.pk
        profile_pk = self.target.profile.pk
        place_pk = self.place.pk

        assign_staff_role(actor=self.initiator, target_id=target_pk, role=ADMIN_ROLE_VOLUNTEER)

        self.target.refresh_from_db()
        self.assertEqual(self.target.pk, target_pk)
        self.assertEqual(self.target.profile.pk, profile_pk)
        self.assertEqual(self.target.created_places.get().pk, place_pk)
        self.assertTrue(self.target.is_staff)
        self.assertFalse(self.target.is_superuser)
        self.assertTrue(self.target.groups.filter(name="KidsMap Volunteers").exists())
        audit = StaffRoleAudit.objects.get(target=self.target, action=StaffRoleAudit.Action.ROLE_CHANGED)
        self.assertEqual(audit.actor, self.initiator)
        self.assertEqual(audit.new_role, ADMIN_ROLE_VOLUNTEER)
        self.assertTrue(audit.created_at)

    def test_superadmin_promotion_requires_a_different_active_superadmin(self):
        from catalog.models import StaffRoleAudit, SuperadminPromotionRequest
        from catalog.services.staff_role_workflow import (
            request_superadmin_promotion,
            resolve_superadmin_promotion,
        )

        request = request_superadmin_promotion(actor=self.initiator, target_id=self.target.pk)
        self.target.refresh_from_db()
        self.assertFalse(self.target.is_superuser)
        self.assertEqual(request.status, SuperadminPromotionRequest.Status.PENDING)
        self.assertTrue(StaffRoleAudit.objects.filter(
            promotion_request=request,
            action=StaffRoleAudit.Action.SUPERADMIN_REQUESTED,
        ).exists())

        with self.assertRaises(ValidationError):
            resolve_superadmin_promotion(actor=self.initiator, request_id=request.pk, approve=True)

        resolved = resolve_superadmin_promotion(actor=self.approver, request_id=request.pk, approve=True)
        self.target.refresh_from_db()
        self.assertTrue(self.target.is_superuser)
        self.assertTrue(self.target.is_staff)
        self.assertEqual(resolved.status, SuperadminPromotionRequest.Status.APPROVED)
        self.assertEqual(resolved.decided_by, self.approver)
        self.assertEqual(
            StaffRoleAudit.objects.filter(
                promotion_request=request,
                action=StaffRoleAudit.Action.SUPERADMIN_APPROVED,
            ).count(),
            1,
        )
        with self.assertRaises(ValidationError):
            resolve_superadmin_promotion(actor=self.approver, request_id=request.pk, approve=True)

    def test_non_superadmin_cannot_change_or_request_or_resolve_roles(self):
        from catalog.services.staff_role_workflow import (
            assign_staff_role,
            request_superadmin_promotion,
            resolve_superadmin_promotion,
        )
        from catalog.services.staff_roles import ADMIN_ROLE_VOLUNTEER

        ordinary = User.objects.create_user("ordinary-staff", is_staff=True)
        request = request_superadmin_promotion(actor=self.initiator, target_id=self.target.pk)

        with self.assertRaises(PermissionDenied):
            assign_staff_role(actor=ordinary, target_id=self.target.pk, role=ADMIN_ROLE_VOLUNTEER)
        with self.assertRaises(PermissionDenied):
            request_superadmin_promotion(actor=ordinary, target_id=self.target.pk)
        with self.assertRaises(PermissionDenied):
            resolve_superadmin_promotion(actor=ordinary, request_id=request.pk, approve=True)

    def test_duplicate_disabled_and_stale_superadmin_requests_are_rejected(self):
        from catalog.services.staff_role_workflow import (
            request_superadmin_promotion,
            resolve_superadmin_promotion,
        )

        request = request_superadmin_promotion(actor=self.initiator, target_id=self.target.pk)
        with self.assertRaises(ValidationError):
            request_superadmin_promotion(actor=self.initiator, target_id=self.target.pk)

        resolve_superadmin_promotion(actor=self.approver, request_id=request.pk, approve=False, rejection_note="No")
        with self.assertRaises(ValidationError):
            resolve_superadmin_promotion(actor=self.approver, request_id=request.pk, approve=True)

        self.target.is_active = False
        self.target.save(update_fields=["is_active"])
        with self.assertRaises(ValidationError):
            request_superadmin_promotion(actor=self.initiator, target_id=self.target.pk)

    def test_last_active_superadmin_cannot_be_demoted_or_deactivated(self):
        from catalog.models import StaffRoleAudit
        from catalog.services.staff_role_workflow import assign_staff_role, set_staff_active
        from catalog.services.staff_roles import ADMIN_ROLE_MODERATOR

        self.approver.is_active = False
        self.approver.save(update_fields=["is_active"])

        with self.assertRaises(ValidationError):
            assign_staff_role(actor=self.initiator, target_id=self.initiator.pk, role=ADMIN_ROLE_MODERATOR)
        with self.assertRaises(ValidationError):
            set_staff_active(actor=self.initiator, target_id=self.initiator.pk, is_active=False)

        self.initiator.refresh_from_db()
        self.assertTrue(self.initiator.is_superuser)
        self.assertTrue(self.initiator.is_active)
        self.assertGreaterEqual(
            StaffRoleAudit.objects.filter(action=StaffRoleAudit.Action.LAST_SUPERADMIN_BLOCKED).count(),
            2,
        )

    def test_one_superadmin_can_demote_another_when_both_are_active(self):
        from catalog.services.staff_role_workflow import assign_staff_role
        from catalog.services.staff_roles import ADMIN_ROLE_MODERATOR, current_staff_role

        assign_staff_role(actor=self.initiator, target_id=self.approver.pk, role=ADMIN_ROLE_MODERATOR)

        self.approver.refresh_from_db()
        self.assertFalse(self.approver.is_superuser)
        self.assertTrue(self.approver.is_staff)
        self.assertEqual(current_staff_role(self.approver), ADMIN_ROLE_MODERATOR)

    def test_pending_superadmin_request_notifies_other_active_superadmins(self):
        from catalog.services.staff_role_workflow import request_superadmin_promotion

        inactive = User.objects.create_superuser(
            "inactive-superadmin",
            "inactive@example.test",
            "password",
        )
        inactive.is_active = False
        inactive.save(update_fields=["is_active"])

        with self.captureOnCommitCallbacks(execute=True):
            request = request_superadmin_promotion(actor=self.initiator, target_id=self.target.pk)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.approver.email])
        self.assertIn(self.target.username, mail.outbox[0].body)
        self.assertIn(self.initiator.username, mail.outbox[0].body)
        self.assertIn(str(request.pk), mail.outbox[0].body)
        self.assertIn(request.created_at.strftime("%Y-%m-%d"), mail.outbox[0].body)
        self.assertNotIn("password", mail.outbox[0].body.lower())

    def test_staff_change_form_uses_role_workflow_not_raw_permission_fields(self):
        from catalog.services.staff_roles import ADMIN_ROLE_VOLUNTEER

        self.client.force_login(self.initiator)
        change_url = reverse("admin:catalog_staffaccessuser_change", args=[self.target.pk])
        response = self.client.get(change_url)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        self.assertIn('name="admin_role"', content)
        self.assertNotIn('name="is_superuser"', content)
        self.assertNotIn('name="is_staff"', content)
        self.assertNotIn('name="groups"', content)
        self.assertNotIn('name="user_permissions"', content)

        role_url = reverse("admin:catalog_staffaccessuser_role_change", args=[self.target.pk])
        response = self.client.post(role_url, {
            "admin_role": ADMIN_ROLE_VOLUNTEER,
            "is_active": "on",
            "is_superuser": "on",
            "groups": [Group.objects.create(name="Unsafe group").pk],
            "user_permissions": list(Permission.objects.values_list("pk", flat=True)[:2]),
        })
        self.assertEqual(response.status_code, 302)
        self.target.refresh_from_db()
        self.assertFalse(self.target.is_superuser)
        self.assertEqual(set(self.target.groups.values_list("name", flat=True)), {"KidsMap Volunteers"})
        self.assertFalse(self.target.user_permissions.exists())

        response = self.client.post(change_url, {
            "username": self.target.username,
            "email": self.target.email,
            "first_name": "Safe",
            "last_name": "Edit",
            "is_superuser": "on",
            "is_staff": "on",
            "groups": [Group.objects.create(name="Second unsafe group").pk],
            "user_permissions": list(Permission.objects.values_list("pk", flat=True)[:2]),
            "profile-TOTAL_FORMS": "1",
            "profile-INITIAL_FORMS": "1",
            "profile-MIN_NUM_FORMS": "0",
            "profile-MAX_NUM_FORMS": "1",
            "profile-0-id": self.target.profile.pk,
            "profile-0-user": self.target.pk,
            "profile-0-phone": "",
            "profile-0-gender": UserProfile.GENDER_UNSPECIFIED,
            "_save": "Save",
        })
        self.assertEqual(response.status_code, 302)
        self.target.refresh_from_db()
        self.assertFalse(self.target.is_superuser)
        self.assertEqual(set(self.target.groups.values_list("name", flat=True)), {"KidsMap Volunteers"})
        self.assertFalse(self.target.user_permissions.exists())

    def test_superadmin_creation_is_not_a_direct_role_option(self):
        self.client.force_login(self.initiator)
        add_url = reverse("admin:catalog_staffaccessuser_add")
        response = self.client.get(add_url)
        self.assertNotContains(response, 'value="superadmin"', html=False)

        response = self.client.post(add_url, {
            "username": "crafted-superadmin",
            "email": "crafted@example.test",
            "password1": "StrongPass123!!",
            "password2": "StrongPass123!!",
            "admin_role": "superadmin",
            "profile-TOTAL_FORMS": "1",
            "profile-INITIAL_FORMS": "0",
            "profile-MIN_NUM_FORMS": "0",
            "profile-MAX_NUM_FORMS": "1",
            "profile-0-phone": "",
            "profile-0-gender": UserProfile.GENDER_UNSPECIFIED,
            "_save": "Save",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="crafted-superadmin").exists())

    def test_pending_queue_and_confirmation_are_visible_only_to_superadmins(self):
        from catalog.services.staff_role_workflow import request_superadmin_promotion

        request = request_superadmin_promotion(actor=self.initiator, target_id=self.target.pk)
        list_url = reverse("admin:catalog_staffaccessuser_superadmin_request_list")
        confirm_url = reverse(
            "admin:catalog_staffaccessuser_superadmin_request_confirm",
            args=[request.pk],
        )

        self.client.force_login(self.approver)
        response = self.client.get(list_url)
        self.assertContains(response, self.target.username)
        self.assertContains(response, self.initiator.username)
        self.assertContains(response, confirm_url)
        self.assertContains(
            response,
            'class="km-staff-promotion-status km-staff-promotion-status--pending"',
            html=False,
        )
        self.assertContains(response, 'class="km-staff-promotion-action"', html=False)
        response = self.client.get(confirm_url)
        self.assertContains(response, 'class="km-staff-promotion-warning"', html=False)
        self.assertContains(response, "Подтвердить")
        self.assertContains(response, "Отклонить")

        self.client.force_login(self.target)
        self.assertEqual(self.client.get(list_url).status_code, 403)
        self.assertEqual(self.client.get(confirm_url).status_code, 403)
        self.assertEqual(self.client.post(confirm_url, {"decision": "approve"}).status_code, 403)
        self.assertEqual(
            self.client.post(
                reverse("admin:catalog_staffaccessuser_role_change", args=[self.target.pk]),
                {"admin_role": "volunteer", "is_active": "on"},
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.post(
                reverse("admin:catalog_staffaccessuser_request_superadmin", args=[self.target.pk]),
            ).status_code,
            403,
        )

    def test_inactive_superadmin_cannot_confirm_and_admin_post_approves_once(self):
        from catalog.models import SuperadminPromotionRequest
        from catalog.services.staff_role_workflow import request_superadmin_promotion

        promotion = request_superadmin_promotion(actor=self.initiator, target_id=self.target.pk)
        confirm_url = reverse(
            "admin:catalog_staffaccessuser_superadmin_request_confirm",
            args=[promotion.pk],
        )
        self.approver.is_active = False
        self.approver.save(update_fields=["is_active"])
        self.client.force_login(self.approver)
        self.assertEqual(self.client.post(confirm_url, {"decision": "approve"}).status_code, 302)
        promotion.refresh_from_db()
        self.target.refresh_from_db()
        self.assertEqual(promotion.status, SuperadminPromotionRequest.Status.PENDING)
        self.assertFalse(self.target.is_superuser)

        self.approver.is_active = True
        self.approver.save(update_fields=["is_active"])
        self.client.force_login(self.approver)
        self.assertEqual(self.client.post(confirm_url, {"decision": "approve"}).status_code, 302)
        promotion.refresh_from_db()
        self.target.refresh_from_db()
        self.assertEqual(promotion.status, SuperadminPromotionRequest.Status.APPROVED)
        self.assertTrue(self.target.is_superuser)

    def test_email_delivery_failure_does_not_cancel_pending_request(self):
        from catalog.models import SuperadminPromotionRequest
        from catalog.services.staff_role_workflow import request_superadmin_promotion

        with self.assertLogs("catalog.services.staff_role_workflow", level="ERROR"):
            with patch(
                "catalog.services.staff_role_workflow.send_mail",
                side_effect=RuntimeError("mail transport unavailable"),
            ):
                with self.captureOnCommitCallbacks(execute=True):
                    promotion = request_superadmin_promotion(
                        actor=self.initiator,
                        target_id=self.target.pk,
                    )

        promotion.refresh_from_db()
        self.target.refresh_from_db()
        self.assertEqual(promotion.status, SuperadminPromotionRequest.Status.PENDING)
        self.assertFalse(self.target.is_superuser)

    def test_admin_endpoint_blocks_last_superadmin_demotion_and_deactivation(self):
        from catalog.models import StaffRoleAudit
        from catalog.services.staff_roles import ADMIN_ROLE_MODERATOR

        self.approver.is_active = False
        self.approver.save(update_fields=["is_active"])
        self.client.force_login(self.initiator)
        role_url = reverse(
            "admin:catalog_staffaccessuser_role_change",
            args=[self.initiator.pk],
        )

        response = self.client.post(role_url, {
            "admin_role": ADMIN_ROLE_MODERATOR,
        })

        self.assertEqual(response.status_code, 302)
        self.initiator.refresh_from_db()
        self.assertTrue(self.initiator.is_active)
        self.assertTrue(self.initiator.is_superuser)
        self.assertTrue(StaffRoleAudit.objects.filter(
            target=self.initiator,
            action=StaffRoleAudit.Action.LAST_SUPERADMIN_BLOCKED,
        ).exists())


@skipUnless(connection.vendor == "postgresql", "Requires PostgreSQL row-level locks")
class StaffRoleWorkflowConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.initiator = User.objects.create_superuser(
            username="concurrency-initiator",
            email="concurrency-initiator@example.test",
            password="password",
        )
        self.approver_one = User.objects.create_superuser(
            username="concurrency-approver-one",
            email="concurrency-approver-one@example.test",
            password="password",
        )
        self.approver_two = User.objects.create_superuser(
            username="concurrency-approver-two",
            email="concurrency-approver-two@example.test",
            password="password",
        )
        self.target = User.objects.create_user(
            username="concurrency-target",
            email="concurrency-target@example.test",
            password="password",
            is_staff=True,
        )

    def test_only_one_concurrent_approval_succeeds(self):
        from catalog.models import StaffRoleAudit, SuperadminPromotionRequest
        from catalog.services.staff_role_workflow import (
            request_superadmin_promotion,
            resolve_superadmin_promotion,
        )

        promotion = request_superadmin_promotion(
            actor=self.initiator,
            target_id=self.target.pk,
        )
        barrier = Barrier(2)

        def approve(actor_id):
            connections.close_all()
            try:
                actor = User.objects.get(pk=actor_id)
                barrier.wait(timeout=10)
                resolve_superadmin_promotion(
                    actor=actor,
                    request_id=promotion.pk,
                    approve=True,
                )
                return "approved"
            except ValidationError:
                return "stale"
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(
                approve,
                [self.approver_one.pk, self.approver_two.pk],
            ))

        promotion.refresh_from_db()
        self.target.refresh_from_db()
        self.assertCountEqual(results, ["approved", "stale"])
        self.assertEqual(promotion.status, SuperadminPromotionRequest.Status.APPROVED)
        self.assertTrue(self.target.is_superuser)
        self.assertEqual(
            StaffRoleAudit.objects.filter(
                promotion_request=promotion,
                action=StaffRoleAudit.Action.SUPERADMIN_APPROVED,
            ).count(),
            1,
        )
