import os

from twitter_bot.since_id.base_provider import BaseSinceIdProvider


class FileSystemSinceIdProvider(BaseSinceIdProvider):

    def __init__(self):
        super(FileSystemSinceIdProvider, self).__init__()
        filename = os.environ.get('TWITTER_SINCE_ID_FILENAME', '.since_id.txt')
        self.filename = os.path.join(os.getcwd(), filename)

    def get(self):
        since_id = ''
        try:
            with open(self.filename) as since_id_file:
                # Disable branch coverage because there is a bug that the last line in
                # a with block will always say it has partial coverage
                since_id = since_id_file.readline()  # pragma: no branch
        except IOError:
            pass
        return since_id

    def set(self, since_id):
        temp_filename = '{0}.tmp'.format(self.filename)
        with open(temp_filename, 'w') as since_id_file:
            since_id_file.write(since_id)
        os.rename(temp_filename, self.filename)
        return True

    def delete(self):
        temp_filename = '{0}.tmp'.format(self.filename)
        with open(temp_filename, 'w') as since_id_file:
            since_id_file.write('')
        os.rename(temp_filename, self.filename)
        return True


__all__ = ["FileSystemSinceIdProvider"]
