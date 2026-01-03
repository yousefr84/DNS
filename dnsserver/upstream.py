import dns.resolver
import dns.rdatatype
import dns.exception


DNS_TYPE_MAP = {
    "A": dns.rdatatype.A,
    "AAAA": dns.rdatatype.AAAA,
    "CNAME": dns.rdatatype.CNAME,
    "MX": dns.rdatatype.MX,
    "TXT": dns.rdatatype.TXT,
    "PTR": dns.rdatatype.PTR,
    "NS": dns.rdatatype.NS,
}


def query_upstream_dns(domain: str, record_type: str) -> dict:


    resolver = dns.resolver.Resolver()
    resolver.nameservers = ["8.8.8.8", "1.1.1.1"]
    resolver.timeout = 3
    resolver.lifetime = 5

    try:
        answers = resolver.resolve(
            domain,
            DNS_TYPE_MAP[record_type],
            raise_on_no_answer=False,
        )

        response = {
            "Status": 0,
            "Question": [
                {
                    "name": domain,
                    "type": DNS_TYPE_MAP[record_type],
                }
            ],
            "Answer": [],
        }

        if answers.rrset is None:
            return response

        for rdata in answers:
            answer = {
                "name": domain,
                "type": DNS_TYPE_MAP[record_type],
                "TTL": answers.rrset.ttl,
            }

            if record_type == "A":
                answer["data"] = rdata.address

            elif record_type == "AAAA":
                answer["data"] = rdata.address

            elif record_type == "CNAME":
                answer["data"] = str(rdata.target).rstrip(".")

            elif record_type == "MX":
                answer["data"] = f"{rdata.preference} {str(rdata.exchange).rstrip('.')}"

            elif record_type == "TXT":
                answer["data"] = "".join(
                    part.decode() if isinstance(part, bytes) else part
                    for part in rdata.strings
                )

            elif record_type == "PTR":
                answer["data"] = str(rdata.target).rstrip(".")

            elif record_type == "NS":
                answer["data"] = str(rdata.target).rstrip(".")

            response["Answer"].append(answer)

        return response

    except dns.resolver.NXDOMAIN:
        return {
            "Status": 3,
            "Question": [
                {
                    "name": domain,
                    "type": DNS_TYPE_MAP[record_type],
                }
            ],
            "Answer": [],
        }

    except dns.exception.Timeout:
        return {
            "Status": 2,
            "Comment": "Upstream DNS timeout",
        }

    except Exception as exc:
        return {
            "Status": 2,
            "Comment": f"Upstream DNS error: {str(exc)}",
        }
