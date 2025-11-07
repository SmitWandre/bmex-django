"""
Analytics service for series data
"""


class AnalyticsService:
    """Service for analytics and plotting data"""

    def get_isotopic_series(self, z, model, quantity, wigner=0,
                           even_even=False, uncertainties=False):
        """Get isotopic chain series"""
        return {'x': [], 'y': []}

    def get_isotonic_series(self, n, model, quantity, wigner=0,
                           even_even=False, uncertainties=False):
        """Get isotonic chain series"""
        return {'x': [], 'y': []}

    def get_isobaric_series(self, a, model, quantity, wigner=0,
                           even_even=False, uncertainties=False):
        """Get isobaric chain series"""
        return {'x': [], 'y': []}

    def get_landscape_data(self, model, quantity, wigner=0, even_even=False):
        """Get landscape data"""
        return {'x': [], 'y': [], 'z': []}

    def get_histogram_data(self, model, quantity, bins=50):
        """Get histogram data"""
        return {'bins': [], 'counts': []}


_analytics_instance = None


def get_analytics_service():
    """Get analytics service instance"""
    global _analytics_instance
    if _analytics_instance is None:
        _analytics_instance = AnalyticsService()
    return _analytics_instance
