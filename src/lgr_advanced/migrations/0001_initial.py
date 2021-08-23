# Generated by Django 3.1.7 on 2021-08-26 13:36

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import lgr_advanced.models
import lgr_models.models.lgr


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='LgrModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to=lgr_models.models.lgr.get_upload_path)),
                ('name', models.CharField(max_length=128)),
                ('validating_repertoire', models.CharField(blank=True, max_length=256, null=True)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['name'],
                'abstract': False,
            },
            bases=(models.Model, lgr_advanced.models.RepertoireCacheMixin),
        ),
        migrations.CreateModel(
            name='LgrSetInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('lgr', models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='set_info', to='lgr_advanced.lgrmodel')),
            ],
        ),
        migrations.CreateModel(
            name='SetLgrModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to=lgr_models.models.lgr.get_upload_path)),
                ('name', models.CharField(max_length=128)),
                ('validating_repertoire', models.CharField(blank=True, max_length=256, null=True)),
                ('common', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lgr_set', to='lgr_advanced.lgrsetinfo')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['name'],
                'abstract': False,
            },
            bases=(models.Model, lgr_advanced.models.RepertoireCacheMixin),
        ),
    ]
