# Generated by Django 2.1 on 2018-10-02 13:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('imageboard', '0003_remove_thread_last_post_hid'),
    ]

    operations = [
        migrations.AddField(
            model_name='board',
            name='custom_style',
            field=models.TextField(blank=True),
        ),
    ]
