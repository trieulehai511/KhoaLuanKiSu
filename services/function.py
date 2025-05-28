from sqlalchemy.orm import Session
from models.model import SysFunction
from schemas.function import FunctionCreate, FunctionUpdate, FunctionResponse
from fastapi import HTTPException, status
from datetime import datetime
from typing import List

def create_function(db: Session, function: FunctionCreate, user_id: str) -> FunctionResponse:
    """
    Tạo mới một chức năng (function).
    """
    # Kiểm tra xem chức năng đã tồn tại chưa
    existing_function = db.query(SysFunction).filter(SysFunction.name == function.name).first()
    if existing_function:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Function with this name already exists"
        )

    # Tạo mới chức năng
    db_function = SysFunction(
        name=function.name,
        path=function.path,
        type=function.type,
        parent_id=function.parent_id,
        description=function.description,
        status=function.status if function.status is not None else 1,  # Mặc định là enabled
        created_by=user_id,
        create_datetime=datetime.utcnow(),
        update_datetime=datetime.utcnow()
    )
    db.add(db_function)
    db.commit()
    db.refresh(db_function)
    return FunctionResponse.from_orm(db_function)

def update_function(db: Session, function_id: int, function: FunctionUpdate) -> FunctionResponse:
    """
    Cập nhật thông tin chức năng (function).
    """
    db_function = db.query(SysFunction).filter(SysFunction.id == function_id).first()
    if not db_function:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Function not found"
        )

    # Cập nhật thông tin
    for key, value in function.dict(exclude_unset=True).items():
        setattr(db_function, key, value)
    db_function.update_datetime = datetime.utcnow()

    db.commit()
    db.refresh(db_function)
    return FunctionResponse.from_orm(db_function)

def get_function_by_id(db: Session, function_id: int) -> FunctionResponse:
    """
    Lấy thông tin chức năng theo ID.
    """
    db_function = db.query(SysFunction).filter(SysFunction.id == function_id).first()
    if not db_function:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Function not found"
        )
    return db_function

def get_all_functions(db: Session) -> List[FunctionResponse]:
    """
    Lấy danh sách tất cả chức năng.
    """
    functions = db.query(SysFunction).all()
    return [FunctionResponse.from_orm(function) for function in functions]

def delete_function(db: Session, function_id: int):
    """
    Xóa một chức năng (function).
    """
    db_function = db.query(SysFunction).filter(SysFunction.id == function_id).first()
    if not db_function:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Function not found"
        )
    db.delete(db_function)
    db.commit()
    return {"message": "Function deleted successfully"}

def get_function_tree_with_parent_name(db: Session) -> List[FunctionResponse]:
    """
    Lấy danh sách chức năng dưới dạng cây (tree structure) và thêm tên của chức năng cha (parent_name).
    """
    # Lấy tất cả các chức năng từ cơ sở dữ liệu
    functions = db.query(SysFunction).all()

    # Chuyển đổi danh sách chức năng thành dictionary để dễ dàng xử lý
    function_dict = {function.id: FunctionResponse(
        id=function.id,
        name=function.name,
        path=function.path,
        type=function.type,
        parent_id=function.parent_id,
        description=function.description,
        status="Hoạt động" if function.status == 1 else "Ngừng hoạt động",
        create_datetime=function.create_datetime,
        update_datetime=function.update_datetime,
        children=[],
        parent_name=None  # Thêm trường parent_name mặc định là None
    ) for function in functions}

    # Gắn tên của chức năng cha (parent_name)
    for function in function_dict.values():
        if function.parent_id:
            parent = function_dict.get(function.parent_id)
            if parent:
                function.parent_name = parent.name

    # Xây dựng cấu trúc cây
    tree = []
    for function in function_dict.values():
        if function.parent_id is None:
            tree.append(function)
        else:
            parent = function_dict.get(function.parent_id)
            if parent:
                parent.children.append(function)

    return tree