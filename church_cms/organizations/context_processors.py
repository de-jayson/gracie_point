from organizations.models import Church

def organization_context(request):
    if request.user.is_authenticated:
        return {
            "church": request.user.church
        }

    return {
        "church": None
    }