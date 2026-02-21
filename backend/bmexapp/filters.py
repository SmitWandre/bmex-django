"""
DRF filters for BMEX Masses API
"""

from django_filters import rest_framework as filters


class MassDataFilter(filters.FilterSet):
    """
    Filter for mass data queries.
    Supports filtering by Z, N, element, model, and quantity.
    """

    # Exact filters
    z = filters.NumberFilter(field_name='Z', label='Proton number')
    n = filters.NumberFilter(field_name='N', label='Neutron number')
    model = filters.CharFilter(label='Model name')
    element = filters.CharFilter(field_name='element_symbol', lookup_expr='iexact', label='Element symbol')

    # Range filters
    z_min = filters.NumberFilter(field_name='Z', lookup_expr='gte', label='Minimum proton number')
    z_max = filters.NumberFilter(field_name='Z', lookup_expr='lte', label='Maximum proton number')
    n_min = filters.NumberFilter(field_name='N', lookup_expr='gte', label='Minimum neutron number')
    n_max = filters.NumberFilter(field_name='N', lookup_expr='lte', label='Maximum neutron number')
    a_min = filters.NumberFilter(field_name='A', lookup_expr='gte', label='Minimum mass number')
    a_max = filters.NumberFilter(field_name='A', lookup_expr='lte', label='Maximum mass number')

    # Quantity filter
    quantity = filters.CharFilter(label='Quantity to retrieve')

    # Search filter
    q = filters.CharFilter(method='search_filter', label='Search query')

    class Meta:
        fields = ['z', 'n', 'model', 'element', 'z_min', 'z_max', 'n_min', 'n_max', 'a_min', 'a_max', 'quantity', 'q']

    def search_filter(self, queryset, _name, _value):
        """Custom search filter across multiple fields."""
        # This would be implemented based on the data backend
        return queryset


class AnalyticsFilter(filters.FilterSet):
    """Filter for analytics queries."""

    model = filters.CharFilter(required=True, label='Model name')
    quantity = filters.CharFilter(required=True, label='Quantity')
    chain_type = filters.ChoiceFilter(
        choices=[('isotopic', 'Isotopic'), ('isotonic', 'Isotonic'), ('isobaric', 'Isobaric'), ('landscape', 'Landscape')],
        label='Chain type'
    )

    # Chain parameters
    z = filters.NumberFilter(label='Proton number (for isotopic chain)')
    n = filters.NumberFilter(label='Neutron number (for isotonic chain)')
    a = filters.NumberFilter(label='Mass number (for isobaric chain)')

    # Wigner coefficient selector
    wigner = filters.NumberFilter(label='Wigner coefficient (0, 1, 2, or 3)')

    # Filters
    even_even = filters.BooleanFilter(label='Even-even nuclei only')
    uncertainties = filters.BooleanFilter(label='Include uncertainties (AME2020)')

    # Range filters
    z_min = filters.NumberFilter(label='Minimum Z')
    z_max = filters.NumberFilter(label='Maximum Z')
    n_min = filters.NumberFilter(label='Minimum N')
    n_max = filters.NumberFilter(label='Maximum N')

    # Histogram parameters
    bins = filters.NumberFilter(label='Number of bins (for histogram)')

    class Meta:
        fields = [
            'model', 'quantity', 'chain_type', 'z', 'n', 'a', 'wigner',
            'even_even', 'uncertainties', 'z_min', 'z_max', 'n_min', 'n_max', 'bins'
        ]
