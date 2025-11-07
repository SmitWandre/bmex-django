"""
DRF Serializers for BMEX Masses API
"""

from rest_framework import serializers


class HealthSerializer(serializers.Serializer):
    """Health check response."""
    ok = serializers.BooleanField()
    version = serializers.CharField()
    data_backend = serializers.CharField()
    timestamp = serializers.DateTimeField()


class ModelSerializer(serializers.Serializer):
    """Theoretical model information."""
    name = serializers.CharField()
    full_name = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True)
    version = serializers.CharField(required=False, allow_blank=True)


class MassRecordSerializer(serializers.Serializer):
    """Mass data record."""
    Z = serializers.IntegerField()
    N = serializers.IntegerField()
    A = serializers.IntegerField(read_only=True)
    element = serializers.CharField(required=False, allow_blank=True)
    model = serializers.CharField()
    quantity = serializers.CharField(required=False)
    value = serializers.FloatField(required=False, allow_null=True)
    uncertainty = serializers.FloatField(required=False, allow_null=True)
    is_estimated = serializers.BooleanField(required=False)
    unit = serializers.CharField(required=False, allow_blank=True)


class NucleusSerializer(serializers.Serializer):
    """Nucleus information."""
    Z = serializers.IntegerField()
    N = serializers.IntegerField()
    A = serializers.IntegerField(read_only=True)
    element_symbol = serializers.CharField(required=False, allow_blank=True)
    element_name = serializers.CharField(required=False, allow_blank=True)


class DropdownOptionSerializer(serializers.Serializer):
    """Dropdown option item."""
    label = serializers.CharField()
    value = serializers.CharField()
    disabled = serializers.BooleanField(default=False)
    title = serializers.CharField(required=False, allow_blank=True)


class AnalyticsSeriesSerializer(serializers.Serializer):
    """Analytics data series for plotting."""
    model = serializers.CharField()
    quantity = serializers.CharField()
    unit = serializers.CharField(allow_blank=True)
    chain_type = serializers.CharField(required=False)

    # For 1D series (isotopic, isotonic, isobaric)
    neutrons = serializers.ListField(child=serializers.IntegerField(), required=False)
    protons = serializers.ListField(child=serializers.IntegerField(), required=False)
    values = serializers.ListField(child=serializers.FloatField(allow_null=True), required=False)
    uncertainties = serializers.ListField(child=serializers.FloatField(allow_null=True), required=False)
    estimated = serializers.ListField(child=serializers.IntegerField(), required=False)

    # For 2D landscape data
    z_values = serializers.ListField(child=serializers.IntegerField(), required=False)
    n_values = serializers.ListField(child=serializers.IntegerField(), required=False)
    data = serializers.ListField(required=False)  # 2D array
    value_min = serializers.FloatField(required=False, allow_null=True)
    value_max = serializers.FloatField(required=False, allow_null=True)
    step = serializers.IntegerField(required=False)

    # For model comparison
    difference = serializers.ListField(child=serializers.FloatField(allow_null=True), required=False)
    model1 = serializers.CharField(required=False)
    model2 = serializers.CharField(required=False)

    # For histogram
    counts = serializers.ListField(child=serializers.IntegerField(), required=False)
    bin_edges = serializers.ListField(child=serializers.FloatField(), required=False)
    total_nuclei = serializers.IntegerField(required=False)
    mean = serializers.FloatField(required=False)
    std = serializers.FloatField(required=False)


class ErrorResponseSerializer(serializers.Serializer):
    """Standard error response."""
    detail = serializers.CharField()
    code = serializers.CharField(required=False)
    hint = serializers.CharField(required=False)
