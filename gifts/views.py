from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import models
from django.utils import timezone

from .models import Campaign, CampaignParticipation
from .serializers import CampaignSerializer, CampaignParticipationSerializer


class CampaignViewSet(viewsets.ModelViewSet):
    queryset = Campaign.objects.all().prefetch_related('rules_list', 'winners', 'participants')
    serializer_class = CampaignSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = super().get_queryset()
        type_q = self.request.query_params.get('type')
        status_q = self.request.query_params.get('status')
        if type_q:
            qs = qs.filter(type=type_q)
        
        now = timezone.now()
        if status_q:
            if status_q != 'all':
                qs = qs.filter(status=status_q)
        else:
            # Client-side: only show active and unexpired campaigns
            qs = qs.filter(
                status='active',
                starts_at__lte=now
            ).filter(
                models.Q(ends_at__isnull=True) | models.Q(ends_at__gte=now)
            )
        return qs

    @action(detail=True, methods=['get', 'post'], permission_classes=[permissions.AllowAny])
    def join(self, request, pk=None):
        campaign = self.get_object()

        if request.method == 'GET':
            qs = campaign.participants.all().order_by('-created_at')[:200]
            serializer = CampaignParticipationSerializer(qs, many=True, context={'request': request})
            return Response(serializer.data)

        if not campaign.is_active:
            return Response({'detail': 'Bu aksiýa häzir işjeň däl'}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user if request.user.is_authenticated else None
        data = request.data or {}
        full_name = data.get('full_name', '').strip()
        phone = data.get('phone', '').strip()
        email = data.get('email', '').strip()
        note = data.get('note', '').strip()

        if not user and not (full_name and phone):
            return Response({'detail': 'Ady we telefon belgisi hökmany'}, status=status.HTTP_400_BAD_REQUEST)

        if user:
            participation, created = CampaignParticipation.objects.get_or_create(
                campaign=campaign, user=user,
                defaults={'full_name': full_name, 'phone': phone, 'email': email, 'note': note},
            )
            if not created:
                return Response({'detail': 'Siz öňden gatnaşyjy'}, status=status.HTTP_400_BAD_REQUEST)

            # Broadcast participation_created
            from management.ws_utils import broadcast_order_event
            p_data = CampaignParticipationSerializer(participation, context={'request': request}).data
            p_data['campaign_title'] = campaign.title
            broadcast_order_event("participation_created", {"participation": p_data})
        else:
            participation = CampaignParticipation.objects.create(
                campaign=campaign,
                full_name=full_name,
                phone=phone,
                email=email,
                note=note,
            )

            # Broadcast participation_created
            from management.ws_utils import broadcast_order_event
            p_data = CampaignParticipationSerializer(participation, context={'request': request}).data
            p_data['campaign_title'] = campaign.title
            broadcast_order_event("participation_created", {"participation": p_data})

        return Response(CampaignParticipationSerializer(participation, context={'request': request}).data,
                        status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def featured(self, request):
        qs = self.get_queryset().filter(is_featured=True, status='active')
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


class CampaignParticipationViewSet(viewsets.ModelViewSet):
    queryset = CampaignParticipation.objects.all()
    serializer_class = CampaignParticipationSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        instance = serializer.save()
        from management.ws_utils import broadcast_order_event
        p_data = serializer.data
        p_data['campaign_title'] = instance.campaign.title
        broadcast_order_event("participation_created", {"participation": p_data})

    def perform_update(self, serializer):
        instance = serializer.save()
        from management.ws_utils import broadcast_order_event
        p_data = serializer.data
        p_data['campaign_title'] = instance.campaign.title
        broadcast_order_event("participation_updated", {"participation": p_data})

    def perform_destroy(self, instance):
        participation_id = instance.id
        campaign_id = instance.campaign_id
        instance.delete()
        from management.ws_utils import broadcast_order_event
        broadcast_order_event("participation_deleted", {
            "participation_id": participation_id,
            "campaign_id": campaign_id
        })
