from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken, TokenError


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def revoke_refresh_token(request):
    """Blacklist a refresh token supplied by the client.

    Body: { "refresh": "<refresh_token>" }
    Requires authenticated user (so we can verify intent).
    """
    token = request.data.get('refresh')
    if not token:
        return Response({'detail': 'refresh token required'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        RefreshToken(token).blacklist()
    except TokenError:
        return Response({'detail': 'invalid token'}, status=status.HTTP_400_BAD_REQUEST)
    return Response({'detail': 'token revoked'}, status=status.HTTP_200_OK)
