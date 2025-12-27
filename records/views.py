from rest_framework import viewsets, status
from rest_framework.response import Response

from .models import DNSRecord
from .serializers import DNSRecordSerializer


class AdminRecordViewSet(viewsets.ModelViewSet):
    """
    /admin/record
    """

    queryset = DNSRecord.objects.all().order_by("domain")
    serializer_class = DNSRecordSerializer

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        if "type" in data:
            data["record_type"] = data.pop("type")

        # بررسی یکتا بودن
        if DNSRecord.objects.filter(
                domain=data.get("domain"),
                record_type=data.get("record_type"),
                value=data.get("value")
        ).exists():
            return Response(
                {"status": "error", "message": "Record already exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({"status": "success", "message": "record added", "data": serializer.data}, status=201)



    def destroy(self, request, *args, **kwargs):
        domain = kwargs.get("pk")  # یا از query param
        record_type = request.query_params.get("type")
        value = request.query_params.get("value")

        if not (domain and record_type and value):
            return Response(
                {"status": "error", "message": "domain, type and value are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        deleted_count, _ = DNSRecord.objects.filter(
            domain=domain,
            record_type=record_type,
            value=value
        ).delete()

        if deleted_count == 0:
            return Response(
                {"status": "error", "message": "record not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response({"status": "success", "message": "record deleted"}, status=200)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        domain = request.query_params.get("domain")
        record_type = request.query_params.get("type")
        value = request.query_params.get("value")

        if domain:
            queryset = queryset.filter(domain=domain)
        if record_type:
            queryset = queryset.filter(record_type=record_type)
        if value:
            queryset = queryset.filter(value=value)

        serializer = self.get_serializer(queryset, many=True)
        return Response({"status": "success", "data": serializer.data})
