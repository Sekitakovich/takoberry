from dataclasses import dataclass


@dataclass()
class ADXL345(object):
    address: int = 0x1D
    threshold: int = 60  # 環境に応じて設定可能とすべく可変抵抗から読み込みたい


@dataclass()
class Constants(object):
    GPSdatetimeFormat: str = '%d-%d-%d %d:%d:%d'
    SYSdatetimeformat: str = '%Y-%m-%d %H:%M:%S'

    adxl345 = ADXL345()

