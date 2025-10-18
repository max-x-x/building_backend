from django.urls import path

from api.api.v1.views.activation import ActivationRequestView, ActivationIkoCheckView, ActivationChecklistView
from api.api.v1.views.auth import (AuthLoginView, AuthRefreshView, AuthLogoutView,
                                   AuthRegisterByInviteView)
from api.api.v1.views.daily_checklists import DailyChecklistsView, DailyChecklistReviewView, ObjectDailyChecklistsView
from api.api.v1.views.deliveries import (DeliveriesCreateView, DeliveryReceiveView, DeliveriesListView,
                                         InvoicesCreateView, DeliverySetStatusView,
                                         LabOrdersCreateView, InvoiceDataReceiveView, DeliveryConfirmView,
                                         DeliveryDetailView)
from api.api.v1.views.documents import DocumentsListView, ExecDocsView
from api.api.v1.views.foremen import ForemenListView
from api.api.v1.views.health import PingView
from api.api.v1.views.memos import MemosView
from api.api.v1.views.objects import (ObjectsListCreateView, ObjectsDetailView,
                                    ObjectSuspendView, ObjectResumeView, ObjectCompleteBySSKView, ObjectCompleteView,
                                    ObjectFullDetailView)
from api.api.v1.views.prescriptions import (PrescriptionFixView, PrescriptionVerifyView,
                                            ViolationsListView, PrescriptionsDetailView,
                                            PrescriptionsCollectionView)
from api.api.v1.views.users import UsersMeView, UsersDetailView, UsersListCreateView
from api.api.v1.views.work_plans import (WorkPlanCreateView, WorkPlanDetailView, WorkPlansListView,
                                         WorkPlanAddVersionView, WorkPlanRequestChangeView, WorkPlanApproveChangeView,
                                         WorkItemSetStatusView, WorkItemDetailView, WorkPlanChangeRequestView,
                                         WorkPlanChangeDecisionView, WorkPlanChangeRequestsListView)
from api.api.v1.views.areas import AreasCreateView, AreasDetailView, AreasListView, SubAreasCreateView
from api.api.v1.views.works import WorksListView, WorkCreateView
from api.api.v1.views.admin import AdminStatsView
from api.api.v1.views.logs import LogsListView, LogsStatsView

urlpatterns = [
    path("auth/login",   AuthLoginView.as_view(),   name="auth-login"),
    path("auth/refresh", AuthRefreshView.as_view(), name="auth-refresh"),
    path("auth/logout",  AuthLogoutView.as_view(),  name="auth-logout"),
    path("auth/register-by-invite", AuthRegisterByInviteView.as_view(), name="auth-register-by-invite"),

    path("users/me",           UsersMeView.as_view(),           name="users-me"),
    path("users/<uuid:id>",    UsersDetailView.as_view(),       name="users-detail"),
    path("users",              UsersListCreateView.as_view(),   name="users-list-create"),
    path("foremen",            ForemenListView.as_view(),       name="foremen-list"),

    path("objects",              ObjectsListCreateView.as_view(), name="objects-list-create"),
    path("objects/<int:id>",     ObjectsDetailView.as_view(),     name="objects-detail"),
    path("objects/<int:id>/full", ObjectFullDetailView.as_view(), name="objects-full-detail"),

    path("objects/<int:id>/activation/request",   ActivationRequestView.as_view(), name="object-activation-request"),
    path("objects/<int:id>/activation/iko-check", ActivationIkoCheckView.as_view(), name="object-activation-iko-check"),
    path("objects/<int:id>/activation/checklist", ActivationChecklistView.as_view(), name="object-activation-checklist"),

    path("objects/<int:id>/suspend",  ObjectSuspendView.as_view(),  name="object-suspend"),
    path("objects/<int:id>/resume",   ObjectResumeView.as_view(),   name="object-resume"),
    path("objects/<int:id>/complete-by-ssk", ObjectCompleteBySSKView.as_view(), name="object-complete-by-ssk"),
    path("objects/<int:id>/complete", ObjectCompleteView.as_view(), name="object-complete"),

    path("prescriptions",                   PrescriptionsCollectionView.as_view(), name="prescriptions-collection"),  # GET+POST
    path("prescriptions/<int:id>",          PrescriptionsDetailView.as_view(),     name="prescriptions-detail"),
    path("prescriptions/<int:id>/fix",      PrescriptionFixView.as_view(),         name="prescriptions-fix"),
    path("prescriptions/<int:id>/verify",   PrescriptionVerifyView.as_view(),      name="prescriptions-verify"),

    path("violations", ViolationsListView.as_view(), name="violations-list"),

    path("work-plans", WorkPlanCreateView.as_view(), name="work-plans-collection"),

    path("documents", DocumentsListView.as_view(), name="documents-list"),
    path("exec-docs", ExecDocsView.as_view(), name="exec-docs"),

    path("work-plans/<int:id>", WorkPlanDetailView.as_view(), name="work-plan-detail"),
    path("work-plans/list", WorkPlansListView.as_view(), name="work-plans-list"),
    path("work-plans/<int:id>/versions", WorkPlanAddVersionView.as_view(), name="work-plan-add-version"),
    path("work-plans/<int:id>/request-change", WorkPlanRequestChangeView.as_view(), name="work-plan-request-change"),
    path("work-plans/<int:id>/approve-change", WorkPlanApproveChangeView.as_view(), name="work-plan-approve-change"),
    path("work-items/<int:id>/status", WorkItemSetStatusView.as_view(), name="work-item-set-status"),
    path("work-items/<int:id>", WorkItemDetailView.as_view(), name="work-item-detail"),
    
    path("work-plans/change-request", WorkPlanChangeRequestView.as_view(), name="work-plan-change-request"),
    path("work-plans/change-requests", WorkPlanChangeRequestsListView.as_view(), name="work-plan-change-requests-list"),
    path("work-plans/change-requests/<int:change_request_id>/decision", WorkPlanChangeDecisionView.as_view(), name="work-plan-change-decision"),

    path("daily-checklists",         DailyChecklistsView.as_view(),         name="daily-checklists"),
    path("daily-checklists/<int:id>/review", DailyChecklistReviewView.as_view(), name="daily-checklist-review"),
    path("objects/<int:id>/daily-checklists", ObjectDailyChecklistsView.as_view(), name="object-daily-checklists"),

    path("deliveries", DeliveriesCreateView.as_view(), name="deliveries-create"),
    path("deliveries/<int:id>", DeliveryDetailView.as_view(), name="delivery-detail"),
    path("deliveries/<int:id>/receive", DeliveryReceiveView.as_view(), name="delivery-receive"),
    path("deliveries/list", DeliveriesListView.as_view(), name="deliveries-list"),
    path("deliveries/<int:id>/confirm", DeliveryConfirmView.as_view(), name="delivery-confirm"),
    path("invoices", InvoicesCreateView.as_view(), name="invoices-create"),
    path("invoices/data", InvoiceDataReceiveView.as_view(), name="invoices-data-receive"),
    path("deliveries/<int:id>/status", DeliverySetStatusView.as_view(), name="deliveries-set-status"),
    path("labs/orders", LabOrdersCreateView.as_view(), name="labs-orders-create"),

    path("works", WorksListView.as_view(), name="works-list"),
    path("works/create", WorkCreateView.as_view(), name="works-create"),

    path("memos", MemosView.as_view(), name="memos"),

    path("areas", AreasCreateView.as_view(), name="areas-create"),
    path("areas/<int:id>", AreasDetailView.as_view(), name="areas-detail"),
    path("areas/list", AreasListView.as_view(), name="areas-list"),
    path("sub-areas", SubAreasCreateView.as_view(), name="sub-areas-create"),

    path("admin/stats", AdminStatsView.as_view(), name="admin-stats"),

    path("logs", LogsListView.as_view(), name="logs-list"),
    path("logs/stats", LogsStatsView.as_view(), name="logs-stats"),

    path("ping", PingView.as_view(), name="ping"),
]

