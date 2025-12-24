import dns.message
import dns.rdatatype
import dns.exception

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse

from records.models import DNSRecord
from dnsserver.upstream import query_upstream_dns


DNS_TYPE_MAP = {
    "A": 1,
    "AAAA": 28,
    "CNAME": 5,
    "MX": 15,
    "TXT": 16,
    "PTR": 12,
    "NS": 2,
}

REVERSE_DNS_TYPE_MAP = {v: k for k, v in DNS_TYPE_MAP.items()}


class DNSQueryView(APIView):
    """
    GET /dns-query
    POST /dns-query (JSON or Binary)
    """

    # =========================
    # GET
    # =========================
    def get(self, request):
        name = request.query_params.get("name")
        record_type = request.query_params.get("type", "A").upper()

        if not name:
            return Response(
                {"error": "Query parameter 'name' is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return self._handle_query(
            domain=name,
            record_type=record_type,
            request=request,
        )

    # =========================
    # POST
    # =========================
    def post(self, request):
        content_type = request.content_type

        # ---- JSON input ----
        if content_type == "application/json":
            name = request.data.get("name")
            record_type = request.data.get("type", "A").upper()

            if not name:
                return Response(
                    {"error": "'name' is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            return self._handle_query(
                domain=name,
                record_type=record_type,
                request=request,
            )

        # ---- Binary DNS input ----
        if content_type == "application/dns-message":
            return self._handle_binary_dns(request)

        return Response(
            {"error": "Unsupported Content-Type"},
            status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        )

    # =========================
    # Core Logic (Shared)
    # =========================
    def _handle_query(self, domain, record_type, request):
        record_type = record_type.upper()

        if record_type not in DNS_TYPE_MAP:
            return Response(
                {"error": f"Unsupported DNS record type: {record_type}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        records = DNSRecord.objects.filter(
            domain=domain,
            record_type=record_type,
        )

        # ---- Local records ----
        if records.exists():
            answers = []

            for record in records:
                data = record.value
                if record.record_type == DNSRecord.RecordType.MX:
                    data = f"{record.priority} {record.value}"

                answers.append(
                    {
                        "name": domain,
                        "type": DNS_TYPE_MAP[record_type],
                        "TTL": record.ttl,
                        "data": data,
                    }
                )

            response_json = {
                "Status": 0,
                "Question": [
                    {"name": domain, "type": DNS_TYPE_MAP[record_type]}
                ],
                "Answer": answers,
            }

            # Client wants binary?
            if request.headers.get("Accept") == "application/dns-message":
                return self._build_binary_response(domain, record_type, answers)

            return Response(response_json)

        # ---- Upstream ----
        upstream_response = query_upstream_dns(domain, record_type)
        return Response(upstream_response)

    # =========================
    # Binary DNS Handling
    # =========================
    def _handle_binary_dns(self, request):
        try:
            dns_query = dns.message.from_wire(request.body)
            question = dns_query.question[0]

            domain = question.name.to_text().rstrip(".")
            record_type = REVERSE_DNS_TYPE_MAP.get(question.rdtype)

            if not record_type:
                return Response(
                    {"error": "Unsupported DNS record type"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            records = DNSRecord.objects.filter(
                domain=domain,
                record_type=record_type,
            )

            # ---- Local answer ----
            if records.exists():
                response = dns.message.make_response(dns_query)

                for record in records:
                    rdata_text = record.value
                    if record.record_type == DNSRecord.RecordType.MX:
                        rdata_text = f"{record.priority} {record.value}"

                    rrset = dns.rrset.from_text(
                        domain,
                        record.ttl,
                        "IN",
                        record_type,
                        rdata_text,
                    )
                    response.answer.append(rrset)

                return HttpResponse(
                    response.to_wire(),
                    content_type="application/dns-message",
                )

            # ---- Upstream fallback ----
            upstream_response = query_upstream_dns(domain, record_type)
            return Response(upstream_response)

        except dns.exception.DNSException:
            return Response(
                {"error": "Invalid DNS binary message"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    # =========================
    # Build Binary Response from JSON
    # =========================
    def _build_binary_response(self, domain, record_type, answers):
        query = dns.message.make_query(domain, record_type)
        response = dns.message.make_response(query)

        for ans in answers:
            rrset = dns.rrset.from_text(
                ans["name"],
                ans["TTL"],
                "IN",
                record_type,
                ans["data"],
            )
            response.answer.append(rrset)

        return HttpResponse(
            response.to_wire(),
            content_type="application/dns-message",
        )
