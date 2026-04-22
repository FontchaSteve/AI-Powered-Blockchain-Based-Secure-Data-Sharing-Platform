import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Combined migration — safe to run whether or not 0005_fileshare was
    previously applied.  Depends only on 0004_file_encryption_key which
    is confirmed to exist.

    Creates:
      - FileShare model
      - File.ipfs_cid   field (IPFS Content Identifier)
      - File.file_size  field (original file size in bytes)
      - Alters File.encrypted_file_path to allow blank (IPFS files have no local path)
    """

    dependencies = [
        ('files', '0004_file_encryption_key'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [

        # ── FileShare model ──────────────────────────────────────────────────
        migrations.CreateModel(
            name='FileShare',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True, primary_key=True,
                    serialize=False, verbose_name='ID'
                )),
                ('shared_at',    models.DateTimeField(default=django.utils.timezone.now)),
                ('expires_at',   models.DateTimeField(blank=True, null=True)),
                ('can_download', models.BooleanField(default=True)),
                ('file', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='shares',
                    to='files.file',
                )),
                ('shared_by', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='shares_given',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('shared_with', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='shares_received',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'ordering': ['-shared_at'],
                'unique_together': {('file', 'shared_with')},
            },
        ),

        # ── IPFS CID field ───────────────────────────────────────────────────
        migrations.AddField(
            model_name='file',
            name='ipfs_cid',
            field=models.CharField(max_length=100, blank=True, null=True),
        ),

        # ── File size field ──────────────────────────────────────────────────
        migrations.AddField(
            model_name='file',
            name='file_size',
            field=models.PositiveBigIntegerField(default=0),
        ),

        # ── Allow encrypted_file_path to be blank (IPFS files have no local path) ──
        migrations.AlterField(
            model_name='file',
            name='encrypted_file_path',
            field=models.CharField(max_length=500, blank=True),
        ),
    ]