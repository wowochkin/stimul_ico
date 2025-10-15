from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Division',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True, verbose_name='Название подразделения')),
            ],
            options={
                'ordering': ['name'],
                'verbose_name': 'Подразделение',
                'verbose_name_plural': 'Подразделения',
            },
        ),
        migrations.CreateModel(
            name='Position',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True, verbose_name='Название должности')),
                ('base_salary', models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Оклад')),
            ],
            options={
                'ordering': ['name'],
                'verbose_name': 'Должность',
                'verbose_name_plural': 'Должности',
            },
        ),
        migrations.CreateModel(
            name='PositionQuota',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_fte', models.DecimalField(decimal_places=3, default=0, max_digits=6, verbose_name='Количество ставок')),
                ('comment', models.CharField(blank=True, max_length=255, verbose_name='Комментарий')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Создано')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Обновлено')),
                ('division', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='quotas', to='staffing.division', verbose_name='Подразделение')),
                ('position', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='quotas', to='staffing.position', verbose_name='Должность')),
            ],
            options={
                'verbose_name': 'Позиция штатного расписания',
                'verbose_name_plural': 'Позиции штатного расписания',
                'unique_together': {('division', 'position')},
            },
        ),
        migrations.CreateModel(
            name='PositionQuotaVersion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('effective_from', models.DateField(verbose_name='Действует с')),
                ('effective_to', models.DateField(blank=True, null=True, verbose_name='Действует по')),
                ('total_fte', models.DecimalField(decimal_places=3, default=0, max_digits=6, verbose_name='Количество ставок')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Создано')),
                ('quota', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='versions', to='staffing.positionquota', verbose_name='Позиция')),
            ],
            options={
                'ordering': ['-effective_from', '-created_at'],
                'verbose_name': 'Версия штатного расписания',
                'verbose_name_plural': 'Версии штатного расписания',
            },
        ),
    ]
