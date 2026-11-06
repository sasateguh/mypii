from mypii.pengecam.my_nric_recognizer import MyNricRecognizer
from mypii.pengecam.my_phone_recognizer import MyPhoneRecognizer
from mypii.pengecam.my_ssm_recognizer import MySsmRecognizer


def semua_pengecam(bahasa: str = "en") -> list:
    return [MyNricRecognizer(supported_language=bahasa), MySsmRecognizer(supported_language=bahasa),
            MyPhoneRecognizer(supported_language=bahasa)]


all_recognizers = semua_pengecam  # nama Inggeris untuk pengguna Presidio antarabangsa (fungsi yang sama)

__all__ = ["MyNricRecognizer", "MyPhoneRecognizer", "MySsmRecognizer", "all_recognizers", "semua_pengecam"]
