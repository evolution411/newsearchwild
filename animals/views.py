import json
import random
from django.contrib import messages
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Animal, AnimalCategory, AnimalLocation,PuzzleScore, AnimalVideo, NewsletterSubscriber
from django.db.models import Q,Count,Avg
from django.http import JsonResponse


COUNTRY_CONTINENT = {
    # Africa
    "Kenya": "Africa",
    "Tanzania": "Africa",
    "Uganda": "Africa",
    "Zambia": "Africa",
    "South Africa": "Africa",
    "Madagascar": "Africa",
    "Botswana": "Africa",
    "Namibia": "Africa",
    "Ethiopia": "Africa",
    "Nigeria": "Africa",
    "Egypt": "Africa",

    # Asia
    "India": "Asia",
    "China": "Asia",
    "Indonesia": "Asia",
    "Japan": "Asia",
    "Thailand": "Asia",
    "Malaysia": "Asia",
    "Nepal": "Asia",
    "Russia": "Asia",

    # Europe
    "United Kingdom": "Europe",
    "France": "Europe",
    "Germany": "Europe",
    "Spain": "Europe",
    "Italy": "Europe",
    "Norway": "Europe",
    "Sweden": "Europe",

    # North America
    "United States": "North America",
    "Canada": "North America",
    "Mexico": "North America",

    # South America
    "Brazil": "South America",
    "Peru": "South America",
    "Colombia": "South America",
    "Argentina": "South America",
    "Chile": "South America",
    "Ecuador": "South America",

    # Oceania
    "Australia": "Oceania",
    "New Zealand": "Oceania",
    "Papua New Guinea": "Oceania",
}

COUNTRY_COORDS = {
    # Africa
    "Kenya": {"lat": -0.0236, "lng": 37.9062},
    "Tanzania": {"lat": -6.3690, "lng": 34.8888},
    "Uganda": {"lat": 1.3733, "lng": 32.2903},
    "Zambia": {"lat": -13.1339, "lng": 27.8493},
    "South Africa": {"lat": -30.5595, "lng": 22.9375},
    "Madagascar": {"lat": -18.7669, "lng": 46.8691},
    "Botswana": {"lat": -22.3285, "lng": 24.6849},
    "Namibia": {"lat": -22.9576, "lng": 18.4904},
    "Ethiopia": {"lat": 9.1450, "lng": 40.4897},
    "Nigeria": {"lat": 9.0820, "lng": 8.6753},
    "Egypt": {"lat": 26.8206, "lng": 30.8025},

    # Asia
    "India": {"lat": 20.5937, "lng": 78.9629},
    "China": {"lat": 35.8617, "lng": 104.1954},
    "Indonesia": {"lat": -0.7893, "lng": 113.9213},
    "Japan": {"lat": 36.2048, "lng": 138.2529},
    "Thailand": {"lat": 15.8700, "lng": 100.9925},
    "Malaysia": {"lat": 4.2105, "lng": 101.9758},
    "Nepal": {"lat": 28.3949, "lng": 84.1240},
    "Russia": {"lat": 61.5240, "lng": 105.3188},

    # Europe
    "United Kingdom": {"lat": 55.3781, "lng": -3.4360},
    "France": {"lat": 46.2276, "lng": 2.2137},
    "Germany": {"lat": 51.1657, "lng": 10.4515},
    "Spain": {"lat": 40.4637, "lng": -3.7492},
    "Italy": {"lat": 41.8719, "lng": 12.5674},
    "Norway": {"lat": 60.4720, "lng": 8.4689},
    "Sweden": {"lat": 60.1282, "lng": 18.6435},

    # North America
    "United States": {"lat": 37.0902, "lng": -95.7129},
    "Canada": {"lat": 56.1304, "lng": -106.3468},
    "Mexico": {"lat": 23.6345, "lng": -102.5528},

    # South America
    "Brazil": {"lat": -14.2350, "lng": -51.9253},
    "Peru": {"lat": -9.1900, "lng": -75.0152},
    "Colombia": {"lat": 4.5709, "lng": -74.2973},
    "Argentina": {"lat": -38.4161, "lng": -63.6167},
    "Chile": {"lat": -35.6751, "lng": -71.5430},
    "Ecuador": {"lat": -1.8312, "lng": -78.1834},

    # Oceania
    "Australia": {"lat": -25.2744, "lng": 133.7751},
    "New Zealand": {"lat": -40.9006, "lng": 174.8860},
    "Papua New Guinea": {"lat": -6.3150, "lng": 143.9555},
}

def puzzle_game_home(request):
    animals = list(
        Animal.objects.filter(
            Q(image__isnull=False) | Q(wiki_image_url__gt="")
        )
    )

    random_animals = random.sample(animals, min(len(animals), 10))

    return render(request, "animals/puzzle_game_home.html", {
        "animals": random_animals,
    })

def puzzle_game(request, animal_id):
    animal = get_object_or_404(Animal, id=animal_id)

    return render(request, "animals/puzzle_game.html", {
        "animal": animal,
    })


# @login_required
# def save_puzzle_score(request):
#     if request.method == 'POST':
#         animal_id = request.POST.get('animal_id')
#         level = request.POST.get('level')
#         points = int(request.POST.get('points', 0))

#         animal = get_object_or_404(Animal, id=animal_id)

#         PuzzleScore.objects.create(
#             user=request.user,
#             animal=animal,
#             level=level,
#             points=points
#         )

#         return JsonResponse({'success': True})

#     return JsonResponse({'success': False})

def get_country_coordinates(country_name, fallback_latitude=None, fallback_longitude=None):
    coords = COUNTRY_COORDS.get(country_name)

    if coords:
        return coords["lat"], coords["lng"]

    return fallback_latitude, fallback_longitude

def get_continent_for_country(country):
    return COUNTRY_CONTINENT.get(country, "Other")


def subscribe(request):
    if request.method != "POST":
        return redirect("animals:home")

    email = (request.POST.get("email") or "").strip().lower()
    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER") or "/"

    try:
        validate_email(email)
    except ValidationError:
        messages.error(request, "Please enter a valid email address.")
        return redirect(next_url)

    subscriber, created = NewsletterSubscriber.objects.get_or_create(
        email=email,
        defaults={"is_active": True},
    )

    if created:
        messages.success(request, "You have been subscribed for updates.")
    else:
        if not subscriber.is_active:
            subscriber.is_active = True
            subscriber.save(update_fields=["is_active"])
            messages.success(request, "Your subscription has been reactivated.")
        else:
            messages.info(request, "That email is already subscribed.")

    return redirect(next_url)

def home(request):
    categories = AnimalCategory.objects.all()
    animals = Animal.objects.all()[:12]


    category_cards = []
    for category in categories:
        sample_animal = Animal.objects.filter(category=category).first()

        category_cards.append({
            'category': category,
            'sample_animal': sample_animal,
        })

    recent_animals = Animal.objects.order_by('-created_at')[:10]
    featured_animals = Animal.objects.all()[:6]

    total_animals = Animal.objects.count()
    total_categories = AnimalCategory.objects.count()

    # featured_videos = AnimalVideo.objects.filter(is_active=True
    # ).order_by("-is_featured", "-created_at")[:4]

    recent_videos = AnimalVideo.objects.filter(
        is_active=True
    ).order_by("-created_at")[:4]

    return render(request, 'animals/home.html', {
        'category_cards': category_cards,
        'recent_animals': recent_animals,
        'featured_animals': featured_animals,
        'total_animals': total_animals,
        'total_categories': total_categories,
        "recent_videos": recent_videos,
    })

def animal_list(request):
    animals = Animal.objects.all()
    categories = AnimalCategory.objects.all()

    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    diet = request.GET.get('diet', '')
    habitat = request.GET.get('habitat', '')
    place = request.GET.get('place', '')
    status = request.GET.get('status', '')
    sort = request.GET.get('sort', '')

    if query:
        animals = animals.filter(
            Q(name__icontains=query) |
            Q(scientific_name__icontains=query) |
            Q(habitat__icontains=query) |
            Q(diet__icontains=query) |
            Q(locations__place_name__icontains=query) |
            Q(locations__country__icontains=query)
        ).distinct()

    if category_id:
        animals = animals.filter(category_id=category_id)

    if diet:
        animals = animals.filter(diet__icontains=diet)

    if habitat:
        animals = animals.filter(habitat__icontains=habitat)

    if place:
        animals = animals.filter(
            Q(locations__place_name__icontains=place) |
            Q(locations__country__icontains=place)
        ).distinct()

    if status:
        animals = animals.filter(conservation_status=status)

    if sort == 'name_az':
        animals = animals.order_by('name')
    elif sort == 'name_za':
        animals = animals.order_by('-name')
    elif sort == 'newest':
        animals = animals.order_by('-created_at')
    elif sort == 'oldest':
        animals = animals.order_by('created_at')

    conservation_statuses = [
        'Least Concern',
        'Near Threatened',
        'Vulnerable',
        'Endangered',
        'Critically Endangered',
        'Extinct in the Wild',
        'Extinct',
        'Unknown',
    ]

    return render(request, 'animals/animal_list.html', {
        'animals': animals,
        'categories': categories,
        'conservation_statuses': conservation_statuses,
        'query': query,
        'selected_category': category_id,
        'selected_diet': diet,
        'selected_habitat': habitat,
        'selected_place': place,
        'selected_status': status,
        'selected_sort': sort,
    })

def category_list(request):
    categories = AnimalCategory.objects.annotate(
        animal_count=Count('animal')
    ).order_by('name')

    category_cards = []

    for category in categories:
        sample_animal = Animal.objects.filter(category=category).first()

        category_cards.append({
            'category': category,
            'sample_animal': sample_animal,
        })

    return render(request, 'animals/category_list.html', {
        'category_cards': category_cards,
    })

def video_list(request):
    videos = AnimalVideo.objects.filter(is_active=True)

    platform = request.GET.get("platform")

    if platform in ["youtube", "tiktok"]:
        videos = videos.filter(platform=platform)

    return render(request, "animals/video_list.html", {
        "videos": videos,
        "platform": platform,
    })

def animal_detail(request, animal_id):
    animal = get_object_or_404(Animal, id=animal_id)
    videos = animal.videos.filter(is_active=True)

    locations = animal.locations.all()


    location_data = [
        {
            "place_name": location.place_name,
            "country": location.country,
            "latitude": location.latitude,
            "longitude": location.longitude,
        }
        for location in locations
    ]
    # map_locations = [
    #     {
    #         "place_name": location.place_name,
    #         "country": location.country,
    #         "latitude": location.latitude,
    #         "longitude": location.longitude,
    #     }
    #     for location in locations
    # ]

    return render(request, 'animals/animal_detail.html', {
        'animal': animal,
        'locations':locations,
        'videos': videos,
        "location_data": location_data,
    })

def place_search(request):
    selected_continent = request.GET.get("continent", "Africa")
    selected_country = request.GET.get("country", "")
    place_query = request.GET.get("place", "")
    sort = request.GET.get("sort", "name_az")

    continents = [
        "Africa",
        "Asia",
        "Europe",
        "North America",
        "South America",
        "Oceania",
    ]

    all_country_data = (
        AnimalLocation.objects
        .exclude(country="")
        .values("country")
        .annotate(
            animal_count=Count("animal", distinct=True),
            latitude=Avg("latitude"),
            longitude=Avg("longitude"),
        )
        .order_by("country")
    )

    country_cards = []

    for item in all_country_data:
        country_name = item["country"]
        continent_name = get_continent_for_country(country_name)

        latitude, longitude = get_country_coordinates(
            country_name,
            item["latitude"],
            item["longitude"]
        )

        country_cards.append({
            "country": country_name,
            "continent": continent_name,
            "animal_count": item["animal_count"],
            "latitude": latitude,
            "longitude": longitude,
        })

    countries_in_continent = [
        item for item in country_cards
        if item["continent"] == selected_continent
    ]

    # If user searches a place
    if place_query:
        animals = Animal.objects.filter(
            Q(locations__place_name__icontains=place_query) |
            Q(locations__country__icontains=place_query)
        ).distinct()

        selected_place_label = place_query

        matching_locations = (
            AnimalLocation.objects
            .filter(
                Q(place_name__icontains=place_query) |
                Q(country__icontains=place_query)
            )
            .values("place_name", "country", "latitude", "longitude")
            .annotate(animal_count=Count("animal", distinct=True))
        )

        map_points = []

        for location in matching_locations:
            map_points.append({
                "name": location["place_name"] or location["country"],
                "country": location["country"],
                "animal_count": location["animal_count"],
                "latitude": location["latitude"],
                "longitude": location["longitude"],
            })

    # If user clicks a country
    elif selected_country:
        animals = Animal.objects.filter(
            Q(locations__country__icontains=selected_country) |
            Q(locations__place_name__icontains=selected_country)
        ).distinct()

        selected_place_label = selected_country

        map_points = [
            item for item in country_cards
            if item["country"] == selected_country
        ]

    # Default: continent selected
    else:
        country_names = [item["country"] for item in countries_in_continent]

        animals = Animal.objects.filter(
            locations__country__in=country_names
        ).distinct()

        selected_place_label = selected_continent
        map_points = countries_in_continent

    if sort == "name_az":
        animals = animals.order_by("name")
    elif sort == "name_za":
        animals = animals.order_by("-name")
    elif sort == "newest":
        animals = animals.order_by("-created_at")

    return render(request, "animals/place_search.html", {
        "animals": animals,
        "continents": continents,
        "selected_continent": selected_continent,
        "selected_country": selected_country,
        "selected_place_label": selected_place_label,
        "place_query": place_query,
        "sort": sort,
        "countries_in_continent": countries_in_continent,
        "map_countries_json": json.dumps(map_points),
    })
