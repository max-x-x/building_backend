from django.urls import path

from api.api.v1.views.auth import AuthLoginView, AuthRefreshView, AuthInviteView, AuthLogoutView
from api.api.v1.views.users import UsersMeView, UsersDetailView, UsersListCreateView

urlpatterns = [
    # AUTH
    path("auth/login", AuthLoginView.as_view()),
    path("auth/refresh", AuthRefreshView.as_view()),
    path("auth/invite", AuthInviteView.as_view()),
    path("auth/logout", AuthLogoutView.as_view()),
    # USERS
    path("users/me", UsersMeView.as_view()),
    path("users/<uuid:id>", UsersDetailView.as_view()),
    path("users", UsersListCreateView.as_view()),
]

