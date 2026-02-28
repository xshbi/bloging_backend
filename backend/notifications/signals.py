from django.db.models.signals import post_save
from django.dispatch import receiver
from reactions.models import Reaction
from comments.models import Comment
from .models import Notification


@receiver(post_save, sender=Reaction)
def notify_on_reaction(sender, instance, created, **kwargs):
    if created and instance.post:
        # don't notify yourself
        if instance.user != instance.post.author:
            Notification.objects.create(
                recipient  = instance.post.author,
                sender     = instance.user,
                notif_type = instance.reaction_type,
                post       = instance.post
            )


@receiver(post_save, sender=Comment)
def notify_on_comment(sender, instance, created, **kwargs):
    if created:
        if instance.parent:
            # it's a reply — notify the parent comment author
            if instance.author != instance.parent.author:
                Notification.objects.create(
                    recipient  = instance.parent.author,
                    sender     = instance.author,
                    notif_type = 'reply',
                    post       = instance.post,
                    comment    = instance
                )
        else:
            # it's a top-level comment — notify the post author
            if instance.author != instance.post.author:
                Notification.objects.create(
                    recipient  = instance.post.author,
                    sender     = instance.author,
                    notif_type = 'comment',
                    post       = instance.post,
                    comment    = instance
                )