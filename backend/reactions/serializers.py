from rest_framework import serializers
from .models import Reaction, Share
from users.serializers import UserPublicSerializer

class ReactionSerializer(serializers.ModelSerializer):
    user = UserPublicSerializer(read_only=True)

    class Meta:
        model  = Reaction
        fields = ['id', 'user', 'post', 'comment', 'reaction_type', 'created_at']
        read_only_fields = ['user']

    def validate(self, data):
        # must have either post or comment, not both, not neither
        post    = data.get('post')
        comment = data.get('comment')

        if not post and not comment:
            raise serializers.ValidationError(
                "A reaction must target either a post or a comment."
            )
        if post and comment:
            raise serializers.ValidationError(
                "A reaction cannot target both a post and a comment."
            )
        return data

    def create(self, validated_data):
        # 'user' is injected by perform_create via serializer.save(user=...).
        # Pop it so it doesn't conflict with **validated_data below.
        user = validated_data.pop('user', None) or self.context['request'].user
        post    = validated_data.get('post')
        comment = validated_data.get('comment')

        # toggle: if same reaction exists remove it; if different, update it
        existing = Reaction.objects.filter(
            user    = user,
            post    = post,
            comment = comment
        ).first()

        if existing:
            if existing.reaction_type == validated_data['reaction_type']:
                existing.delete()   # clicking same button removes reaction
                # Signal the view that this was a "toggle off", not a creation
                raise serializers.ValidationError({'toggled_off': True, 'detail': 'Reaction removed.'})
            else:
                existing.reaction_type = validated_data['reaction_type']
                existing.save()
                return existing

        return Reaction.objects.create(user=user, **validated_data)


class ShareSerializer(serializers.ModelSerializer):
    user = UserPublicSerializer(read_only=True)

    class Meta:
        model  = Share
        fields = ['id', 'user', 'post', 'platform', 'shared_at']
        read_only_fields = ['user', 'shared_at']