"""
URL patterns for bmexapp API v1
"""

from django.urls import path
from . import views

app_name = 'bmexapp'

urlpatterns = [
    # Health check
    path('health/', views.health_check, name='health'),

    # Models
    path('models/', views.list_models, name='list-models'),

    # Mass data queries
    path('masses/', views.query_masses, name='query-masses'),

    # Nuclei list
    path('nuclei/', views.list_nuclei, name='list-nuclei'),

    # Dropdown options
    path('dropdowns/<str:name>/', views.get_dropdown_options, name='dropdown-options'),

    # Analytics/series data
    path('analytics/series/', views.get_analytics_series, name='analytics-series'),
]
