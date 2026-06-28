from rest_framework import serializers
from django.utils import timezone
from .models import Campaign, CampaignRule, CampaignParticipation, CampaignWinner


class CampaignRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = CampaignRule
        fields = ['id', 'text', 'order']


class CampaignParticipationSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = CampaignParticipation
        fields = [
            'id', 'campaign', 'user', 'user_name',
            'full_name', 'phone', 'email', 'note',
            'status', 'created_at',
        ]
        read_only_fields = ['user', 'created_at']

    def get_user_name(self, obj):
        if obj.user:
            return getattr(obj.user, 'username', None) or getattr(obj.user, 'email', None) or obj.full_name
        return obj.full_name or 'Anonim'


class CampaignWinnerSerializer(serializers.ModelSerializer):
    participant_name = serializers.SerializerMethodField()

    class Meta:
        model = CampaignWinner
        fields = ['id', 'campaign', 'participant', 'participant_name', 'prize_title', 'announced_at']

    def get_participant_name(self, obj):
        p = obj.participant
        if p.user:
            return getattr(p.user, 'username', None) or p.full_name or 'Anonim'
        return p.full_name or 'Anonim'


class CampaignSerializer(serializers.ModelSerializer):
    rules_list = CampaignRuleSerializer(many=True, read_only=True)
    winners = CampaignWinnerSerializer(many=True, read_only=True)
    participants_count = serializers.IntegerField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    joined_by_me = serializers.SerializerMethodField()
    time_left_seconds = serializers.SerializerMethodField()

    class Meta:
        model = Campaign
        fields = [
            'id', 'type', 'title', 'subtitle', 'description',
            'image_url', 'banner_url', 'bg_gradient',
            'prize_title', 'prize_value', 'prize_image',
            'starts_at', 'ends_at', 'rules',
            'min_order_amount', 'discount_percent', 'promo_code',
            'winners_count', 'is_featured', 'status',
            'rules_list', 'winners', 'participants_count', 'is_active',
            'joined_by_me', 'time_left_seconds', 'created_at',
        ]

    def get_joined_by_me(self, obj):
        request = self.context.get('request')
        if not request or not request.user or not request.user.is_authenticated:
            return False
        return CampaignParticipation.objects.filter(campaign=obj, user=request.user).exists()

    def get_time_left_seconds(self, obj):
        if not obj.ends_at:
            return None
        delta = obj.ends_at - timezone.now()
        return max(int(delta.total_seconds()), 0)
