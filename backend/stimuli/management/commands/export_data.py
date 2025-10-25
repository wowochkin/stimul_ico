from django.core.management.base import BaseCommand
from django.core.management import call_command
import os
from pathlib import Path


class Command(BaseCommand):
    help = 'Экспортирует данные из базы данных в фикстуры для миграции'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='data_export.json',
            help='Имя файла для экспорта (по умолчанию: data_export.json)'
        )
        parser.add_argument(
            '--app',
            type=str,
            action='append',
            help='Экспортировать данные только из указанного приложения (можно указать несколько раз)'
        )

    def handle(self, *args, **options):
        output_file = options['output']
        apps = options.get('app', [])
        
        # Определяем путь для сохранения фикстур
        fixtures_dir = Path('fixtures')
        fixtures_dir.mkdir(exist_ok=True)
        
        output_path = fixtures_dir / output_file
        
        self.stdout.write('📦 Начинаем экспорт данных...')
        
        try:
            if apps:
                # Экспортируем только указанные приложения
                for app in apps:
                    self.stdout.write(f'📤 Экспортируем данные из приложения: {app}')
                    app_output = fixtures_dir / f'{app}_data.json'
                    call_command('dumpdata', app, output=app_output, indent=2)
                    self.stdout.write(self.style.SUCCESS(f'✅ Данные из {app} экспортированы в {app_output}'))
            else:
                # Экспортируем все данные
                call_command('dumpdata', output=output_path, indent=2, exclude=['contenttypes', 'auth.permission'])
                self.stdout.write(self.style.SUCCESS(f'✅ Все данные экспортированы в {output_path}'))
            
            # Показываем размер файла
            file_size = output_path.stat().st_size if output_path.exists() else 0
            self.stdout.write(f'📊 Размер файла: {file_size / 1024:.1f} KB')
            
            self.stdout.write('\n📋 Инструкции по импорту:')
            self.stdout.write('1. Скопируйте файл фикстур на сервер')
            self.stdout.write('2. Выполните: python manage.py loaddata fixtures/data_export.json')
            self.stdout.write('3. Проверьте данные в админке Django')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Ошибка при экспорте: {str(e)}')
            )
            return
        
        self.stdout.write(self.style.SUCCESS('\n🎉 Экспорт завершен успешно!'))
