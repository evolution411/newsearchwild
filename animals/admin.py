from django.contrib import admin
from .models import Animal, AnimalCategory, AnimalLocation, AnimalVideo, NewsletterSubscriber
from .wiki_api import fetch_wikipedia_summary


@admin.register(AnimalCategory)
class AnimalCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)


class AnimalLocationInline(admin.TabularInline):
    model = AnimalLocation
    extra = 1


@admin.register(Animal)
class AnimalAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'scientific_name',
        'category',
        'conservation_status',
        'wiki_title',
    )

    list_filter = ('category', 'conservation_status', 'diet', 'habitat')
    search_fields = ('name', 'scientific_name', 'habitat', 'diet', 'wiki_title')
    actions = ['fetch_wikipedia_info']
    inlines = [AnimalLocationInline]

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'name',
                'scientific_name',
                'category',
                'image',
                'habitat',
                'diet',
                'lifespan',
                'size',
                'conservation_status',
            )
        }),
        ('Manual Content', {
            'fields': (
                'description',
                'fun_fact',
            )
        }),
        ('Wikipedia Data', {
            'fields': (
                'wiki_title',
                'wiki_summary',
                'wiki_image_url',
                'wiki_page_url',
            )
        }),
    )

    @admin.action(description='Fetch animal info from Wikipedia')
    def fetch_wikipedia_info(self, request, queryset):
        updated = 0
        failed = 0

        for animal in queryset:
            search_title = animal.wiki_title or animal.name
            wiki_data = fetch_wikipedia_summary(search_title)

            if wiki_data:
                animal.wiki_title = wiki_data["title"]
                animal.wiki_summary = wiki_data["summary"]
                animal.wiki_image_url = wiki_data["image_url"]
                animal.wiki_page_url = wiki_data["page_url"]

                if not animal.description:
                    animal.description = wiki_data["summary"]

                animal.save()
                updated += 1
            else:
                failed += 1

        self.message_user(
            request,
            f"Wikipedia update complete. Updated: {updated}. Failed: {failed}."
        )
        
@admin.register(AnimalVideo)
class AnimalVideoAdmin(admin.ModelAdmin):
    list_display = ("title", "platform", "animal", "category", "is_featured", "is_active", "created_at")
    list_filter = ("platform", "is_featured", "is_active", "category")
    search_fields = ("title", "description", "animal__name", "category__name")

@admin.register(AnimalLocation)
class AnimalLocationAdmin(admin.ModelAdmin):
    list_display = ('animal', 'place_name', 'country', 'latitude', 'longitude')
    search_fields = ('animal__name', 'place_name', 'country')


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ("email", "is_active", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("email",)
