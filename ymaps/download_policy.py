import os

from ymaps import DownloadableInterface, DownloadResult, DownloadableInterface, DownloadPolicyInterface


class CommonDownloadPolicy(DownloadPolicyInterface):

    def __init__(self, obj: DownloadableInterface):
        self.obj = obj

    def errfile(self):
        return f"{self.obj.destination()}.error"

    def before_download(self):
        # Return True if object should be downloaded, otherwise returns False
        if os.path.exists(self.errfile()):
            with open(self.errfile(), "r") as f:
                result = DownloadResult.fromstr(f.read())
                return result.is_retriable()
        else:
            return not os.path.exists(self.obj.destination())

    def after_download(self, result: DownloadResult):
        if not result.is_success():
            with open(self.errfile(), "w") as f:
                f.write(str(result))
