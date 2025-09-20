from fraud.models.plate_detect import LicensePlateDetector
import numpy as np
class PlateDetectHandler:
    def __init__(self):
        pass
    @staticmethod
    def handle(plate_detection:np.array) -> None:
     print(f"Handling plate detection: {plate_detection}")