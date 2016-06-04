from pyramid import view as p_view


class avro_message(p_view.view_config):

    def __call__(self, wrapped):
        settings = self.__dict__.copy()
        depth = settings.pop("_depth", 0)
        settings.pop("message_impl", None)

        # Mostly a copy of view_config"s impl, just changing the config
        # attachment.
        def callback(context, name, ob):
            if settings.get("service_name") is None:
                # Try service_name attribute.
                service_name = getattr(ob, "service_name", None)

                # Else, try class name.
                if service_name is None:
                    service_name = ob.__name__.lower()

                settings["service_name"] = service_name

            message_name = settings.pop("message", None) or wrapped.__name__
            settings["message"] = message_name
            config = context.config.with_package(info.module)
            config.register_avro_message(message_impl=wrapped, **settings)

        info = self.venusian.attach(
            wrapped,
            callback,
            category="pyramid",
            depth=depth + 1
        )
        return wrapped


__all__ = [avro_message.__name__]
