# Generated by Django 2.2.2 on 2019-06-19 22:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('predictors', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='metric',
            name='timestamp',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
