# Helper to get all installed applications on MacOS
import os


class Application:
    def __init__(self, name: str, path: str):
        self.name = name
        self.path = path

    def __str__(self):
        return f"{self.name} - {self.path}"

    def __repr__(self):
        return self.__str__()


def get_installed_applications():
    sources = [
        "/Applications",
    ]
    applications = []
    for source in sources:
        for app in os.listdir(source):
            if app.endswith(".app"):
                applications.append(
                    Application(app.removesuffix(".app"), os.path.join(source, app))
                )

    return sorted(applications, key=lambda x: x.name)


if __name__ == "__main__":
    print(*get_installed_applications(), sep="\n")
