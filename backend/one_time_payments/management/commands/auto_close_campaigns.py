"""
Команда для автоматического закрытия кампаний.
Запускайте эту команду ежедневно через cron для автоматического закрытия кампаний.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from one_time_payments.models import RequestCampaign


class Command(BaseCommand):
    help = 'Автоматически закрывает кампании, у которых истек дедлайн'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Только показать кампании, которые будут закрыты, без фактического закрытия',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        today = timezone.localdate()
        
        # Находим все открытые кампании с включенным автозакрытием
        campaigns = RequestCampaign.objects.filter(
            status=RequestCampaign.Status.OPEN,
            auto_close_enabled=True,
        )
        
        closed_count = 0
        
        for campaign in campaigns:
            if campaign.should_auto_close(on_date=today):
                if dry_run:
                    self.stdout.write(
                        self.style.WARNING(
                            f'[DRY RUN] Будет закрыта кампания: {campaign.name} '
                            f'(дедлайн: {campaign.deadline.strftime("%d.%m.%Y")})'
                        )
                    )
                else:
                    try:
                        campaign.close(archive=False)
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Закрыта кампания: {campaign.name} '
                                f'(дедлайн: {campaign.deadline.strftime("%d.%m.%Y")})'
                            )
                        )
                        closed_count += 1
                    except Exception as exc:
                        self.stdout.write(
                            self.style.ERROR(
                                f'Ошибка при закрытии кампании {campaign.name}: {exc}'
                            )
                        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'\n[DRY RUN] Всего кампаний для закрытия: {closed_count}'
                )
            )
        elif closed_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'\nУспешно закрыто кампаний: {closed_count}')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('Нет кампаний для автоматического закрытия.')
            )

