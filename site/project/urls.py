from django.urls import path, include

from www import urls as www_urls


urlpatterns = [
    path("", include(www_urls)),
    path("unicorn/", include("django_unicorn.urls")),
]
