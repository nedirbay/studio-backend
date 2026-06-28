from django.db import models
from django.conf import settings
from django.utils import timezone


class Campaign(models.Model):
    TYPE_CHOICES = [
        ('giveaway', 'Bäsleşik / Giveaway'),
        ('promotion', 'Aksiýa'),
        ('gift', 'Sowgat'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Garaşylýar'),
        ('active', 'Işjeň'),
        ('finished', 'Tamamlandy'),
        ('cancelled', 'Ýatyryldy'),
    ]

    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='giveaway')
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    image_url = models.CharField(max_length=500, blank=True)
    banner_url = models.CharField(max_length=500, blank=True)
    bg_gradient = models.CharField(max_length=120, default='from-red-600 to-orange-500')

    prize_title = models.CharField(max_length=200, blank=True)
    prize_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    prize_image = models.CharField(max_length=500, blank=True)

    starts_at = models.DateTimeField(default=timezone.now)
    ends_at = models.DateTimeField(null=True, blank=True)

    rules = models.TextField(blank=True, help_text='Gatnaşmagyň şertleri (her setir aýry şert)')
    min_order_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_percent = models.PositiveIntegerField(default=0)
    promo_code = models.CharField(max_length=80, blank=True)

    winners_count = models.PositiveIntegerField(default=1)
    is_featured = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_featured', '-starts_at']

    def __str__(self) -> str:
        return f"[{self.type}] {self.title}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Automatically sync the rules text field to CampaignRule objects
        self.rules_list.all().delete()
        if self.rules:
            lines = [line.strip() for line in self.rules.split('\n') if line.strip()]
            for idx, line in enumerate(lines):
                CampaignRule.objects.create(campaign=self, text=line, order=idx)

    @property
    def participants_count(self) -> int:
        return self.participants.count()

    @property
    def is_active(self) -> bool:
        now = timezone.now()
        if self.status != 'active':
            return False
        if self.ends_at and self.ends_at < now:
            return False
        return self.starts_at <= now


class CampaignRule(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='rules_list')
    text = models.CharField(max_length=300)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self) -> str:
        return self.text


class CampaignParticipation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Garaşylýar'),
        ('approved', 'Tassyklandy'),
        ('won', 'Ýeňiji'),
        ('rejected', 'Ret edildi'),
    ]

    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='campaign_participations',
        null=True,
        blank=True,
    )
    full_name = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=80, blank=True)
    email = models.EmailField(blank=True)
    note = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('campaign', 'user')
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.full_name or (self.user and self.user.username) or 'anonim'} -> {self.campaign.title}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old_status = None
        if not is_new:
            try:
                old_status = CampaignParticipation.objects.get(pk=self.pk).status
            except CampaignParticipation.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)
        
        if self.status == 'won' and old_status != 'won':
            CampaignWinner.objects.get_or_create(
                campaign=self.campaign,
                participant=self,
                defaults={'prize_title': self.campaign.prize_title or 'Aksiýa Sowgady'}
            )
        elif self.status != 'won' and old_status == 'won':
            CampaignWinner.objects.filter(campaign=self.campaign, participant=self).delete()


class CampaignWinner(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='winners')
    participant = models.ForeignKey(CampaignParticipation, on_delete=models.CASCADE, related_name='+')
    prize_title = models.CharField(max_length=200, blank=True)
    announced_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Winner: {self.participant} ({self.campaign.title})"
