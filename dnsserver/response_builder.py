import dns.message
import dns.rrset

DNS_TYPE_MAP = {
    "A": 1, "AAAA": 28, "CNAME": 5, "MX": 15,
    "TXT": 16, "PTR": 12, "NS": 2
}

def build_dns_response(request, answers):
    """
    request: dns.message.Message
    answers: list of dict {name, type, TTL, data}
    Returns: bytes (binary DNS response)
    """
    response = dns.message.make_response(request)

    for ans in answers:
        record_type = ans["type"]
        rdata_text = ans["data"]

        # MX record: باید شامل priority باشد
        if record_type == "MX" and " " not in rdata_text:
            # فرض: priority 10 پیش‌فرض
            rdata_text = f"10 {rdata_text}"

        rrset = dns.rrset.from_text(
            ans["name"],
            ans["TTL"],
            "IN",
            record_type,
            rdata_text,
        )
        response.answer.append(rrset)

    return response.to_wire()
