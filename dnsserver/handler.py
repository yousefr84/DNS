import logging
import dns.rdatatype

from records.models import DNSRecord
from dnsserver.cache import get_from_cache, set_cache
from dnsserver.upstream import query_upstream_dns
from dnsserver.response_builder import build_dns_response, DNS_TYPE_MAP

logger = logging.getLogger(__name__)


def handle_query(domain=None, record_type=None, request=None, dns_request=None):
    """
    Unified DNS query handler for:
    - DoH (JSON / Binary)
    - UDP/TCP DNS server
    """

    # -------------------------------
    # 1️⃣ Extract domain & type
    # -------------------------------
    if dns_request:
        question = dns_request.question[0]
        domain = question.name.to_text().rstrip(".")
        record_type = dns.rdatatype.to_text(question.rdtype)

    record_type = record_type.upper()
    logger.info(f"DNS QUERY: {domain} {record_type}")

    # -------------------------------
    # 2️⃣ Cache lookup
    # -------------------------------
    cached_answers = get_from_cache(domain, record_type)
    if cached_answers:
        logger.info(f"CACHE HIT: {domain} {record_type}")
        return (
            build_dns_response(dns_request, cached_answers)
            if dns_request
            else cached_answers
        )

    # -------------------------------
    # 3️⃣ Query local database
    # -------------------------------
    records = DNSRecord.objects.filter(domain=domain, record_type=record_type)
    answers = []

    if records.exists():
        logger.info(f"LOCAL RECORD: {domain} {record_type}")

        for record in records:
            data = record.value
            if record.record_type == "MX":
                data = f"{record.priority} {record.value}"

            answers.append({
                "name": domain,
                "type": DNS_TYPE_MAP[record_type],
                "TTL": record.ttl,
                "data": data,
            })

        set_cache(domain, record_type, answers)

    else:
        # -------------------------------
        # 4️⃣ Fallback to upstream DNS
        # -------------------------------
        logger.info(f"UPSTREAM QUERY: {domain} {record_type}")

        upstream_response = query_upstream_dns(domain, record_type)
        answers = upstream_response.get("Answer", [])
        set_cache(domain, record_type, answers)

    # -------------------------------
    # 5️⃣ Return response
    # -------------------------------
    return (
        build_dns_response(dns_request, answers)
        if dns_request
        else answers
    )
