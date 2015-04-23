class HelloWorldMessageProvider(object):

    def create(self):
        return "Hello World!"


__all__ = ["HelloWorldMessageProvider"]
