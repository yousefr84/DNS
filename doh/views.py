import dns.exception as dexception
import dns.message as dmessage
from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework.views import APIView

from dnsserver.handler import handle_query
from dnsserver.response_builder import DNS_TYPE_MAP


class DNSQueryView(APIView):
    """
    GET /dns-query
    POST /dns-query
    RFC 8484 compliant
    """

    def get(self, request):
        name = request.query_params.get("name")
        record_type = request.query_params.get("type", "A").upper()
        accept = request.headers.get("Accept", "application/dns-json")

        if not name:
            return Response({"error": "Query parameter 'name' is required"}, status=400)

        # پاسخ handler
        answers = handle_query(domain=name, record_type=record_type)

        if accept == "application/dns-message":
            # ساخت DNS binary
            import dns.message
            query = dns.message.make_query(name, record_type)
            import dns.rrset
            response = dns.message.make_response(query)
            for ans in answers:
                rrset = dns.rrset.from_text(ans["name"], ans["TTL"], "IN", record_type, ans["data"])
                response.answer.append(rrset)
            return HttpResponse(response.to_wire(), content_type="application/dns-message")

        # default JSON
        return Response({
            "Status": 0,
            "Question": [{"name": name, "type": DNS_TYPE_MAP[record_type]}],
            "Answer": answers
        })

    def post(self, request):
        content_type = request.content_type
        accept = request.headers.get("Accept", "application/dns-json")

        # ---- JSON input ----
        if content_type == "application/json":
            name = request.data.get("name")
            record_type = request.data.get("type", "A").upper()

            if not name:
                return Response({"error": "'name' is required"}, status=400)

            answers = handle_query(domain=name, record_type=record_type)

            if accept == "application/dns-message":
                import dns.message
                query = dns.message.make_query(name, record_type)
                import dns.rrset
                response = dns.message.make_response(query)
                for ans in answers:
                    rrset = dns.rrset.from_text(ans["name"], ans["TTL"], "IN", record_type, ans["data"])
                    response.answer.append(rrset)
                return HttpResponse(response.to_wire(), content_type="application/dns-message")

            # default JSON
            return Response({
                "Status": 0,
                "Question": [{"name": name, "type": DNS_TYPE_MAP[record_type]}],
                "Answer": answers
            })

        # ---- Binary DNS input ----
        if content_type == "application/dns-message":
            try:
                dns_request = dmessage.from_wire(request.body)
                response = handle_query(dns_request=dns_request)
                return HttpResponse(response, content_type="application/dns-message")
            except dexception.DNSException:
                return Response({"error": "Invalid DNS binary message"}, status=400)

        return Response({"error": "Unsupported Content-Type"}, status=415)
