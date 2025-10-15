from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stimuli', '0004_internal_assignments'),
    ]

    operations = [
        migrations.AlterField(
            model_name='employee',
            name='rate',
            field=models.DecimalField(decimal_places=3, default=1, max_digits=6, verbose_name='Ставка'),
        ),
        migrations.AlterField(
            model_name='internalassignment',
            name='rate',
            field=models.DecimalField(decimal_places=3, default=1, max_digits=6, verbose_name='Ставка'),
        ),
    ]
