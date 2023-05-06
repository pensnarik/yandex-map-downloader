from enum import Enum


class DownloadResultEnum(Enum):
    DOWNLOADED = 1
    ERROR = 2
    EXISTS = 3


class DownloaderInterface():

    def download(self):
        raise NotImplementedError


class DownloadableInterface():

    def url(self):
        raise NotImplementedError

    def destination():
        raise NotImplementedError


class DownloadSchedulerInterface():

    def download(self):
        raise NotImplementedError


class DownloadPolicyInterface():

    def before_download(self, obj: DownloadableInterface):
        raise NotImplementedError

    def after_download(self):
        raise NotImplementedError

class DownloadResult():

    def __init__(self, result: DownloadResultEnum, code: str=None):
        self.__result = result
        self.__code = code

    def is_retriable(self):
        return self.__result == DownloadResultEnum.ERROR and \
               self.__code in ['400', 'timeout', 'connection_error']

    def need_to_sleep(self):
        return self.__result == DownloadResultEnum.DOWNLOADED

    def is_success(self):
        return self.__result == DownloadResultEnum.DOWNLOADED

    @classmethod
    def fromstr(cls, s: str):
        if ',' not in s:
            return cls(DownloadResultEnum[s])
        else:
            return cls(DownloadResultEnum[s.split(',')[0]], s.split(',')[1])

    def __str__(self):
        if self.__code:
            return f"{self.__result.name},{self.__code}"
        else:
            return f"{self.__result.name}"

    def __repr__(self):
        return self.__str__()
