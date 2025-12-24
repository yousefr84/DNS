from django.db import models


class RecordType(models.TextChoices):
    A = "A", "A"
    AAAA = "AAAA", "AAAA"
    CNAME = "CNAME", "CNAME"
    MX = "MX", "MX"
    TXT = "TXT", "TXT"
    PTR = "PTR", "PTR"
    NS = "NS", "NS"


class DNSRecord(models.Model):
    domain = models.CharField(
        max_length=255
    )

    record_type = models.CharField(
        max_length=10,
        choices=RecordType.choices,
        default=RecordType.A
    )

    value = models.CharField(
        max_length=512
    )

    ttl = models.PositiveIntegerField(
        default=300
    )  # seconde

    priority = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["domain", "record_type"]),
        ]
        unique_together = ("domain", "record_type", "value")
        verbose_name = "DNS Record"
        verbose_name_plural = "DNS Records"

    def __str__(self):
        return f"{self.domain} {self.record_type} {self.value}"
