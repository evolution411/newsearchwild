from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class AnimalCategory(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = "Animal Categories"

    def __str__(self):
        return self.name



DIET_CHOICES = [
    ('Carnivore', 'Carnivore'),
    ('Herbivore', 'Herbivore'),
    ('Omnivore', 'Omnivore'),
    ('Insectivore', 'Insectivore'),
]


HABITAT_CHOICES = [
    ('Forest', 'Forest'),
    ('Ocean', 'Ocean'),
    ('Desert', 'Desert'),
    ('Grassland', 'Grassland'),
    ('Wetland', 'Wetland'),
    ('Mountain', 'Mountain'),
    ('Arctic', 'Arctic'),
]

class Animal(models.Model):
    CONSERVATION_CHOICES = [
        ('Least Concern', 'Least Concern'),
        ('Near Threatened', 'Near Threatened'),
        ('Vulnerable', 'Vulnerable'),
        ('Endangered', 'Endangered'),
        ('Critically Endangered', 'Critically Endangered'),
        ('Extinct in the Wild', 'Extinct in the Wild'),
        ('Extinct', 'Extinct'),
        ('Unknown', 'Unknown'),
    ]

    name = models.CharField(max_length=150)
    scientific_name = models.CharField(max_length=150, blank=True)

    category = models.ForeignKey(
        AnimalCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    image = models.ImageField(
        upload_to='animal_images/',
        blank=True,
        null=True
    )

    habitat = models.CharField(
        max_length=150,
        choices=HABITAT_CHOICES,
        blank=True
    )

    diet = models.CharField(
        max_length=150,
        choices=DIET_CHOICES,
        blank=True
    )


    lifespan = models.CharField(max_length=100, blank=True)
    size = models.CharField(max_length=100, blank=True)
    natural_enemies = models.JSONField(default=list, blank=True)

    conservation_status = models.CharField(
        max_length=50,
        choices=CONSERVATION_CHOICES,
        default='Unknown'
    )

    description = models.TextField(blank=True)
    fun_fact = models.TextField(blank=True)

    # Extra location fields for world map
    countries = models.JSONField(default=list, blank=True)
    map_points = models.JSONField(default=list, blank=True)

    # Wikipedia fields
    wiki_title = models.CharField(max_length=200, blank=True)
    wiki_summary = models.TextField(blank=True)
    wiki_image_url = models.URLField(max_length=500, blank=True)
    wiki_page_url = models.URLField(max_length=500, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    # countries = models.JSONField(default=list, blank=True)
	# map_points = models.JSONField(default=list, blank=True)
	# distribution_summary = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class PuzzleScore(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE)
    level = models.CharField(max_length=20)
    points = models.IntegerField(default=0)
    completed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.animal.name} - {self.points}"


class AnimalLocation(models.Model):
    animal = models.ForeignKey(
        Animal,
        on_delete=models.CASCADE,
        related_name='locations'
    )
    place_name = models.CharField(max_length=150)
    country = models.CharField(max_length=150, blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()

    def __str__(self):
        return f"{self.animal.name} - {self.place_name}"
        
class AnimalVideo(models.Model):
    PLATFORM_CHOICES = [
        ("youtube", "YouTube Shorts"),
        ("tiktok", "TikTok"),
    ]

    animal = models.ForeignKey(
        Animal,
        on_delete=models.CASCADE,
        related_name="videos",
        null=True,
        blank=True
    )

    category = models.ForeignKey(
        AnimalCategory,
        on_delete=models.SET_NULL,
        related_name="videos",
        null=True,
        blank=True
    )

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    platform = models.CharField(
        max_length=20,
        choices=PLATFORM_CHOICES
    )

    video_url = models.URLField(max_length=500)
    embed_url = models.URLField(max_length=500, blank=True)

    thumbnail_url = models.URLField(max_length=500, blank=True)

    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        from .utils import get_video_embed_url

        if self.video_url:
            self.embed_url = get_video_embed_url(self.platform, self.video_url)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
