from fraud.kafka.producer import publish
class LicenseIdHandler:
    def __init__(self):
        pass
    @staticmethod
    def handle(license_id: str) -> bool:
        publish({"license_id": license_id}, topic="license_id")
        return True