from django.core.management.base import BaseCommand
from django.core.management import call_command
from pathlib import Path


class Command(BaseCommand):
    help = 'Импортирует данные из фикстур в базу данных'

    def add_arguments(self, parser):
        parser.add_argument(
            'fixture_file',
            type=str,
            help='Путь к файлу фикстур для импорта'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Очистить существующие данные перед импортом'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать что будет импортировано без фактического импорта'
        )

    def handle(self, *args, **options):
        fixture_file = options['fixture_file']
        clear_data = options['clear']
        dry_run = options['dry_run']
        
        # Проверяем существование файла
        fixture_path = Path(fixture_file)
        if not fixture_path.exists():
            self.stdout.write(
                self.style.ERROR(f'❌ Файл {fixture_file} не найден!')
            )
            return
        
        self.stdout.write('📦 Начинаем импорт данных...')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 [DRY RUN] Режим предварительного просмотра'))
            # В dry-run режиме просто показываем информацию о файле
            file_size = fixture_path.stat().st_size
            self.stdout.write(f'📊 Размер файла: {file_size / 1024:.1f} KB')
            self.stdout.write(f'📁 Путь к файлу: {fixture_path.absolute()}')
            self.stdout.write('✅ Dry-run завершен. Для фактического импорта уберите флаг --dry-run')
            return
        
        try:
            if clear_data:
                self.stdout.write('🗑️  Очищаем существующие данные...')
                call_command('flush', '--noinput')
                self.stdout.write(self.style.WARNING('⚠️  Все данные очищены!'))
            
            # Импортируем данные
            self.stdout.write(f'📤 Импортируем данные из {fixture_file}...')
            call_command('loaddata', fixture_file)
            
            self.stdout.write(self.style.SUCCESS('✅ Данные успешно импортированы!'))
            
            # Показываем статистику
            self.stdout.write('\n📊 Статистика импорта:')
            self.stdout.write('Проверьте данные в админке Django или выполните:')
            self.stdout.write('python manage.py shell -c "from staffing.models import Division, Position; print(f\'Подразделений: {Division.objects.count()}, Должностей: {Position.objects.count()}\')"')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Ошибка при импорте: {str(e)}')
            )
            return
        
        self.stdout.write(self.style.SUCCESS('\n🎉 Импорт завершен успешно!'))
