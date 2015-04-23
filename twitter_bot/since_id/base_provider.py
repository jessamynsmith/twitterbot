class BaseSinceIdProvider(object):

    def __init__(self, *args, **kwargs):
        """
        Create an instance of provider
        :return: Instantiated provider
        """
        # Hook for future functionality
        pass

    def get(self):
        """
        Retrieve the value for since_id
        :return: The since_id previously stored, or empty string if none available
        """
        raise NotImplementedError("Child class must implement get(self)")

    def set(self, since_id):
        """
        Set the value for since_id
        :param since_id: The since_id value to be stored
        :return: Some truthy value if successful
        """
        raise NotImplementedError("Child class must implement set(self, since_id)")

    def delete(self):
        """
        Delete the saved value for since_id
        :return: Some truthy value if successful
        """
        raise NotImplementedError("Child class must implement delete(self)")


__all__ = ["BaseSinceIdProvider"]
