import time
from typing import List, Dict, Tuple

DNS_CACHE: Dict[Tuple[str, str], Dict] = {}


def get_from_cache(domain: str, record_type: str):
    key = (domain, record_type)
    item = DNS_CACHE.get(key)

    if not item:
        return None

    if time.time() > item["expires_at"]:
        DNS_CACHE.pop(key, None)
        return None

    return item["answers"]


def set_cache(domain: str, record_type: str, answers: List[dict]):
    if not answers:
        return

    ttl = min(ans.get("TTL", 60) for ans in answers)

    DNS_CACHE[(domain, record_type)] = {
        "answers": answers,
        "expires_at": time.time() + ttl
    }
