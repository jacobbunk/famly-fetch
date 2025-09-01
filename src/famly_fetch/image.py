from dataclasses import dataclass
from datetime import datetime


@dataclass
class BaseImage:
    img_id: str
    prefix: str
    width: int
    height: int
    key: str
    date: datetime
    text: str | None

    @property
    def url(self):
        raise NotImplementedError()


@dataclass
class Image(BaseImage):
    @staticmethod
    def from_dict(
        data: dict, date_override: str | None = None, text_override: str | None = None
    ):
        return Image(
            img_id=data["imageId"],
            prefix=data["prefix"],
            width=data["width"],
            height=data["height"],
            key=data["key"],
            date=datetime.fromisoformat(date_override or data["createdAt"]),
            text=text_override or data.get("text", None),
        )

    @property
    def url(self):
        return f"{self.prefix}/{self.width}x{self.height}/{self.key}"


@dataclass
class SecretImage(BaseImage):
    path: str
    expires: str

    @staticmethod
    def from_dict(
        data: dict, date_override: str | None = None, text_override: str | None = None
    ):
        return SecretImage(
            img_id=data["id"],
            prefix=data["secret"]["prefix"],
            width=data["width"],
            height=data["height"],
            key=data["secret"]["key"],
            date=datetime.fromisoformat(date_override or data["createdAt"]),
            path=data["secret"]["path"],
            expires=data["secret"]["expires"],
            text=text_override or data.get("text", None),
        )

    @property
    def url(self):
        return f"{self.prefix}/{self.key}/{self.width}x{self.height}/{self.path}?expires={self.expires}"
