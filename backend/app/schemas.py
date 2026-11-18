from typing import Literal
from pydantic import BaseModel, Field, ConfigDict

class Strict(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)

class SessionIn(Strict):
    name: str = Field(min_length=1,max_length=60)

class Preferences(Strict):
    aesthetics: list[str] = Field(default_factory=list,max_length=20)
    preferred_colors: list[str] = Field(default_factory=list,max_length=20)
    silhouettes: list[str] = Field(default_factory=list,max_length=20)
    garment_preferences: list[str] = Field(default_factory=list,max_length=20)
    budget: float | None = Field(default=None,gt=0,le=1000000)
    department: str | None = Field(default=None,max_length=60)
    size: str | None = Field(default=None,max_length=30)

class Location(Strict):
    latitude: float = Field(ge=-90,le=90)
    longitude: float = Field(ge=-180,le=180)
    label: str | None = Field(default=None,max_length=100)

class DailyIn(Strict):
    location: Location
    occasion: Literal['everyday','work','evening','outdoor'] = 'everyday'

class SwipeIn(Strict):
    product_id: str = Field(min_length=1,max_length=200)
    action: Literal['like','dislike','save']

class SearchIn(Strict):
    query: str = Field(min_length=2,max_length=250)
    max_price: float | None = Field(default=None,gt=0,le=1000000)
    limit: int = Field(default=12,ge=1,le=30)
    country: Literal['IN']='IN'
    currency: Literal['INR']='INR'

class Product(Strict):
    id: str = Field(min_length=1,max_length=200)
    title: str = Field(min_length=1,max_length=500)
    brand: str | None = None
    category: str | None = None
    colors: list[str] = Field(default_factory=list)
    aesthetics: list[str] = Field(default_factory=list)
    fits: list[str] = Field(default_factory=list)
    weather_tags: list[str] = Field(default_factory=list)
    functional_tags: list[str] = Field(default_factory=list)
    size: str | None = None
    model_number: str | None = None
    gtin: str | None = None
    price: float | None = Field(default=None,ge=0)
    shipping_cost: float | None = Field(default=None,ge=0)
    currency: str = 'INR'
    image_url: str | None = None
    merchant_url: str | None = None
    merchant: str | None = None
    source: str = 'submitted'
    is_demo: bool = False
    observed_at: str | None = None

class MatchIn(Strict):
    target: Product
    candidates: list[Product] = Field(max_length=50)

class OutfitIn(Strict):
    product_id: str
    budget: float | None = Field(default=None,gt=0)

class AgentIn(Strict):
    message: str = Field(min_length=2,max_length=2000)
    location: Location | None = None
    previous_run_id: str | None = Field(default=None,max_length=100)
    selected_product_id: str | None = Field(default=None,max_length=200)

class VisionImage(Strict):
    aesthetics: list[Literal['minimalist','streetwear','smart_casual','formal','athleisure','vintage','contemporary','casual','romantic','outdoor','preppy','bohemian']]
    preferred_colors: list[str]
    silhouettes: list[str]
    garment_preferences: list[str]
    visible_materials: list[str]
    uncertainty: list[str]

class VisionResult(Strict):
    images: list[VisionImage] = Field(min_length=5,max_length=5)

class PaletteIn(Strict):
    undertone: Literal['warm','cool','neutral','unsure']
    consent: bool
    preference: Literal['muted','vibrant','balanced'] = 'balanced'

class Inspiration(Strict):
    name: str = Field(min_length=1,max_length=80)
    tags: list[str] = Field(default_factory=list,max_length=10)

class InspirationsIn(Strict):
    inspirations: list[Inspiration] = Field(max_length=20)

class HairIn(Strict):
    length: Literal['short','medium','long'] = 'medium'
    texture: Literal['straight','wavy','curly','coily','unsure'] = 'unsure'
    goal: str = Field(default='low-maintenance everyday styling',max_length=400)

class AvatarDesign(Strict):
    top_color: str = Field(pattern=r'^#[0-9A-Fa-f]{6}$')
    bottom_color: str = Field(pattern=r'^#[0-9A-Fa-f]{6}$')
    shoe_color: str = Field(pattern=r'^#[0-9A-Fa-f]{6}$')
    backdrop_color: str = Field(pattern=r'^#[0-9A-Fa-f]{6}$')
    silhouette: Literal['relaxed','tailored','oversized']
    explanation: str = Field(min_length=1,max_length=500)


class GarmentAnalysis(Strict):
    title: str = Field(min_length=1,max_length=120)
    category: Literal['tops','bottoms','footwear','one-pieces','accessories']
    colors: list[str] = Field(max_length=6)
    aesthetics: list[Literal['minimalist','streetwear','smart_casual','formal','athleisure','vintage','contemporary','casual','romantic','outdoor','preppy','bohemian']] = Field(max_length=5)
    fit: Literal['relaxed','oversized','regular','straight','slim','tailored','unknown']
    uncertainty: list[str] = Field(max_length=8)
