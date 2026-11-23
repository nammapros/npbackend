"""Group individual water tank services into 3 canonical services with size packages.

The 3 services in the Water Tank Cleaning category:
1. Overhead Water Tank Cleaning (sizes up to 1000L, 1000-3000L, 3000-6000L, 6000-10000L)
2. Overhead Concrete Water Tank Cleaning (sizes up to 1000L, 1000-3000L)
3. Underground Sump Cleaning (sizes up to 5000L, 5000-8000L, 8000-12000L, 12000-20000L)

Existing packages, prices, and coverage are moved to the new canonical services.
The individual size services are deactivated.
"""
from django.db import migrations

GROUPS = [
    {
        "slug": "overhead-water-tank-cleaning",
        "name": "Overhead Water Tank Cleaning",
        "summary": "Overhead water tank cleaning with sludge removal, scrubbing, and rinse. Pick your tank size.",
        "sort_order": 1,
        "sizes": [
            ("overhead-water-tank-cleaning-up-to-1000-litres", "Up to 1000 Litres", 77900, 90),
            ("overhead-water-tank-cleaning-1000-to-3000-litres", "1000 to 3000 Litres", 104900, 120),
            ("overhead-water-tank-cleaning-3000-to-6000-litres", "3000 to 6000 Litres", 144900, 150),
            ("overhead-water-tank-cleaning-6000-to-10000-litres", "6000 to 10000 Litres", 249900, 180),
        ],
    },
    {
        "slug": "overhead-concrete-water-tank-cleaning",
        "name": "Overhead Concrete Water Tank Cleaning",
        "summary": "Concrete overhead tank cleaning with intensive scrubbing and sludge removal. Pick your tank size.",
        "sort_order": 2,
        "sizes": [
            ("overhead-concrete-water-tank-cleaning-up-to-1000-l", "Up to 1000 Litres", 119900, 120),
            ("overhead-concrete-water-tank-cleaning-1000-to-3000", "1000 to 3000 Litres", 149900, 150),
        ],
    },
    {
        "slug": "underground-sump-cleaning",
        "name": "Underground Sump Cleaning",
        "summary": "Underground sump cleaning with deep sludge extraction and jet wash. Pick your sump size.",
        "sort_order": 3,
        "sizes": [
            ("underground-sump-cleaning-up-to-5000-litres", "Up to 5000 Litres", 139900, 150),
            ("underground-sump-cleaning-5000-to-8000-litres", "5000 to 8000 Litres", 189900, 180),
            ("underground-sump-cleaning-8000-to-12000-litres", "8000 to 12000 Litres", 234900, 210),
            ("underground-sump-cleaning-12000-to-20000-litres", "12000 to 20000 Litres", 389900, 240),
        ],
    },
]

COPY_FIELDS = [
    "description", "important_notes", "inclusions", "exclusions", "features", "faq_items",
    "process_steps", "brands", "cover_image", "landing_thumbnail", "popup_cover_image", "popup_content_image",
    "list_image", "cover_image_url", "landing_thumbnail_url", "popup_cover_image_url", "popup_content_image_url",
    "list_image_url", "show_in_app",
]


def group_water_tank_sizes(apps, schema_editor):
    Service = apps.get_model("catalog", "Service")
    Category = apps.get_model("catalog", "Category")
    ServicePackage = apps.get_model("catalog", "ServicePackage")
    ServiceCoverage = apps.get_model("locations", "ServiceCoverage")

    # The production monorepo migration may already have grouped these rows.
    # Avoid adding a second set of unpriced size packages on a later deploy from
    # this standalone backend repository.
    source_slugs = [size[0] for group in GROUPS for size in group["sizes"]]
    grouped_slugs = [group["slug"] for group in GROUPS]
    if (
        not Service.objects.filter(slug__in=source_slugs, is_active=True).exists()
        and all(ServicePackage.objects.filter(service__slug=slug).exists() for slug in grouped_slugs)
    ):
        return

    category = Category.objects.filter(slug="water-tank-cleaning").first()

    for grp in GROUPS:
        old_slugs = [s[0] for s in grp["sizes"]]
        old = {s.slug: s for s in Service.objects.filter(slug__in=old_slugs)}

        first = old.get(old_slugs[0]) or (next(iter(old.values())) if old else None)
        cat_id = (category.id if category else None) or (first.category_id if first else None)
        if not cat_id:
            continue

        new, created = Service.objects.get_or_create(
            slug=grp["slug"],
            defaults={
                "category_id": cat_id,
                "name": grp["name"],
                "summary": grp["summary"],
                "sort_order": grp["sort_order"],
                "is_active": True,
            },
        )
        if created and first:
            for field in COPY_FIELDS:
                if hasattr(first, field) and getattr(first, field) is not None:
                    setattr(new, field, getattr(first, field))
            new.summary = grp["summary"]
            new.is_popular = any(s.is_popular for s in old.values())
            new.is_featured = any(s.is_featured for s in old.values())
        else:
            new.name = grp["name"]
            new.summary = grp["summary"]
            new.sort_order = grp["sort_order"]
            new.is_active = True

        prices = []
        for slug, label, default_price, default_duration in grp["sizes"]:
            service = old.get(slug)
            if service is not None:
                pkgs = list(ServicePackage.objects.filter(service=service))
                if pkgs:
                    for package in pkgs:
                        package.service = new
                        package.name = label
                        package.save(update_fields=["service", "name"])
                        if package.base_price_paise:
                            prices.append(package.base_price_paise)
                else:
                    price = service.starting_price_paise or default_price
                    prices.append(price)
                    ServicePackage.objects.create(
                        service=new,
                        name=label,
                        base_price_paise=price,
                        pricing_model="FIXED_PRICE",
                        duration_minutes=default_duration,
                        is_active=True,
                    )
                if service.starting_price_paise:
                    prices.append(service.starting_price_paise)

                for coverage in ServiceCoverage.objects.filter(service=service):
                    row, made = ServiceCoverage.objects.get_or_create(
                        service=new, zone_id=coverage.zone_id, defaults={"is_active": coverage.is_active}
                    )
                    if not made and coverage.is_active and not row.is_active:
                        row.is_active = True
                        row.save(update_fields=["is_active"])

                service.is_active = False
                service.is_popular = False
                service.save(update_fields=["is_active", "is_popular"])
            else:
                # If old service doesn't exist yet, ensure package exists on new service
                pkg, p_created = ServicePackage.objects.get_or_create(
                    service=new,
                    name=label,
                    defaults={
                        "base_price_paise": default_price,
                        "pricing_model": "FIXED_PRICE",
                        "duration_minutes": default_duration,
                        "is_active": True,
                    },
                )
                prices.append(pkg.base_price_paise or default_price)

        if prices:
            new.starting_price_paise = min(prices)
        new.is_active = True
        new.save()


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0014_tv_installation_sizes"),
        ("locations", "0005_zone_country_zone_locality_aliases_and_more"),
    ]

    operations = [migrations.RunPython(group_water_tank_sizes, migrations.RunPython.noop)]
