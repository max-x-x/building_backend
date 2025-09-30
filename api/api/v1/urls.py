from django.urls import path

from api.api.v1.views.activation import ActivationRequestView, ActivationIkoCheckView
from api.api.v1.views.auth import (AuthLoginView, AuthRefreshView, AuthLogoutView,
                                   AuthRegisterByInviteView)
from api.api.v1.views.daily_checklists import DailyChecklistsView, DailyChecklistReviewView
from api.api.v1.views.deliveries import (DeliveriesCreateView, DeliveryReceiveView, DeliveriesListView,
                                         InvoicesCreateView, DeliverySetStatusView,
                                         LabOrdersCreateView)
from api.api.v1.views.documents import DocumentsListView, ExecDocsView
from api.api.v1.views.foremen import ForemenListView
from api.api.v1.views.health import PingView
from api.api.v1.views.memos import MemosView
from api.api.v1.views.objects import (ObjectsListCreateView, ObjectsDetailView,
                                      ObjectSuspendView, ObjectResumeView, ObjectCompleteView)
from api.api.v1.views.prescriptions import (PrescriptionFixView, PrescriptionVerifyView,
                                            ViolationsListView, PrescriptionsDetailView,
                                            PrescriptionsCollectionView)
 # from api.api.v1.views.tickets import TicketsView, TicketSetStatusView  # disabled: admin panel tickets external
from api.api.v1.views.users import UsersMeView, UsersDetailView, UsersListCreateView
# from api.api.v1.views.visits import (QrCreateView, VisitsDetailView, VisitRequestsView)  # disabled: visits/qr external
from api.api.v1.views.work_plans import (WorkPlanCreateView, WorkPlanDetailView, WorkPlansListView,
                                         WorkPlanAddVersionView, WorkPlanRequestChangeView, WorkPlanApproveChangeView,
                                         WorkItemSetStatusView)
from api.api.v1.views.areas import AreasCreateView, AreasDetailView, AreasListView
from api.api.v1.views.works import WorksListView, WorkCreateView

urlpatterns = [
    # AUTH
    path("auth/login",   AuthLoginView.as_view(),   name="auth-login"),
    path("auth/refresh", AuthRefreshView.as_view(), name="auth-refresh"),
    # path("auth/invite",  AuthInviteView.as_view(),  name="auth-invite"),  # disabled: invites handled externally
    path("auth/logout",  AuthLogoutView.as_view(),  name="auth-logout"),
    path("auth/register-by-invite", AuthRegisterByInviteView.as_view(), name="auth-register-by-invite"),

    # USERS
    path("users/me",           UsersMeView.as_view(),           name="users-me"),
    path("users/<uuid:id>",    UsersDetailView.as_view(),       name="users-detail"),
    path("users",              UsersListCreateView.as_view(),   name="users-list-create"),
    path("foremen",            ForemenListView.as_view(),       name="foremen-list"),

    # OBJECTS
    path("objects",              ObjectsListCreateView.as_view(), name="objects-list-create"),
    path("objects/<int:id>",     ObjectsDetailView.as_view(),     name="objects-detail"),

    path("objects/<int:id>/activation/request",   ActivationRequestView.as_view(), name="object-activation-request"),
    path("objects/<int:id>/activation/iko-check", ActivationIkoCheckView.as_view(), name="object-activation-iko-check"),

    path("objects/<int:id>/suspend",  ObjectSuspendView.as_view(),  name="object-suspend"),
    path("objects/<int:id>/resume",   ObjectResumeView.as_view(),   name="object-resume"),
    path("objects/<int:id>/complete", ObjectCompleteView.as_view(), name="object-complete"),

    # VISITS + QR (disabled, handled by external service)
    # path("visit-requests",            VisitRequestsView.as_view(),   name="visit-requests-collection"),  # GET+POST
    # path("visit-requests/<int:id>",   VisitsDetailView.as_view(),    name="visit-requests-detail"),
    # path("qr-codes",                  QrCreateView.as_view(),        name="qr-create"),

    # PRESCRIPTIONS
    path("prescriptions",                   PrescriptionsCollectionView.as_view(), name="prescriptions-collection"),  # GET+POST
    path("prescriptions/<int:id>",          PrescriptionsDetailView.as_view(),     name="prescriptions-detail"),
    path("prescriptions/<int:id>/fix",      PrescriptionFixView.as_view(),         name="prescriptions-fix"),
    path("prescriptions/<int:id>/verify",   PrescriptionVerifyView.as_view(),      name="prescriptions-verify"),

    # VIOLATIONS alias (без префикса api/v1)
    path("violations", ViolationsListView.as_view(), name="violations-list"),

    path("work-plans", WorkPlanCreateView.as_view(), name="work-plans-collection"),

    # DOCUMENTS
    path("documents", DocumentsListView.as_view(), name="documents-list"),
    path("exec-docs", ExecDocsView.as_view(), name="exec-docs"),

    # WORK PLANS extended
    path("work-plans/<int:id>", WorkPlanDetailView.as_view(), name="work-plan-detail"),
    path("work-plans/list", WorkPlansListView.as_view(), name="work-plans-list"),
    path("work-plans/<int:id>/versions", WorkPlanAddVersionView.as_view(), name="work-plan-add-version"),
    path("work-plans/<int:id>/request-change", WorkPlanRequestChangeView.as_view(), name="work-plan-request-change"),
    path("work-plans/<int:id>/approve-change", WorkPlanApproveChangeView.as_view(), name="work-plan-approve-change"),
    path("work-items/<int:id>/status", WorkItemSetStatusView.as_view(), name="work-item-set-status"),

    # DAILY CHECKLISTS
    path("daily-checklists", DailyChecklistsView.as_view(), name="daily-checklists"),
    path("daily-checklists/<uuid:id>/review", DailyChecklistReviewView.as_view(), name="daily-checklist-review"),

    # DELIVERIES / INVOICES / LABS
    path("deliveries", DeliveriesCreateView.as_view(), name="deliveries-create"),
    path("deliveries/<int:id>", DeliveryReceiveView.as_view(), name="delivery-receive"),
    path("deliveries/list", DeliveriesListView.as_view(), name="deliveries-list"),
    path("invoices", InvoicesCreateView.as_view(), name="invoices-create"),
    # path("invoices/<int:id>/parse-ttn", InvoiceParseTTNView.as_view(), name="invoice-parse-ttn"),  # disabled: CV external
    path("deliveries/<int:id>/status", DeliverySetStatusView.as_view(), name="deliveries-set-status"),
    path("labs/orders", LabOrdersCreateView.as_view(), name="labs-orders-create"),

    # WORKS
    path("works", WorksListView.as_view(), name="works-list"),
    path("works/create", WorkCreateView.as_view(), name="works-create"),

    # MEMOS
    path("memos", MemosView.as_view(), name="memos"),

    # TICKETS (disabled: admin panel external)
    # path("tickets", TicketsView.as_view(), name="tickets"),
    # path("tickets/<uuid:id>/status", TicketSetStatusView.as_view(), name="ticket-set-status"),

    # AREAS / POLYGONS
    path("areas", AreasCreateView.as_view(), name="areas-create"),
    path("areas/<int:id>", AreasDetailView.as_view(), name="areas-detail"),
    path("areas/list", AreasListView.as_view(), name="areas-list"),

    path("ping", PingView.as_view(), name="ping"),
]

