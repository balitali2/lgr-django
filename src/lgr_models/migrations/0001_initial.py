# Generated by Django 3.1.7 on 2021-02-26 02:21

from django.db import migrations, models
import django.db.models.deletion
import lgr_models.models.lgr


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='RefLgr',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to=lgr_models.models.lgr.get_upload_path)),
                ('name', models.CharField(max_length=128, unique=True)),
                ('language_script', models.CharField(max_length=32, unique=True)),
                ('language', models.CharField(blank=True, max_length=8)),
                ('script', models.CharField(blank=True, max_length=8)),
            ],
            options={
                'ordering': ['name'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RzLgr',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to=lgr_models.models.lgr.get_upload_path)),
                ('name', models.CharField(max_length=128, unique=True)),
            ],
            options={
                'ordering': ['name'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RzLgrMember',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to=lgr_models.models.lgr.get_upload_path)),
                ('name', models.CharField(max_length=128, unique=True)),
                ('language', models.CharField(max_length=8)),
                ('script', models.CharField(max_length=8)),
                ('rz_lgr', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='repository', to='lgr_models.rzlgr')),
            ],
            options={
                'ordering': ['name'],
                'abstract': False,
            },
        ),
    ]
