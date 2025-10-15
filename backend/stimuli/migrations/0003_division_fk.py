from django.db import migrations, models
import django.db.models.deletion


def populate_structures(apps, schema_editor):
    Division = apps.get_model('staffing', 'Division')
    Position = apps.get_model('staffing', 'Position')
    Employee = apps.get_model('stimuli', 'Employee')

    for employee in Employee.objects.all():
        division_name = (employee.division_char or '').strip() or 'Не указано'
        position_name = (employee.position_char or '').strip() or 'Без должности'

        division_obj, _ = Division.objects.get_or_create(name=division_name)
        position_obj, _ = Position.objects.get_or_create(name=position_name)

        employee.division = division_obj
        employee.position = position_obj
        if employee.rate is None:
            employee.rate = 1
        if employee.allowance_amount is None:
            employee.allowance_amount = 0
        employee.save(update_fields=['division', 'position', 'rate', 'allowance_amount'])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('staffing', '0001_initial'),
        ('stimuli', '0002_alter_stimulusrequest_options'),
    ]

    operations = [
        migrations.RenameField(
            model_name='employee',
            old_name='division',
            new_name='division_char',
        ),
        migrations.RenameField(
            model_name='employee',
            old_name='position',
            new_name='position_char',
        ),
        migrations.AddField(
            model_name='employee',
            name='division',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='employees', to='staffing.division', verbose_name='Подразделение'),
        ),
        migrations.AddField(
            model_name='employee',
            name='position',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='employees', to='staffing.position', verbose_name='Должность'),
        ),
        migrations.AddField(
            model_name='employee',
            name='rate',
            field=models.DecimalField(decimal_places=2, default=1, max_digits=5, verbose_name='Ставка'),
        ),
        migrations.AddField(
            model_name='employee',
            name='allowance_amount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Надбавка'),
        ),
        migrations.AddField(
            model_name='employee',
            name='allowance_reason',
            field=models.CharField(blank=True, max_length=255, verbose_name='Основание надбавки'),
        ),
        migrations.AddField(
            model_name='employee',
            name='allowance_until',
            field=models.DateField(blank=True, null=True, verbose_name='Срок надбавки'),
        ),
        migrations.RunPython(populate_structures, reverse_code=noop_reverse),
        migrations.AlterField(
            model_name='employee',
            name='division',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='employees', to='staffing.division', verbose_name='Подразделение'),
        ),
        migrations.AlterField(
            model_name='employee',
            name='position',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='employees', to='staffing.position', verbose_name='Должность'),
        ),
        migrations.RemoveField(
            model_name='employee',
            name='division_char',
        ),
        migrations.RemoveField(
            model_name='employee',
            name='position_char',
        ),
    ]
