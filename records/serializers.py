from rest_framework import serializers

from .models import DNSRecord


class DNSRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = DNSRecord
        fields = [
            "id",
            "domain",
            "record_type",
            "value",
            "ttl",
            "priority",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ("id", "created_at", "updated_at")

    def validate(self, attrs):
        record_type = attrs.get("record_type")
        priority = attrs.get("priority")

        if record_type == DNSRecord.RecordType.MX and priority is None:
            raise serializers.ValidationError(
                {"priority": "MX records require a priority value."}
            )

        if record_type != DNSRecord.RecordType.MX and priority is not None:
            raise serializers.ValidationError(
                {"priority": "Priority is only allowed for MX records."}
            )

        return attrs
