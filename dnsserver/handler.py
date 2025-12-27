import dns.message
from records.models import DNSRecord
from dnsserver.upstream import query_upstream_dns
from dnsserver.response_builder import build_dns_response, DNS_TYPE_MAP

def handle_query(domain=None, record_type=None, request=None, dns_request=None):
    """
    domain: str
    record_type: str
    request: HttpRequest (DoH)
    dns_request: dns.message.Message (DNS UDP/TCP)
    """

    # اگر dns_request هست، اطلاعات domain/type از request گرفته میشه
    if dns_request:
        question = dns_request.question[0]
        domain = question.name.to_text().rstrip(".")
        record_type = dns.rdatatype.to_text(question.rdtype)

    # Query رکورد از دیتابیس
    records = DNSRecord.objects.filter(domain=domain, record_type=record_type)
    answers = []

    if records.exists():
        for record in records:
            data = record.value
            if record.record_type == "MX":
                data = f"{record.priority} {record.value}"

            answers.append({
                "name": domain,
                "type": DNS_TYPE_MAP[record_type],
                "TTL": record.ttl,
                "data": data
            })
    else:
        # fallback به upstream
        upstream = query_upstream_dns(domain, record_type)
        answers = upstream.get("Answer", [])

    # خروجی Binary یا JSON
    if dns_request:
        return build_dns_response(dns_request, answers)
    else:
        return answers  # برای DoH, JSON پاسخ
