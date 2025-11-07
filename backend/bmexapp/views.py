"""
DRF Views for BMEX Masses API

All endpoints are read-only (GET only).
"""

import logging
from datetime import datetime
from typing import Dict, Any

from django.conf import settings
from rest_framework import status, views
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.exceptions import APIException, ValidationError
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, OpenApiExample

from .serializers import (
    HealthSerializer, ModelSerializer, MassRecordSerializer,
    NucleusSerializer, DropdownOptionSerializer, AnalyticsSeriesSerializer,
    ErrorResponseSerializer
)
from .services.reference import get_data_loader, DataLoader
from .services.dropdowns import DropdownService
from .services.analytics import get_analytics_service
from .pagination import StandardResultsSetPagination

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler for standardized error responses.
    """
    from rest_framework.views import exception_handler

    response = exception_handler(exc, context)

    if response is not None:
        custom_response_data = {
            'detail': response.data.get('detail', str(exc)),
            'code': getattr(exc, 'default_code', 'error'),
        }

        # Add hint for common errors
        if isinstance(exc, ValidationError):
            custom_response_data['hint'] = 'Check the request parameters and try again.'

        response.data = custom_response_data

    return response


@extend_schema(
    tags=['health'],
    summary='Health check',
    description='Check API health and get system status',
    responses={
        200: HealthSerializer,
    }
)
@api_view(['GET'])
def health_check(request):
    """
    Health check endpoint.
    Returns system status and configuration info.
    """
    return Response({
        'ok': True,
        'version': '1.0.0',
        'data_backend': settings.BMEX_DATA_BACKEND,
        'timestamp': datetime.utcnow().isoformat(),
    })

@extend_schema(
    tags=['models'],
    summary='List available models',
    description='Get list of all available theoretical nuclear models',
    responses={
        200: ModelSerializer(many=True),
    }
)
@api_view(['GET'])
def list_models(request):
    """
    List all available theoretical models.
    """
    models = [
        {
            'name': 'AME2020',
            'full_name': 'Atomic Mass Evaluation 2020',
            'description': 'Experimental mass evaluation from AME2020',
            'version': '2020'
        },
        {
            'name': 'SKMS',
            'full_name': 'Skyrme SkMs',
            'description': 'Skyrme Hartree-Fock-Bogoliubov model',
            'version': ''
        },
        {
            'name': 'SKP',
            'full_name': 'Skyrme SKP',
            'description': 'Skyrme Hartree-Fock-Bogoliubov model',
            'version': ''
        },
        {
            'name': 'SLY4',
            'full_name': 'Skyrme SLY4',
            'description': 'Skyrme Hartree-Fock-Bogoliubov model',
            'version': ''
        },
        {
            'name': 'SV',
            'full_name': 'Skyrme SV',
            'description': 'Skyrme Hartree-Fock-Bogoliubov model',
            'version': ''
        },
        {
            'name': 'UNEDF0',
            'full_name': 'UNEDF0',
            'description': 'Universal Nuclear Energy Density Functional',
            'version': '0'
        },
        {
            'name': 'UNEDF1',
            'full_name': 'UNEDF1',
            'description': 'Universal Nuclear Energy Density Functional',
            'version': '1'
        },
        {
            'name': 'UNEDF2',
            'full_name': 'UNEDF2',
            'description': 'Universal Nuclear Energy Density Functional',
            'version': '2'
        },
        {
            'name': 'ME2',
            'full_name': 'Covariant ME2',
            'description': 'Relativistic mean-field model',
            'version': ''
        },
        {
            'name': 'MEdelta',
            'full_name': 'Covariant MEdelta',
            'description': 'Relativistic mean-field model with delta',
            'version': ''
        },
        {
            'name': 'PC1',
            'full_name': 'Point-Coupling PC1',
            'description': 'Relativistic point-coupling model',
            'version': ''
        },
        {
            'name': 'NL3S',
            'full_name': 'Covariant NL3S',
            'description': 'Relativistic mean-field model',
            'version': ''
        },
        {
            'name': 'FRDM12',
            'full_name': 'Finite Range Droplet Model 2012',
            'description': 'Macroscopic-microscopic mass model',
            'version': '2012'
        },
        {
            'name': 'HFB24',
            'full_name': 'Hartree-Fock-Bogoliubov 24',
            'description': 'HFB mass table',
            'version': '24'
        },
        {
            'name': 'BCPM',
            'full_name': 'Brussels-Montreal Energy Density Functional',
            'description': 'Energy density functional model',
            'version': ''
        },
        {
            'name': 'D1M',
            'full_name': 'Gogny D1M',
            'description': 'Gogny force based model',
            'version': ''
        },
    ]
    return Response(models)


@extend_schema(
    tags=['masses'],
    summary='Query mass data',
    description='Query nuclear mass data with filtering and pagination',
    parameters=[
        OpenApiParameter('model', str, description='Model name (default: AME2020)'),
        OpenApiParameter('z', int, description='Exact proton number'),
        OpenApiParameter('n', int, description='Exact neutron number'),
        OpenApiParameter('z_min', int, description='Minimum proton number'),
        OpenApiParameter('z_max', int, description='Maximum proton number'),
        OpenApiParameter('n_min', int, description='Minimum neutron number'),
        OpenApiParameter('n_max', int, description='Maximum neutron number'),
        OpenApiParameter('element', str, description='Element symbol (e.g., Fe, U)'),
        OpenApiParameter('quantity', str, description='Specific quantity to retrieve (e.g., BE, TwoNSE)'),
        OpenApiParameter('page', int, description='Page number'),
        OpenApiParameter('page_size', int, description='Results per page (max 1000)'),
    ],
    responses={
        200: MassRecordSerializer(many=True),
        400: ErrorResponseSerializer,
    }
)
@api_view(['GET'])
def query_masses(request):
    """
    Query nuclear mass data with filters.
    Supports pagination and various filter parameters.
    """
    loader = get_data_loader()

    # Get query parameters
    model = request.query_params.get('model', 'AME2020')
    z = request.query_params.get('z')
    n = request.query_params.get('n')
    z_min = request.query_params.get('z_min')
    z_max = request.query_params.get('z_max')
    n_min = request.query_params.get('n_min')
    n_max = request.query_params.get('n_max')
    element = request.query_params.get('element')
    quantity = request.query_params.get('quantity')

    # Pagination
    page = int(request.query_params.get('page', 1))
    page_size = min(int(request.query_params.get('page_size', 100)), 1000)
    offset = (page - 1) * page_size

    try:
        # Convert parameters to int where needed
        if z:
            z_min = z_max = int(z)
        else:
            z_min = int(z_min) if z_min else None
            z_max = int(z_max) if z_max else None

        if n:
            n_min = n_max = int(n)
        else:
            n_min = int(n_min) if n_min else None
            n_max = int(n_max) if n_max else None

        # Query data
        records, total = loader.filter_masses(
            model=model,
            z_min=z_min,
            z_max=z_max,
            n_min=n_min,
            n_max=n_max,
            element=element,
            quantity=quantity,
            limit=page_size,
            offset=offset
        )

        # Build response
        total_pages = (total + page_size - 1) // page_size

        return Response({
            'count': total,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages,
            'results': records
        })

    except ValueError as e:
        return Response(
            {'detail': str(e), 'code': 'invalid_parameters'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Error querying masses: {e}")
        return Response(
            {'detail': 'Internal server error', 'code': 'server_error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    tags=['nuclei'],
    summary='List nuclei',
    description='List nuclei in discovery range',
    parameters=[
        OpenApiParameter('z_min', int, description='Minimum Z'),
        OpenApiParameter('z_max', int, description='Maximum Z'),
        OpenApiParameter('n_min', int, description='Minimum N'),
        OpenApiParameter('n_max', int, description='Maximum N'),
    ],
    responses={
        200: NucleusSerializer(many=True),
    }
)
@api_view(['GET'])
def list_nuclei(request):
    """
    List nuclei within specified ranges.
    """
    loader = get_data_loader()

    try:
        z_min = int(request.query_params.get('z_min', 1))
        z_max = int(request.query_params.get('z_max', 118))
        n_min = int(request.query_params.get('n_min', 0))
        n_max = int(request.query_params.get('n_max', 180))

        # Load AME2020 data to get discovered nuclei
        df = loader.load_model_data('AME2020')
        df = df[(df['Z'] >= z_min) & (df['Z'] <= z_max)]
        df = df[(df['N'] >= n_min) & (df['N'] <= n_max)]

        nuclei = []
        for _, row in df.iterrows():
            nuclei.append({
                'Z': int(row['Z']),
                'N': int(row['N']),
                'A': int(row['Z'] + row['N']),
            })

        return Response(nuclei)

    except Exception as e:
        logger.error(f"Error listing nuclei: {e}")
        return Response(
            {'detail': str(e), 'code': 'server_error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    tags=['dropdowns'],
    summary='Get dropdown options',
    description='Get dropdown option lists for UI components',
    parameters=[
        OpenApiParameter('name', str, description='Dropdown name (models, quantities, datasets, elements)', required=True),
        OpenApiParameter('quantity', str, description='Quantity filter (for datasets dropdown)'),
        OpenApiParameter('dataset', str, description='Dataset filter (for quantities dropdown)'),
        OpenApiParameter('beta_type', str, description='Beta decay type: minus or plus'),
        OpenApiParameter('q', str, description='Search query'),
    ],
    responses={
        200: DropdownOptionSerializer(many=True),
        400: ErrorResponseSerializer,
    }
)
@api_view(['GET'])
def get_dropdown_options(request, name):
    """
    Get dropdown options for UI components.
    Supports: models, quantities, datasets, elements
    """
    service = DropdownService()

    try:
        if name == 'models':
            # Return all available models
            options = [{'label': m, 'value': m} for m in DataLoader.MODELS]
            return Response(options)

        elif name == 'quantities':
            # Get quantities for a specific dataset
            dataset = request.query_params.get('dataset', 'AME2020')
            beta_type = request.query_params.get('beta_type', 'minus')
            options = service.get_quantity_options(dataset, beta_type)
            return Response(options)

        elif name == 'datasets':
            # Get datasets for a specific quantity
            quantity = request.query_params.get('quantity')
            if not quantity:
                return Response(
                    {'detail': 'quantity parameter is required', 'code': 'missing_parameter'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            exp_diff = request.query_params.get('exp_diff', 'false').lower() == 'true'
            options = service.get_dataset_options(quantity, exp_diff)
            return Response(options)

        elif name == 'elements':
            options = service.get_element_options()
            return Response(options)

        else:
            return Response(
                {'detail': f'Unknown dropdown name: {name}', 'code': 'invalid_dropdown'},
                status=status.HTTP_400_BAD_REQUEST
            )

    except ValueError as e:
        return Response(
            {'detail': str(e), 'code': 'invalid_parameters'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Error getting dropdown options for {name}: {e}")
        return Response(
            {'detail': 'Internal server error', 'code': 'server_error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    tags=['analytics'],
    summary='Get analytics series data',
    description='Get data series for plotting and visualization',
    parameters=[
        OpenApiParameter('model', str, description='Model name', required=True),
        OpenApiParameter('quantity', str, description='Quantity', required=True),
        OpenApiParameter('chain_type', str, description='isotopic, isotonic, isobaric, or landscape'),
        OpenApiParameter('z', int, description='Proton number (for isotopic chain)'),
        OpenApiParameter('n', int, description='Neutron number (for isotonic chain)'),
        OpenApiParameter('a', int, description='Mass number (for isobaric chain)'),
        OpenApiParameter('wigner', int, description='Wigner coefficient: 0, 1, 2, or 3'),
        OpenApiParameter('even_even', bool, description='Filter even-even nuclei only'),
        OpenApiParameter('uncertainties', bool, description='Include uncertainties (AME2020)'),
        OpenApiParameter('bins', int, description='Number of bins (for histogram)'),
    ],
    responses={
        200: AnalyticsSeriesSerializer,
        400: ErrorResponseSerializer,
    }
)
@api_view(['GET'])
def get_analytics_series(request):
    """
    Get data series for analytics and plotting.
    Supports isotopic, isotonic, isobaric chains and landscape data.
    """
    analytics = get_analytics_service()

    # Required parameters
    model = request.query_params.get('model')
    quantity = request.query_params.get('quantity')

    if not model or not quantity:
        return Response(
            {'detail': 'model and quantity parameters are required', 'code': 'missing_parameters'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Optional parameters
    chain_type = request.query_params.get('chain_type', 'isotopic')
    wigner = int(request.query_params.get('wigner', 0))
    even_even = request.query_params.get('even_even', 'false').lower() == 'true'
    uncertainties = request.query_params.get('uncertainties', 'false').lower() == 'true'

    try:
        if chain_type == 'isotopic':
            z = request.query_params.get('z')
            if not z:
                return Response(
                    {'detail': 'z parameter required for isotopic chain', 'code': 'missing_parameter'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            data = analytics.get_isotopic_series(
                int(z), model, quantity, wigner, even_even, uncertainties
            )

        elif chain_type == 'isotonic':
            n = request.query_params.get('n')
            if not n:
                return Response(
                    {'detail': 'n parameter required for isotonic chain', 'code': 'missing_parameter'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            data = analytics.get_isotonic_series(
                int(n), model, quantity, wigner, even_even, uncertainties
            )

        elif chain_type == 'isobaric':
            a = request.query_params.get('a')
            if not a:
                return Response(
                    {'detail': 'a parameter required for isobaric chain', 'code': 'missing_parameter'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            data = analytics.get_isobaric_series(
                int(a), model, quantity, wigner, even_even, uncertainties
            )

        elif chain_type == 'landscape':
            data = analytics.get_landscape_data(
                model, quantity, wigner, even_even
            )

        elif chain_type == 'histogram':
            bins = int(request.query_params.get('bins', 50))
            data = analytics.get_histogram_data(model, quantity, bins)

        else:
            return Response(
                {'detail': f'Invalid chain_type: {chain_type}', 'code': 'invalid_parameter'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(data)

    except ValueError as e:
        return Response(
            {'detail': str(e), 'code': 'invalid_parameters'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Error getting analytics series: {e}")
        return Response(
            {'detail': 'Internal server error', 'code': 'server_error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
