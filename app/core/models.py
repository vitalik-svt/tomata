import os
import json
from enum import Enum
import datetime as dt
from typing import Optional, List, Dict, Literal
from pydantic import ConfigDict, BaseModel, Field, EmailStr, model_validator
from pydantic.functional_validators import BeforeValidator

from typing_extensions import Annotated


event_type_mapper = {
    "GA:detail": """'elementType': 'page',
'elementBlock': 'productDetail', // блок, в котором расположен элемент
'productName': 'Клей для виниловых обоев с индикатором Axton 35-45 м2 7-9
рулонов', // название товара
'productId': '18149575', // артикул товара
'productPrice': '75.00', // текущая стоимость единицы товара
'productPrevPrice': '175.00', // стоимость единицы товара до снижения цены или null
'productBelong': 'LeroyMerlin', // принадлежность товара: LeroyMerlinMarketplace - для
товаров Маркетплейс, Longtail - для товаров longtail, LeroyMerlin - для товаров Леруа
Мерлен
'productAvailability': 'S-02.12.21/D-03.12.21', // S - самовывоз и через дефис дата; / для
разделения типов; D - доставка и через дефис дата; Если товар недоступен, то
передавать “unavailable”
'productsQuantityAvailable': '543', // суммарное кол-во доступных товаров по всем
магазинам. Если товар недоступен - передавать 0.
'productTag': 'bestPrice', // bestPrice для “Лучшей цены” и onlineOnly для “Только
онлайн заказ”, а также остальные бейджи. При наличии нескольких передавать
через разделитель “,”
'division': 'Стройматериалы', // отдел, к которому относится товар, должен
передаваться в текстовом формате
'subdivision': 'Сухие смеси и грунтовки', // подотдел, к которому относится товар,
должен передаваться в текстовом формате
'wowPrice': '1' // признак шок-цены (null если товар без шок-цены)
""",
    "GA:removeFromShoppingList": """
    sdfdf
""",
    "GA:promoClick": """
"""
}


class Image(BaseModel):
    file: str
    description: str


class Event(BaseModel):
    type: Optional[str]
    description: Optional[str] = None
    images: Optional[List[Image]]
    event_data: str
    # event_data: Dict[str, Optional[str]] = Field(default_factory=dict)

    @model_validator(mode="before")
    def set_default_event_data(cls, values):
        """Set data based on type by default"""
        event_type = values.get("type")
        if event_type:
            values.setdefault("event_data", event_type_mapper[event_type])
        return values


class Action(BaseModel):
    name: str
    description: Optional[str] = None
    events: List[Event] = Field(default_factory=list)


# Represents an ObjectId field in the database.
# It will be represented as a `str` on the model so that it can be serialized to JSON.
PyObjectId = Annotated[str, BeforeValidator(str)]


class Assignment(BaseModel):

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )

    name: str
    author: Optional[str] = None
    description: Optional[str] = None
    created_at: str = Field(default=dt.datetime.now().isoformat())
    updated_at: str = Field(default=dt.datetime.now().isoformat())
    actions: List[Action] = Field(default_factory=Action)


assignment_default = Assignment(
    **{
        "name": "New Assignment",
        "author": "author@ogurkova_castorama.com",
        "description": f"""ОЧЕНЬ ВАЖНО!!! Все события, особенно GA:pageview должны отрабатывать после
загрузки GTM DOM, в противном случае не будет слушателей разметки и данные
уйдут в пустоту.

События следует отправлять на уровень document (НЕ document.body) и
генерировать их через dispatchEvent.

Также необходимо добавить логирование в консоль, если enabledLogAnalytics = 1
При клике на кнопку или ссылку (clickButton, clickProduct, promoClick) - учитывать
все клики, которые приводят к переходу - левой кнопкой мыши, по колесику мыши.
Желтым выделены новые события или параметры, которые еще не внедрены на прод
и ожидают внедрения со стороны разработки или пост-ревью со стороны аналитики.
""",
        "created_at": dt.datetime.now().isoformat(),
        "updated_at": dt.datetime.now().isoformat(),
        "actions": []
    }
)


def assignment_to_js_schema() -> dict:

    """
    generate json Schema for json-form creator
    https://github.com/json-editor/json-editor?tab=readme-ov-file
    """

    schema = {
        "title": "Technical Assignment",
        "type": "object",
        "properties": {
            "_id": {
                "title": "id",
                "type": "string",
                "readonly": True,
                "propertyOrder": 100000
            },
            "name": {
                "title": "Assignment Name",
                "type": "string",
                "propertyOrder": 100010,
            },
            "author": {
                "title": "Author Email",
                "type": "string",
                "propertyOrder": 100020
            },
            "created_at": {
                "title": "Create dtm",
                "type": "string",
                "readonly": True,
                "propertyOrder": 100030
            },
            "updated_at": {
                "title": "Update dtm",
                "type": "string",
                "readonly": True,
                "propertyOrder": 100040
            },
            "description": {
                "type": "string",
                "title": "Assignment description",
                "propertyOrder": 100050,
                "format": "markdown",
            },
            "actions": {
                "title": "Actions",
                "type": "array",
                "propertyOrder": 100060,
                "items": {
                    "type": "object",
                    "title": "Action",
                    "properties": {
                        "name": {
                            "type": "string",
                            "title": "Action name",
                            "propertyOrder": 100100,
                        },
                        "description": {
                            "type": "string",
                            "title": "Action description",
                            "propertyOrder": 100200,
                            "format": "xhtml",
                            "options": {
                                "wysiwyg": True
                            }
                        },
                        "events": {
                            "type": "array",
                            "title": "Action events",
                            "propertyOrder": 100300,
                            "items": {
                                "type": "object",
                                "title": "Event",
                                "properties": {
                                    "images": {
                                        "type": "array",
                                        "format": "table",
                                        "propertyOrder": 100400,
                                        "title": "Event Images",
                                        "items": {
                                            "type": "object",
                                            "title": "Image",
                                            "format": "grid",
                                            "properties": {
                                                "file": {
                                                    "type": "string",
                                                    "title": "File",
                                                    "media": {
                                                        "binaryEncoding": "base64",
                                                        "type": "img/png"
                                                    },
                                                    "options": {
                                                        "grid_columns": 6,
                                                        "multiple": True
                                                    }
                                                },
                                                "description": {
                                                    "type": "string",
                                                    "title": "Description",
                                                    "options": {
                                                        "grid_columns": 6
                                                    }
                                                }
                                            }
                                        }
                                    },
                                    "type": {
                                        "type": "string",
                                        "title": "Event Type",
                                        "enum": [key for key in event_type_mapper],
                                        "propertyOrder": 100500,
                                    },
                                    "description": {
                                        "type": "string",
                                        "title": "Event Description",
                                        "propertyOrder": 100600,
                                        "default": """Событие должно срабатывать при ХХХ.
При срабатывании данного события должны передаваться следующие данные:""",
                                        "format": "xhtml",
                                        "options": {
                                            "wysiwyg": True
                                        }
                                    },
                                    "event_data": {
                                        "type": "string",
                                        "title": "Event Data",
                                        "propertyOrder": 100700,
                                        "format": "xhtml",
                                        "options": {
                                            "wysiwyg": True
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    return schema

