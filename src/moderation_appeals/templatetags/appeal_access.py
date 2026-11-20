from django import template

from moderation_appeals.services import can_access_queue

register = template.Library()
register.simple_tag(can_access_queue, name="can_review_appeals")
