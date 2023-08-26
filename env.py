from exenenv import EnvironmentProfile

try:
    import dotenv

    dotenv.load_dotenv()
except ModuleNotFoundError:
    pass


class MainEnvironment(EnvironmentProfile):
    TOKEN: str
    API_PORT: int = 3030
    API_SECRET: str


env = MainEnvironment()
env.load()
