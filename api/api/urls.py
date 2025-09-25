from django.urls import include, path

urlpatterns = [
    path('v1/', include('api.api.v1.urls')),
]

