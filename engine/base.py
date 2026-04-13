from abc import ABC, abstractmethod


class RedModule(ABC):
    name: str = ""
    description: str = ""
    version: str = "1.0.0"

    @abstractmethod
    def run(self, params: dict) -> dict:
        """Execute the module. Returns a result dict with at least a 'status' key."""
        ...

    def info(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "type": "red",
        }


class BlueModule(ABC):
    name: str = ""
    description: str = ""
    version: str = "1.0.0"

    @abstractmethod
    def run(self, params: dict) -> dict:
        """Process logs or events. Returns a result dict with at least a 'status' key."""
        ...

    def info(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "type": "blue",
        }


class PurpleModule(ABC):
    name: str = ""
    description: str = ""
    version: str = "1.0.0"

    @abstractmethod
    def run(self, params: dict) -> dict:
        """Correlate red and blue results. Returns a result dict with at least a 'status' key."""
        ...

    def info(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "type": "purple",
        }
