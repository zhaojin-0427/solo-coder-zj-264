from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from .. import models, schemas

router = APIRouter()


@router.get("", response_model=List[schemas.Bouquet])
def list_bouquets(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    bouquets = db.query(models.Bouquet).offset(skip).limit(limit).all()
    return bouquets


@router.get("/{bouquet_id}", response_model=schemas.Bouquet)
def get_bouquet(bouquet_id: int, db: Session = Depends(get_db)):
    bouquet = db.query(models.Bouquet).filter(models.Bouquet.id == bouquet_id).first()
    if not bouquet:
        raise HTTPException(status_code=404, detail="花束不存在")
    return bouquet


@router.post("", response_model=schemas.Bouquet)
def create_bouquet(bouquet_in: schemas.BouquetCreate, db: Session = Depends(get_db)):
    bouquet_data = bouquet_in.model_dump(exclude={"flowers"})
    bouquet = models.Bouquet(**bouquet_data)
    db.add(bouquet)
    db.flush()
    for f in bouquet_in.flowers:
        bf = models.BouquetFlower(
            bouquet_id=bouquet.id, flower_id=f.flower_id, quantity=f.quantity
        )
        db.add(bf)
    db.commit()
    db.refresh(bouquet)
    return bouquet


@router.put("/{bouquet_id}", response_model=schemas.Bouquet)
def update_bouquet(
    bouquet_id: int, bouquet_in: schemas.BouquetUpdate, db: Session = Depends(get_db)
):
    bouquet = db.query(models.Bouquet).filter(models.Bouquet.id == bouquet_id).first()
    if not bouquet:
        raise HTTPException(status_code=404, detail="花束不存在")
    update_data = bouquet_in.model_dump(exclude_unset=True)
    flowers_data = update_data.pop("flowers", None)
    for key, value in update_data.items():
        setattr(bouquet, key, value)
    if flowers_data is not None:
        db.query(models.BouquetFlower).filter(
            models.BouquetFlower.bouquet_id == bouquet_id
        ).delete()
        for f in flowers_data:
            bf = models.BouquetFlower(
                bouquet_id=bouquet.id, flower_id=f.flower_id, quantity=f.quantity
            )
            db.add(bf)
    db.commit()
    db.refresh(bouquet)
    return bouquet


@router.delete("/{bouquet_id}")
def delete_bouquet(bouquet_id: int, db: Session = Depends(get_db)):
    bouquet = db.query(models.Bouquet).filter(models.Bouquet.id == bouquet_id).first()
    if not bouquet:
        raise HTTPException(status_code=404, detail="花束不存在")
    db.query(models.BouquetFlower).filter(
        models.BouquetFlower.bouquet_id == bouquet_id
    ).delete()
    db.delete(bouquet)
    db.commit()
    return {"message": "删除成功"}
