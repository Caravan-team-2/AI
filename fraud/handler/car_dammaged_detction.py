from fraud.kafka.producer import publish
class CarDamageDetectionHandler:
    def __init__(self):
        pass
    @staticmethod
    def handle(car_dammaged_detection: str) -> bool:
        publish({"car_dammaged_detection": car_dammaged_detection}, topic="car_dammaged_detection")
        return True