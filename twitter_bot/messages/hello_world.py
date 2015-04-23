from twitter_bot.messages.base import BaseMessageProvider


class HelloWorldMessageProvider(BaseMessageProvider):

    def create(self, mention, max_message_length):
        """
        Create a message
        :param mention: JSON object containing mention details from Twitter (or an empty dict {})
        :param max_message_length: Maximum allowable length for created message
        :return: the message "Hello World!"
        """
        return "Hello World!"


__all__ = ["HelloWorldMessageProvider"]
