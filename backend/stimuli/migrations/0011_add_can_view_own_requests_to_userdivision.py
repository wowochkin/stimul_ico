# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stimuli', '0010_add_can_view_all_to_userdivision'),
    ]

    operations = [
        migrations.AddField(
            model_name='userdivision',
            name='can_view_own_requests',
            field=models.BooleanField(
                default=False,
                verbose_name='Может видеть заявки на себя',
                help_text='Если включено, пользователь может видеть заявки, поданные на самого себя, без возможности их редактирования'
            ),
        ),
    ]

