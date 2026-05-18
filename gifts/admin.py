from django.contrib import admin
from .models import Campaign, CampaignRule, CampaignParticipation, CampaignWinner


class CampaignRuleInline(admin.TabularInline):
    model = CampaignRule
    extra = 1


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'status', 'starts_at', 'ends_at', 'is_featured')
    list_filter = ('type', 'status', 'is_featured')
    search_fields = ('title', 'description', 'promo_code')
    inlines = [CampaignRuleInline]


@admin.register(CampaignParticipation)
class CampaignParticipationAdmin(admin.ModelAdmin):
    list_display = ('campaign', 'user', 'full_name', 'phone', 'status', 'created_at')
    list_filter = ('campaign', 'status')
    search_fields = ('full_name', 'phone', 'email')


@admin.register(CampaignWinner)
class CampaignWinnerAdmin(admin.ModelAdmin):
    list_display = ('campaign', 'participant', 'prize_title', 'announced_at')
