from dataclasses import dataclass


@dataclass
class ParkingState:
    vehicle_in_parking: bool = False
    absent_cycles: int = 0
