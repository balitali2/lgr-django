# Generated by Django 3.1.7 on 2022-07-14 17:34

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import lgr_models.models.lgr


def reflgr_initial_data(apps, schema_editor):
    OldRefLgr = apps.get_model("lgr_models", "RefLgr")
    OldRefLgrMember = apps.get_model("lgr_models", "RefLgrMember")
    db_alias = schema_editor.connection.alias
    reflgr = OldRefLgrMember.objects.using(db_alias).first()
    OldRefLgr.objects.using(db_alias).create(name='Ref LGR',
                                             file=reflgr.file,
                                             owner=reflgr.owner,
                                             active=False)


def reflgrmember_link_to_reflgr(apps, schema_editor):
    OldRefLgr = apps.get_model("lgr_models", "RefLgr")
    OldRefLgrMember = apps.get_model("lgr_models", "RefLgrMember")
    db_alias = schema_editor.connection.alias
    reflgr = OldRefLgr.objects.using(db_alias).first()
    OldRefLgrMember.objects.using(db_alias).all().update(ref_lgr=reflgr)


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('lgr_models', '0008_report_owner_nullable'),
    ]

    operations = [
        migrations.RenameModel('RefLgr', 'RefLgrMember'),
        migrations.CreateModel(
            name='RefLgr',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to=lgr_models.models.lgr.get_upload_path)),
                ('name', models.CharField(max_length=128, unique=True)),
                ('owner',
                 models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+',
                                   to=settings.AUTH_USER_MODEL)),
                ('active', models.BooleanField(default=True))
            ],
            options={
                'ordering': ['name'],
                'abstract': False,
            },
        ),
        migrations.RunPython(reflgr_initial_data),
        migrations.AddField(
            name='ref_lgr', model_name='reflgrmember',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='repository',
                                    to='lgr_models.reflgr', null=True)
        ),
        migrations.RunPython(reflgrmember_link_to_reflgr),
        migrations.AlterField(
            name='ref_lgr', model_name='reflgrmember',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='repository',
                                    to='lgr_models.reflgr', null=False),
            preserve_default=False
        )
    ]
