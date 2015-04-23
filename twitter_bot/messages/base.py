class BaseMessageProvider(object):

    def __init__(self, *args, **kwargs):
        """
        Create an instance of provider
        :return: Instantiated provider
        """
        # Hook for future functionality
        pass

    def _extract_hashtags(self, mention):
        return [x['text'] for x in mention.get('entities', {}).get('hashtags', {})]

    def create(self, mention, max_message_length):
        """
        Create a message
        :param mention: JSON object containing mention details from Twitter (or an empty dict {})
        :param max_message_length: Maximum allowable length for created message
        :return: a message
        """
        raise NotImplementedError("Child class must implement "
                                  "create(self, mention, max_message_length)")


__all__ = ["BaseMessageProvider"]
