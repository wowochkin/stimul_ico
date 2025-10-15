from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('staffing', '0001_initial'),
        ('stimuli', '0003_division_fk'),
    ]

    operations = [
        migrations.CreateModel(
            name='InternalAssignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rate', models.DecimalField(decimal_places=2, default=1, max_digits=5, verbose_name='Ставка')),
                ('allowance_amount', models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Надбавка')),
                ('allowance_reason', models.CharField(blank=True, max_length=255, verbose_name='Основание надбавки')),
                ('allowance_until', models.DateField(blank=True, null=True, verbose_name='Срок надбавки')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assignments', to='stimuli.employee', verbose_name='Сотрудник')),
                ('position', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='assignments', to='staffing.position', verbose_name='Должность')),
            ],
            options={
                'verbose_name': 'Внутреннее совмещение',
                'verbose_name_plural': 'Внутренние совмещения',
            },
        ),
    ]
