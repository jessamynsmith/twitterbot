class HelloWorldMessageProvider(object):

    def create(self, mention):
        """
        Create a message
        :param mention: JSON object containing mention details from Twitter (or an empty dict {})
        :return: a message
        """
        return "Hello World!"


__all__ = ["HelloWorldMessageProvider"]
