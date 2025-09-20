from fraud.kafka.producer import publish
import numpy as np
from fraud.models.detect_driver_license import detect_driver_license
class LicenseIdHandler:
    def __init__(self):
        pass
    @staticmethod
    def handle(image: np.array) -> bool:
        LicenseId=detect_driver_license(license_id)
        publish({"license_id": LicenseId}, topic="license_id")
        return LicenseId