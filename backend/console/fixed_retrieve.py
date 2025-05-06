from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
import logging

logger = logging.getLogger(__name__)

class FixedRetrieve(APIView):
    def retrieve(self, request, pk=None):
        """
        دریافت اطلاعات یک کانال خاص با استفاده از Supabase REST API
        """
        try:
            response = _make_request('GET', f"/rest/v1/channels?uid=eq.{pk}")
            
            if response is True or response is None or (isinstance(response, list) and len(response) == 0):
                return Response(
                    {"detail": "Channel not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
                
            # اگر پاسخ یک لیست است، اولین آیتم را برگردان
            if isinstance(response, list) and len(response) > 0:
                return Response(response[0], status=status.HTTP_200_OK)
            
            # اگر پاسخ یک آبجکت است
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"خطا در دریافت کانال از Supabase: {e}")
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 