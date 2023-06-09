import os

from polyconf.core.model import Context, Status
from polyconf.core.model.plugin import Plugin


class EnvPlugin(Plugin):
    name = "env"
    is_flat = True

    def hydrate(self, context: Context) -> Context:
        self.logger.info(f'{self.name} says, "hello"')

        # Pattern: (section + _ + key).upper()
        gather = {
            k: v
            for k, v in os.environ.items()
            if k.startswith(f"{context.app_prefix}_")
        }
        # self.logger.info(f"{gather=}")

        for k, v in gather.items():
            name = k.removeprefix(f"{context.app_prefix}_")
            self.add_result(name=name, value=v, context=context, source=name)

        # # --------------------------------------------------------------------------
        # section = "default"
        # data.default_account = os.getenv(f"{section}_account".upper()) or data.default_account
        # data.default_region = os.getenv(f"{section}_region".upper()) or data.default_region
        # data.default_namespace = os.getenv(f"{section}_namespace".upper()) or data.default_namespace
        #
        # # --------------------------------------------------------------------------
        # section = "aws"
        # data.aws_profile = os.getenv(f"{section}_profile".upper()) or data.aws_profile
        # data.native_account = os.getenv("native_account".upper()) or data.native_account
        # data.session_name_prefix = os.getenv("session_name_prefix".upper()) or data.session_name_prefix
        #
        # # --------------------------------------------------------------------------
        # if debug := os.getenv("DEBUG"):
        #     data.raw.debug = debug
        #     data.raw.seen.add("debug")
        #
        # if account_map := os.getenv("account_map".upper()):
        #     data.raw.account_map = account_map
        #     data.raw.seen.add("account_map")

        context.status = Status.OK
        return context


def factory(*args, **kwargs):
    return EnvPlugin(*args, **kwargs)
