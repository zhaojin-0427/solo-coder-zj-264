from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import date, datetime
from ..database import get_db
from .. import models, schemas

router = APIRouter()


def calc_days_left(flower: models.Flower) -> int:
    if flower.purchase_date:
        elapsed = (date.today() - flower.purchase_date).days
        return flower.shelf_life_days - elapsed
    return flower.shelf_life_days


def enrich_flower(flower: models.Flower) -> schemas.Flower:
    days_left = calc_days_left(flower)
    data = schemas.Flower.model_validate(flower)
    data.days_left = days_left
    data.is_warning = days_left <= flower.warning_threshold
    return data


@router.get("", response_model=List[schemas.Flower])
def list_flowers(
    skip: int = 0, limit: int = 100, warning_only: bool = False, db: Session = Depends(get_db)
):
    flowers = db.query(models.Flower).offset(skip).limit(limit).all()
    result = [enrich_flower(f) for f in flowers]
    if warning_only:
        result = [f for f in result if f.is_warning]
    return result


@router.get("/{flower_id}", response_model=schemas.Flower)
def get_flower(flower_id: int, db: Session = Depends(get_db)):
    flower = db.query(models.Flower).filter(models.Flower.id == flower_id).first()
    if not flower:
        raise HTTPException(status_code=404, detail="花材不存在")
    return enrich_flower(flower)


@router.post("", response_model=schemas.Flower)
def create_flower(flower_in: schemas.FlowerCreate, db: Session = Depends(get_db)):
    flower = models.Flower(**flower_in.model_dump())
    db.add(flower)
    db.commit()
    db.refresh(flower)
    return enrich_flower(flower)


@router.put("/{flower_id}", response_model=schemas.Flower)
def update_flower(
    flower_id: int, flower_in: schemas.FlowerUpdate, db: Session = Depends(get_db)
):
    flower = db.query(models.Flower).filter(models.Flower.id == flower_id).first()
    if not flower:
        raise HTTPException(status_code=404, detail="花材不存在")
    update_data = flower_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(flower, key, value)
    db.commit()
    db.refresh(flower)
    return enrich_flower(flower)


@router.delete("/{flower_id}")
def delete_flower(flower_id: int, db: Session = Depends(get_db)):
    flower = db.query(models.Flower).filter(models.Flower.id == flower_id).first()
    if not flower:
        raise HTTPException(status_code=404, detail="花材不存在")
    db.delete(flower)
    db.commit()
    return {"message": "删除成功"}
