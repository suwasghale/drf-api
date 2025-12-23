from rest_framework.pagination import PageNumberPagination

class StandardResultsSetPagination(PageNumberPagination):
    """
    Standard pagination class for consistent API responses.
    Can be reused across all API viewsets.
    """
    page_size = 10                      # Default items per page
    page_size_query_param = 'page_size' # Allow ?page_size=20
    max_page_size = 100                 # Prevent abuse
    page_query_param = 'page'           # Allow ?page=2