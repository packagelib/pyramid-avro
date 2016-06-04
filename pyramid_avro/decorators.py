from pyramid import view as p_view


class avro_message(p_view.view_config):

    def __call__(self, wrapped):
        settings = self.__dict__.copy()
        depth = settings.pop("_depth", 0)

        # Mostly a copy of view_config"s impl, just changing the config
        # attachment.
        def callback(context, name, ob):
            config = context.config.with_package(info.module)
            config.register_avro_message(message_impl=ob, **settings)

        info = self.venusian.attach(
            wrapped,
            callback,
            category="pyramid",
            depth=depth + 1
        )

        if info.scope == "class":
            # if the decorator was attached to a method in a class, or
            # otherwise executed at class scope, we need to set an
            # "attr" into the settings if one isn"t already in there
            if settings.get("attr") is None:
                settings["attr"] = wrapped.__name__

        settings["_info"] = info.codeinfo # fbo "action_method"
        return wrapped


__all__ = [avro_message.__name__]
