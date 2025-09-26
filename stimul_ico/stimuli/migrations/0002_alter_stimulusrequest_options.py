from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stimuli', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='stimulusrequest',
            options={
                'ordering': ['-created_at'],
                'permissions': [
                    ('view_all_requests', 'Может видеть все заявки'),
                    ('edit_pending_requests', 'Может редактировать заявки на рассмотрении'),
                ],
                'verbose_name': 'Заявка на стимулирование',
                'verbose_name_plural': 'Заявки на стимулирование',
            },
        ),
    ]
