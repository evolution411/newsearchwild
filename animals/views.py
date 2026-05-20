import json
import random
import requests
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.conf import settings
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


def send_subscription_welcome_email(email):
    if not settings.SUBSCRIPTION_WELCOME_EMAIL_ENABLED:
        return

    if not settings.EMAIL_HOST and "console.EmailBackend" not in settings.EMAIL_BACKEND:
        return

    signer = TimestampSigner()
    unsubscribe_token = signer.sign(email)
    unsubscribe_url = f"{settings.SITE_URL}/unsubscribe/?token={unsubscribe_token}"
    animals_url = f"{settings.SITE_URL}/animals/"
    categories_url = f"{settings.SITE_URL}/categories/"
    videos_url = f"{settings.SITE_URL}/videos/"

    subject = "Welcome to Search Wilds"
    text_content = (
        "Thanks for subscribing to Search Wilds.\n\n"
        "You'll now receive updates about wildlife facts, animals, and videos.\n\n"
        f"You're subscribed as: {email}\n\n"
        f"Explore animals: {animals_url}\n"
        f"Browse categories: {categories_url}\n"
        f"Watch videos: {videos_url}\n\n"
        f"Unsubscribe anytime: {unsubscribe_url}\n\n"
        "We’re glad to have you with us."
    )
    html_content = """
    <html>
      <body style="margin:0;padding:0;background:#f6f4ec;font-family:Arial,Helvetica,sans-serif;color:#163022;">
        <div style="max-width:640px;margin:0 auto;padding:32px 16px;">
          <div style="background:#ffffff;border-radius:24px;overflow:hidden;box-shadow:0 18px 50px rgba(12,32,21,0.12);">
            <div style="background:linear-gradient(135deg,#123524 0%,#1f6b3c 100%);padding:36px 32px;color:#ffffff;">
              <div style="font-size:13px;letter-spacing:0.18em;text-transform:uppercase;opacity:0.8;font-weight:700;">Search Wilds</div>
              <h1 style="margin:14px 0 10px;font-size:34px;line-height:1.05;font-family:Georgia,'Times New Roman',serif;">Welcome to the wild side</h1>
              <p style="margin:0;font-size:16px;line-height:1.7;max-width:460px;">
                Thanks for subscribing. You’re now on the list for wildlife facts, new animal highlights, and video updates.
              </p>
            </div>

            <div style="padding:32px;">
              <p style="margin:0 0 14px;font-size:14px;line-height:1.7;color:#6b7a71;">
                Subscription email: <strong style="color:#163022;">%s</strong>
              </p>
              <p style="margin:0 0 18px;font-size:16px;line-height:1.8;color:#32463a;">
                We’ll send you occasional updates about fascinating species, habitats around the world, and new content added to Search Wilds.
              </p>

              <div style="background:#eff6ef;border-radius:18px;padding:20px 22px;margin:0 0 24px;">
                <div style="font-size:14px;font-weight:700;color:#174f2d;margin-bottom:8px;">What you can explore now</div>
                <ul style="padding-left:18px;margin:0;color:#405246;line-height:1.8;font-size:15px;">
                  <li>Animal profiles and conservation facts</li>
                  <li>Wildlife location discovery by region</li>
                  <li>Short animal videos and visual highlights</li>
                </ul>
              </div>

              <div style="margin:0 0 24px;">
                <a href="%s" style="display:inline-block;background:#174f2d;color:#ffffff;text-decoration:none;font-weight:700;padding:14px 24px;border-radius:999px;margin:0 10px 10px 0;">
                  Explore Animals
                </a>
                <a href="%s" style="display:inline-block;background:#edf5ef;color:#174f2d;text-decoration:none;font-weight:700;padding:14px 24px;border-radius:999px;margin:0 10px 10px 0;border:1px solid #d7e6da;">
                  Browse Categories
                </a>
                <a href="%s" style="display:inline-block;background:#edf5ef;color:#174f2d;text-decoration:none;font-weight:700;padding:14px 24px;border-radius:999px;margin:0 10px 10px 0;border:1px solid #d7e6da;">
                  Watch Videos
                </a>
              </div>

              <p style="margin:28px 0 0;font-size:14px;line-height:1.7;color:#6b7a71;">
                Thanks for being part of the Search Wilds community.
              </p>
              <p style="margin:16px 0 0;font-size:13px;line-height:1.7;color:#7b877f;">
                If you no longer want these updates, you can
                <a href="%s" style="color:#174f2d;">unsubscribe here</a>.
              </p>
            </div>
          </div>
        </div>
      </body>
    </html>
    """ % (email, animals_url, categories_url, videos_url, unsubscribe_url)

    message = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[email],
    )
    message.attach_alternative(html_content, "text/html")
    message.send(fail_silently=False)


def sync_subscription_to_brevo(email):
    if not settings.BREVO_SYNC_ENABLED or not settings.BREVO_API_KEY:
        return

    payload = {
        "email": email,
        "emailBlacklisted": False,
        "updateEnabled": True,
    }

    if settings.BREVO_LIST_ID:
        try:
            payload["listIds"] = [int(settings.BREVO_LIST_ID)]
        except ValueError:
            raise ValueError("BREVO_LIST_ID must be a number.")

    response = requests.post(
        "https://api.brevo.com/v3/contacts",
        headers={
            "accept": "application/json",
            "api-key": settings.BREVO_API_KEY,
            "content-type": "application/json",
        },
        json=payload,
        timeout=20,
    )

    if response.status_code not in (200, 201, 204):
        raise RuntimeError(
            f"Brevo contact sync failed with status {response.status_code}: {response.text[:200]}"
        )


def sync_unsubscribe_to_brevo(email):
    if not settings.BREVO_SYNC_ENABLED or not settings.BREVO_API_KEY:
        return

    response = requests.put(
        f"https://api.brevo.com/v3/contacts/{email}",
        headers={
            "accept": "application/json",
            "api-key": settings.BREVO_API_KEY,
            "content-type": "application/json",
        },
        json={
            "emailBlacklisted": True,
        },
        timeout=20,
    )

    if response.status_code not in (200, 204):
        raise RuntimeError(
            f"Brevo unsubscribe sync failed with status {response.status_code}: {response.text[:200]}"
        )


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
        try:
            sync_subscription_to_brevo(email)
        except Exception:
            messages.warning(request, "Subscription saved, but Brevo sync could not be completed.")
            return redirect(next_url)

        try:
            send_subscription_welcome_email(email)
        except Exception:
            messages.warning(request, "Subscription saved, but the welcome email could not be sent.")
            return redirect(next_url)

        messages.success(request, "You have been subscribed for updates.")
    else:
        if not subscriber.is_active:
            subscriber.is_active = True
            subscriber.save(update_fields=["is_active"])
            try:
                sync_subscription_to_brevo(email)
            except Exception:
                messages.warning(request, "Your subscription was reactivated, but Brevo sync could not be completed.")
                return redirect(next_url)
            messages.success(request, "Your subscription has been reactivated.")
        else:
            messages.info(request, "That email is already subscribed.")

    return redirect(next_url)


def unsubscribe(request):
    token = request.GET.get("token", "")

    if not token:
        messages.error(request, "Missing unsubscribe token.")
        return redirect("animals:home")

    signer = TimestampSigner()

    try:
        email = signer.unsign(token, max_age=60 * 60 * 24 * 30)
    except (BadSignature, SignatureExpired):
        messages.error(request, "This unsubscribe link is invalid or has expired.")
        return redirect("animals:home")

    updated = NewsletterSubscriber.objects.filter(email=email, is_active=True).update(is_active=False)

    if updated:
        try:
            sync_unsubscribe_to_brevo(email)
        except Exception:
            messages.warning(request, "You were unsubscribed locally, but Brevo sync could not be completed.")
            return redirect("animals:home")

        messages.success(request, "You have been unsubscribed from Search Wilds updates.")
    else:
        messages.info(request, "That subscription is already inactive or no longer exists.")

    return redirect("animals:home")

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

    paginator = Paginator(animals, 15)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

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
        'animals': page_obj,
        'page_obj': page_obj,
        'animal_count': paginator.count,
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

    paginator = Paginator(videos, 8)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "animals/video_list.html", {
        "videos": page_obj,
        "page_obj": page_obj,
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
