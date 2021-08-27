# Generated by Django 3.1.7 on 2021-08-25 18:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lgr_models', '0003_populate_default_lgrs'),
    ]

    operations = [
        migrations.CreateModel(
            name='UnicodeVersion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version', models.CharField(max_length=255, unique=True)),
                ('activated', models.BooleanField()),
            ],
        ),
    ]
