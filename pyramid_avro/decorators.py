import inspect

from pyramid import view as p_view


class avro_message(p_view.view_config):
    """Decorator for registering an avro message with a given service."""

    _err = "service_name must be provided as an attribute or keyword " \
           "argument to the callable {}"

    def __call__(self, wrapped):
        """
        The wrapped object to register as a valid callable for handling this
        message.

        :param wrapped: an object to register as a message for a service.
        :return: the wrapped object.
        """
        settings = self.__dict__.copy()
        depth = settings.pop("_depth", 0)
        settings.pop("message_impl", None)

        # Mostly a copy of view_config"s impl, just changing the config
        # attachment.
        def callback(context, name, ob):
            message_impl = wrapped
            # Try to grab the "service_name" from our initial args if possible.
            if settings.get("service_name") is None:
                # If it's not in the args, see if it's on the object.
                service_name = getattr(ob, "service_name", None)

                # Try to use the class name if it's  class.
                if service_name is None:
                    if not inspect.isclass(ob):
                        raise AttributeError(
                            self._err.format(message_impl.__name__)
                        )
                    message_impl = message_impl.__get__(ob)
                    service_name = ob.__name__.lower()
                settings["service_name"] = service_name
            message_name = settings.pop("message", None)
            settings["message"] = message_name or message_impl.__name__
            config = context.config.with_package(info.module)
            config.register_avro_message(
                message_impl=message_impl,
                **settings
            )

        info = self.venusian.attach(
            wrapped,
            callback,
            category="pyramid",
            depth=depth + 1
        )
        return wrapped


__all__ = [avro_message.__name__]
