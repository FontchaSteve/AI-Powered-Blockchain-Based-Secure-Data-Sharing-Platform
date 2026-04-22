from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        # Chain after the FileShare migration (0005)
        ('files', '0005_fileshare'),
    ]

    operations = [
        # IPFS Content Identifier — null means file is stored locally
        migrations.AddField(
            model_name='file',
            name='ipfs_cid',
            field=models.CharField(max_length=100, blank=True, null=True),
        ),
        # Original file size in bytes for display
        migrations.AddField(
            model_name='file',
            name='file_size',
            field=models.PositiveBigIntegerField(default=0),
        ),
        # Make encrypted_file_path optional (blank=True) since IPFS files won't have a local path
        migrations.AlterField(
            model_name='file',
            name='encrypted_file_path',
            field=models.CharField(max_length=500, blank=True),
        ),
    ]