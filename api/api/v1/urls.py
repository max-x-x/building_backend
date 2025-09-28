from django.urls import path

from api.api.v1.views.activation import ActivationRequestView, ActivationIkoCheckView
from api.api.v1.views.auth import AuthLoginView, AuthRefreshView, AuthInviteView, AuthLogoutView
from api.api.v1.views.foremen import ForemenListView
from api.api.v1.views.objects import ObjectsAssignForemanView, ObjectsListCreateView
from api.api.v1.views.prescriptions import (PrescriptionFixView, PrescriptionVerifyView,
                                            ViolationsListView, PrescriptionsDetailView,
                                            PrescriptionsCollectionView)
from api.api.v1.views.users import UsersMeView, UsersDetailView, UsersListCreateView
from api.api.v1.views.visits import (QrCreateView, VisitsDetailView, VisitRequestsView)
from api.api.v1.views.work_plans import WorkPlanCreateView

urlpatterns = [
    # AUTH
    path("auth/login",   AuthLoginView.as_view(),   name="auth-login"),
    path("auth/refresh", AuthRefreshView.as_view(), name="auth-refresh"),
    path("auth/invite",  AuthInviteView.as_view(),  name="auth-invite"),
    path("auth/logout",  AuthLogoutView.as_view(),  name="auth-logout"),

    # USERS
    path("users/me",           UsersMeView.as_view(),           name="users-me"),
    path("users/<uuid:id>",    UsersDetailView.as_view(),       name="users-detail"),
    path("users",              UsersListCreateView.as_view(),   name="users-list-create"),
    path("foremen",            ForemenListView.as_view(),       name="foremen-list"),

    # OBJECTS
    path("objects",                        ObjectsListCreateView.as_view(),  name="objects-list-create"),
    path("objects/<int:id>",               ObjectsAssignForemanView.as_view(), name="objects-detail"),  # привязка прораба
    path("objects/<int:id>/activation/request",   ActivationRequestView.as_view(), name="object-activation-request"),
    path("objects/<int:id>/activation/iko-check", ActivationIkoCheckView.as_view(), name="object-activation-iko-check"),

    # VISITS + QR
    path("visit-requests",            VisitRequestsView.as_view(),   name="visit-requests-collection"),  # GET+POST
    path("visit-requests/<int:id>",   VisitsDetailView.as_view(),    name="visit-requests-detail"),
    path("qr-codes",                  QrCreateView.as_view(),        name="qr-create"),

    # PRESCRIPTIONS
    path("prescriptions",                   PrescriptionsCollectionView.as_view(), name="prescriptions-collection"),  # GET+POST
    path("prescriptions/<int:id>",          PrescriptionsDetailView.as_view(),     name="prescriptions-detail"),
    path("prescriptions/<int:id>/fix",      PrescriptionFixView.as_view(),         name="prescriptions-fix"),
    path("prescriptions/<int:id>/verify",   PrescriptionVerifyView.as_view(),      name="prescriptions-verify"),

    # VIOLATIONS alias (без префикса api/v1)
    path("violations", ViolationsListView.as_view(), name="violations-list"),

    path("work-plans", WorkPlanCreateView.as_view(), name="work-plans-collection"),
]

