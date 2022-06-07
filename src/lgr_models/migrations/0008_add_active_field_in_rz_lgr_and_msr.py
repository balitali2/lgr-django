# Generated by Django 3.1.7 on 2022-05-13 15:31

from django.db import migrations, models

from lgr_models.models.lgr import RzLgr, MSR


def set_default(apps, schema_editor):
    OldRzLgr: RzLgr = apps.get_model("lgr_models", "RzLgr")
    OldMsr: MSR = apps.get_model("lgr_models", "MSR")

    last_rz: RzLgr = OldRzLgr.objects.last()
    last_rz.active = True
    last_rz.save(update_fields=['active'])
    last_msr: MSR = OldMsr.objects.last()
    last_msr.active = True
    last_msr.save(update_fields=['active'])


class Migration(migrations.Migration):
    dependencies = [
        ('lgr_models', '0007_populate_unicode_versions'),
    ]

    operations = [
        migrations.AddField(
            model_name='msr',
            name='active',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='rzlgr',
            name='active',
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(set_default)
    ]
