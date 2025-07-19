from typing import TypeVar, Generic, Type, Optional, List, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db
    
    async def get(self, id: Any) -> Optional[ModelType]:
        """Get a single record by ID."""
        return await self.db.get(self.model, id)
    
    async def get_multi(
        self, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_desc: bool = False
    ) -> List[ModelType]:
        """Get multiple records with pagination and filtering."""
        stmt = select(self.model)
        
        # Apply filters
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    if isinstance(value, list):
                        stmt = stmt.where(getattr(self.model, key).in_(value))
                    else:
                        stmt = stmt.where(getattr(self.model, key) == value)
        
        # Apply ordering
        if order_by and hasattr(self.model, order_by):
            order_column = getattr(self.model, order_by)
            if order_desc:
                stmt = stmt.order_by(order_column.desc())
            else:
                stmt = stmt.order_by(order_column)
        
        # Apply pagination
        stmt = stmt.offset(skip).limit(limit)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def create(self, obj_in: CreateSchemaType, **kwargs) -> ModelType:
        """Create a new record."""
        obj_data = obj_in.dict() if hasattr(obj_in, 'dict') else obj_in
        obj_data.update(kwargs)
        
        db_obj = self.model(**obj_data)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj
    
    async def update(
        self, 
        db_obj: ModelType, 
        obj_in: UpdateSchemaType | Dict[str, Any]
    ) -> ModelType:
        """Update an existing record."""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj
    
    async def delete(self, id: Any) -> bool:
        """Delete a record by ID."""
        db_obj = await self.get(id)
        if db_obj:
            await self.db.delete(db_obj)
            await self.db.commit()
            return True
        return False
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records with optional filtering."""
        stmt = select(func.count(self.model.id))
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    if isinstance(value, list):
                        stmt = stmt.where(getattr(self.model, key).in_(value))
                    else:
                        stmt = stmt.where(getattr(self.model, key) == value)
        
        result = await self.db.execute(stmt)
        return result.scalar()
    
    async def exists(self, id: Any) -> bool:
        """Check if a record exists by ID."""
        stmt = select(self.model.id).where(self.model.id == id)
        result = await self.db.execute(stmt)
        return result.scalar() is not None
    
    async def get_by_field(self, field: str, value: Any) -> Optional[ModelType]:
        """Get a record by a specific field value."""
        if not hasattr(self.model, field):
            return None
        
        stmt = select(self.model).where(getattr(self.model, field) == value)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_multi_by_field(
        self, 
        field: str, 
        value: Any,
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        """Get multiple records by a specific field value."""
        if not hasattr(self.model, field):
            return []
        
        stmt = select(self.model).where(getattr(self.model, field) == value)
        stmt = stmt.offset(skip).limit(limit)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def bulk_create(self, objects: List[CreateSchemaType]) -> List[ModelType]:
        """Create multiple records in bulk."""
        db_objects = []
        for obj_in in objects:
            obj_data = obj_in.dict() if hasattr(obj_in, 'dict') else obj_in
            db_obj = self.model(**obj_data)
            db_objects.append(db_obj)
        
        self.db.add_all(db_objects)
        await self.db.commit()
        
        for db_obj in db_objects:
            await self.db.refresh(db_obj)
        
        return db_objects
    
    async def bulk_update(
        self, 
        ids: List[Any], 
        update_data: Dict[str, Any]
    ) -> int:
        """Update multiple records in bulk."""
        stmt = select(self.model).where(self.model.id.in_(ids))
        result = await self.db.execute(stmt)
        objects = result.scalars().all()
        
        updated_count = 0
        for obj in objects:
            for field, value in update_data.items():
                if hasattr(obj, field):
                    setattr(obj, field, value)
            updated_count += 1
        
        await self.db.commit()
        return updated_count
    
    async def bulk_delete(self, ids: List[Any]) -> int:
        """Delete multiple records in bulk."""
        stmt = select(self.model).where(self.model.id.in_(ids))
        result = await self.db.execute(stmt)
        objects = result.scalars().all()
        
        deleted_count = 0
        for obj in objects:
            await self.db.delete(obj)
            deleted_count += 1
        
        await self.db.commit()
        return deleted_count
    
    async def search(
        self, 
        query: str, 
        fields: List[str],
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        """Search records across multiple fields."""
        if not query or not fields:
            return []
        
        search_conditions = []
        for field in fields:
            if hasattr(self.model, field):
                field_attr = getattr(self.model, field)
                search_conditions.append(field_attr.ilike(f"%{query}%"))
        
        if not search_conditions:
            return []
        
        stmt = select(self.model).where(or_(*search_conditions))
        stmt = stmt.offset(skip).limit(limit)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_paginated(
        self,
        page: int = 1,
        size: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        search_query: Optional[str] = None,
        search_fields: Optional[List[str]] = None,
        order_by: Optional[str] = None,
        order_desc: bool = False
    ) -> Dict[str, Any]:
        """Get paginated results with search and filtering."""
        skip = (page - 1) * size
        
        # Build base query
        stmt = select(self.model)
        count_stmt = select(func.count(self.model.id))
        
        # Apply filters
        conditions = []
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    if isinstance(value, list):
                        conditions.append(getattr(self.model, key).in_(value))
                    else:
                        conditions.append(getattr(self.model, key) == value)
        
        # Apply search
        if search_query and search_fields:
            search_conditions = []
            for field in search_fields:
                if hasattr(self.model, field):
                    field_attr = getattr(self.model, field)
                    search_conditions.append(field_attr.ilike(f"%{search_query}%"))
            
            if search_conditions:
                conditions.append(or_(*search_conditions))
        
        # Apply all conditions
        if conditions:
            stmt = stmt.where(and_(*conditions))
            count_stmt = count_stmt.where(and_(*conditions))
        
        # Apply ordering
        if order_by and hasattr(self.model, order_by):
            order_column = getattr(self.model, order_by)
            if order_desc:
                stmt = stmt.order_by(order_column.desc())
            else:
                stmt = stmt.order_by(order_column)
        
        # Get total count
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar()
        
        # Apply pagination
        stmt = stmt.offset(skip).limit(size)
        
        # Get items
        result = await self.db.execute(stmt)
        items = result.scalars().all()
        
        # Calculate pagination info
        pages = (total + size - 1) // size
        has_next = page < pages
        has_prev = page > 1
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "size": size,
            "pages": pages,
            "has_next": has_next,
            "has_prev": has_prev
        }
