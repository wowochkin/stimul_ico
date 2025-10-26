# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stimuli', '0009_add_final_status_field'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userdivision',
            name='division',
            field=models.ForeignKey(
                'staffing.Division',
                on_delete=models.CASCADE,
                related_name='managers',
                verbose_name='Подразделение',
                null=True,
                blank=True,
                help_text='Оставьте пустым для доступа ко всем сотрудникам'
            ),
        ),
        migrations.AddField(
            model_name='userdivision',
            name='can_view_all',
            field=models.BooleanField(
                default=False,
                verbose_name='Доступ ко всем сотрудникам',
                help_text='Если включено, пользователь видит всех сотрудников независимо от подразделения'
            ),
        ),
    ]

