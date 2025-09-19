import threading
import time
from typing import Optional

from kafka import KafkaConsumer
from fraud.core.config import get_settings

class FraudKafkaConsumer:
	def __init__(self) -> None:
		self._settings = get_settings()
		self._consumer: Optional[KafkaConsumer] = None
		self._thread: Optional[threading.Thread] = None
		self._stop_event = threading.Event()
	def start(self) -> None:
		if self._thread and self._thread.is_alive():
			return
		self._stop_event.clear()
		self._thread = threading.Thread(target=self._run_loop, name="fraud-kafka-consumer", daemon=True)
		self._thread.start()

	def stop(self) -> None:
		self._stop_event.set()
		if self._consumer is not None:
			try:
				self._consumer.close()
			except Exception:
				pass
		if self._thread is not None:
			self._thread.join(timeout=5)

	def _ensure_consumer(self) -> None:
		if self._consumer is None:
			print(f"[fraud-consumer] Initializing consumer to {self._settings.kafka_bootstrap_servers} topic={self._settings.kafka_topic}")
			self._consumer = KafkaConsumer(
				self._settings.kafka_topic,
				bootstrap_servers=self._settings.kafka_bootstrap_servers,
				client_id="fraud-consumer",
				group_id="fraud-service-group",
				auto_offset_reset="earliest",
				enable_auto_commit=True,
				value_deserializer=lambda v: v.decode("utf-8", errors="ignore"),
				security_protocol="PLAINTEXT",
			)

	def _run_loop(self) -> None:
		while not self._stop_event.is_set():
			try:
				
				self._ensure_consumer()
				assert self._consumer is not None
				records = self._consumer.poll(timeout_ms=1000, max_records=100)
				if not records:
					continue
				for tp, msgs in records.items():
					for message in msgs:
						if self._stop_event.is_set():
							break
						print(f"[fraud-consumer] topic={message.topic} partition={message.partition} offset={message.offset} value={message.value}")
			except Exception as exc:
				# Backoff on error
				print(f"[fraud-consumer] Error: {exc}. Retrying in 5s...")
				time.sleep(5)


consumer = FraudKafkaConsumer()


