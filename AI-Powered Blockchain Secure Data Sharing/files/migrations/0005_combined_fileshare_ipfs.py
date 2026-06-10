import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    """
    The files_fileshare table already exists in the database from a
    previously applied but untracked migration.  This migration SKIPS
    re-creating that table and only adds the two new fields:
      - File.ipfs_cid   (IPFS Content Identifier for online storage)
      - File.file_size  (original file size in bytes)
    and alters encrypted_file_path to allow blank values.
    """

    dependencies = [
        ('files', '0004_file_encryption_key'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [

        # IPFS CID field
        migrations.AddField(
            model_name='file',
            name='ipfs_cid',
            field=models.CharField(max_length=100, blank=True, null=True),
        ),

        # File size field
        migrations.AddField(
            model_name='file',
            name='file_size',
            field=models.PositiveBigIntegerField(default=0),
        ),

        # Allow encrypted_file_path to be blank (IPFS files have no local path)
        migrations.AlterField(
            model_name='file',
            name='encrypted_file_path',
            field=models.CharField(max_length=500, blank=True),
        ),
    ]