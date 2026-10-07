from django.conf import settings

from base.context_processors import white_labelling_company


def branding(request):
    """Keep Horilla's optional company branding, with BOBAI as the default."""
    company_branding = white_labelling_company(request)
    if not company_branding["white_label_company"]:
        company_branding["white_label_company_name"] = settings.BRAND_NAME
    return {
        **company_branding,
        "brand_name": settings.BRAND_NAME,
        "brand_logo": settings.BRAND_LOGO,
    }
