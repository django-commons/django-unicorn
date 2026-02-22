from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from example.unicorn.components.hello_world import HelloWorldView


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("example.www.urls")),
    # Include django-unicorn urls
    path("unicorn/", include("django_unicorn.urls")),
    path("test", HelloWorldView.as_view(), name="test"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
