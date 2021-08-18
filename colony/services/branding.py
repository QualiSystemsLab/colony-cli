import enum


class Brand(str, enum.Enum):
    Torque = "torque"
    Colony = "colony"


class Branding:
    Brand = None

    @staticmethod
    def __check_if_set():
        if not Branding.Brand:
            raise Exception("Brand not set")

    @staticmethod
    def package_name():
        Branding.__check_if_set()
        if Branding.Brand == Brand.Torque:
            return "torque-cli"
        elif Branding.Brand == Brand.Colony:
            return "colony-cli"

    @staticmethod
    def command_name():
        Branding.__check_if_set()
        if Branding.Brand == Brand.Torque:
            return "torque"
        elif Branding.Brand == Brand.Colony:
            return "colony"

    @staticmethod
    def product_name():
        Branding.__check_if_set()
        if Branding.Brand == Brand.Torque:
            return "Torque"
        elif Branding.Brand == Brand.Colony:
            return "Colony"

    @staticmethod
    def api_host():
        Branding.__check_if_set()
        if Branding.Brand == Brand.Torque:
            return "qtorque.io"
        elif Branding.Brand == Brand.Colony:
            return "cloudshellcolony.com"


    @staticmethod
    def env_var_prefix():
        Branding.__check_if_set()
        if Branding.Brand == Brand.Torque:
            return "COLONY"
        elif Branding.Brand == Brand.Colony:
            return "TORQUE"


