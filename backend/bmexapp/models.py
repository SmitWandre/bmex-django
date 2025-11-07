"""
Django models for BMEX Masses API

These models are optional and only used when BMEX_DATA_BACKEND='db'.
For file mode, data is loaded directly from HDF5 files.
"""

from django.db import models


class TheoreticalModel(models.Model):
    """Represents a theoretical nuclear model."""

    name = models.CharField(max_length=50, unique=True, db_index=True)
    full_name = models.CharField(max_length=200)
    version = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'theoretical_models'
        ordering = ['name']

    def __str__(self):
        return self.name


class Nucleus(models.Model):
    """Represents a nucleus with Z protons and N neutrons."""

    Z = models.IntegerField(db_index=True, help_text="Proton number")
    N = models.IntegerField(db_index=True, help_text="Neutron number")
    element_symbol = models.CharField(max_length=3, blank=True, db_index=True)
    element_name = models.CharField(max_length=50, blank=True)

    class Meta:
        db_table = 'nuclei'
        unique_together = [['Z', 'N']]
        ordering = ['Z', 'N']
        indexes = [
            models.Index(fields=['Z', 'N']),
        ]

    @property
    def A(self):
        """Mass number (A = Z + N)"""
        return self.Z + self.N

    def __str__(self):
        return f"{self.element_symbol}-{self.A} (Z={self.Z}, N={self.N})"


class MassRecord(models.Model):
    """
    Stores nuclear mass and related quantities for a specific nucleus and model.
    Only used in DB mode.
    """

    nucleus = models.ForeignKey(Nucleus, on_delete=models.CASCADE, related_name='mass_records')
    model = models.ForeignKey(TheoreticalModel, on_delete=models.CASCADE, related_name='mass_records')

    # Core quantities
    BE = models.FloatField(null=True, blank=True, help_text="Binding Energy (MeV)")
    MassExcess = models.FloatField(null=True, blank=True, help_text="Mass Excess (MeV)")

    # Separation energies
    OneNSE = models.FloatField(null=True, blank=True, help_text="One Neutron Separation Energy (MeV)")
    OnePSE = models.FloatField(null=True, blank=True, help_text="One Proton Separation Energy (MeV)")
    TwoNSE = models.FloatField(null=True, blank=True, help_text="Two Neutron Separation Energy (MeV)")
    TwoPSE = models.FloatField(null=True, blank=True, help_text="Two Proton Separation Energy (MeV)")
    AlphaSE = models.FloatField(null=True, blank=True, help_text="Alpha Separation Energy (MeV)")

    # Decay Q-values
    BetaMinusDecay = models.FloatField(null=True, blank=True, help_text="Beta Minus Decay Q-Value (MeV)")
    BetaPlusDecay = models.FloatField(null=True, blank=True, help_text="Beta Plus Decay Q-Value (MeV)")
    ElectronCaptureQValue = models.FloatField(null=True, blank=True, help_text="Electron Capture Q-Value (MeV)")
    AlphaDecayQValue = models.FloatField(null=True, blank=True, help_text="Alpha Decay Q-Value (MeV)")

    # Shell effects
    TwoNSGap = models.FloatField(null=True, blank=True, help_text="Two Neutron Shell Gap (MeV)")
    TwoPSGap = models.FloatField(null=True, blank=True, help_text="Two Proton Shell Gap (MeV)")

    # Uncertainties (AME2020 only)
    u_BE = models.FloatField(null=True, blank=True, help_text="BE Uncertainty")
    e_BE = models.IntegerField(null=True, blank=True, help_text="BE Estimated flag")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'mass_records'
        unique_together = [['nucleus', 'model']]
        indexes = [
            models.Index(fields=['nucleus', 'model']),
        ]

    def __str__(self):
        return f"{self.nucleus} - {self.model.name}"
