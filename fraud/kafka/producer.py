import json
from typing import Optional, Union

from kafka import KafkaProducer

from fraud.core.config import get_settings


_producer: Optional[KafkaProducer] = None


def _get_producer() -> KafkaProducer:
	global _producer
	if _producer is None:
		settings = get_settings()
		_producer = KafkaProducer(
			bootstrap_servers=settings.kafka_bootstrap_servers,
			client_id="fraud-producer",
			value_serializer=lambda v: v if isinstance(v, (bytes, bytearray)) else json.dumps(v).encode("utf-8"),
			security_protocol="PLAINTEXT",
		)
	return _producer


def publish(value: Union[str, bytes, dict], topic: Optional[str] = None) -> None:
	settings = get_settings()
	producer = _get_producer()
	topic_name = topic or settings.kafka_topic
	producer.send(topic_name, value)
	producer.flush()



