# Generated by Django 2.1.5 on 2019-01-17 13:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('imageboard', '0007_auto_20190111_1136'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='session_id',
            field=models.CharField(db_index=True, default='00000000000000000000000000000000', editable=False, max_length=32),
            preserve_default=False,
        ),
    ]
