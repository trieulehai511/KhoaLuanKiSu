from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from db.database import get_db
from models.model import User
from schemas.function import FunctionCreate, FunctionUpdate, FunctionResponse
from services.function import (
    create_function,
    get_function_by_id,
    get_function_tree_with_parent_name,
    update_function,
    get_all_functions,
    delete_function
)
from routers.auth import get_current_user


router = APIRouter(
    prefix="/functions",
    tags=["functions"]
)

@router.post("/", response_model=FunctionResponse)
def create_function_endpoint(
    function: FunctionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return create_function(db, function, user.id)

@router.get("/get_by_id/{function_id}", response_model=FunctionResponse)
def get_function_by_id_endpoint(function_id: int, db: Session = Depends(get_db)):
    """
    API để lấy thông tin một chức năng (function) theo ID.
    """
    return get_function_by_id(db, function_id)


@router.put("/{function_id}", response_model=FunctionResponse)
def update_function_endpoint(
    function_id: int,
    function: FunctionUpdate,
    db: Session = Depends(get_db)
):
    """
    API để cập nhật thông tin một chức năng (function).
    """
    return update_function(db, function_id, function)

# @router.get("/{function_id}", response_model=FunctionResponse)
# def get_function_endpoint(
#     function_id: int,
#     db: Session = Depends(get_db)
# ):
#     """
#     API để lấy thông tin một chức năng (function) theo ID.
#     """
#     return get_function_by_id(db, function_id)

@router.get("/", response_model=List[FunctionResponse])
def get_all_functions_endpoint(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    API để lấy danh sách tất cả chức năng (functions).
    """
    return get_all_functions(db)

@router.delete("/{function_id}")
def delete_function_endpoint(
    function_id: int,
    db: Session = Depends(get_db)
):
    """
    API để xóa một chức năng (function) theo ID.
    """
    return delete_function(db, function_id)


def remove_empty_children(obj):
    if isinstance(obj, list):
        return [remove_empty_children(item) for item in obj]
    elif isinstance(obj, dict):
        if 'children' in obj:
            if not obj['children']:
                obj.pop('children')
            else:
                obj['children'] = remove_empty_children(obj['children'])
        return {k: remove_empty_children(v) for k, v in obj.items()}
    return obj

def remove_empty_children(obj):
    if isinstance(obj, list):
        return [remove_empty_children(item) for item in obj]
    elif isinstance(obj, dict):
        children = obj.get('children')
        if children is not None:
            if isinstance(children, list) and not children:
                obj.pop('children')
            else:
                obj['children'] = remove_empty_children(children)
        return {k: remove_empty_children(v) for k, v in obj.items()}
    return obj


@router.get("/tree", response_model=List[FunctionResponse])
def get_function_tree_with_parent_name_endpoint(db: Session = Depends(get_db),user: User = Depends(get_current_user)):
    """
    API để lấy danh sách chức năng dưới dạng cây và thêm tên của chức năng cha.
    """
    return get_function_tree_with_parent_name(db)
