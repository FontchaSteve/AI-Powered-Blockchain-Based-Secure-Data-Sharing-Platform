from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Adds download_count to the File model.
    Chains after 0006_fileshare which is the last confirmed migration.
    """

    dependencies = [
        ('files', '0006_fileshare'),
    ]

    operations = [
        migrations.AddField(
            model_name='file',
            name='download_count',
            field=models.PositiveIntegerField(default=0),
        ),
    ]