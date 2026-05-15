from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("animals", "0009_animalvideo"),
    ]

    operations = [
        migrations.AlterField(
            model_name="animal",
            name="wiki_image_url",
            field=models.URLField(blank=True, max_length=500),
        ),
        migrations.AlterField(
            model_name="animal",
            name="wiki_page_url",
            field=models.URLField(blank=True, max_length=500),
        ),
        migrations.AlterField(
            model_name="animalvideo",
            name="embed_url",
            field=models.URLField(blank=True, max_length=500),
        ),
        migrations.AlterField(
            model_name="animalvideo",
            name="thumbnail_url",
            field=models.URLField(blank=True, max_length=500),
        ),
        migrations.AlterField(
            model_name="animalvideo",
            name="video_url",
            field=models.URLField(max_length=500),
        ),
    ]
