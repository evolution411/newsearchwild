from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("animals", "0012_zoo_and_seed_data"),
    ]

    operations = [
        migrations.AddField(
            model_name="zoo",
            name="image_url",
            field=models.URLField(blank=True, max_length=500),
        ),
    ]
