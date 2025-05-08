# minimal_main.py
import sys
print("DEBUG SYS.PATH:", sys.path)  # Dòng debug
print("-----") # Để dễ nhìn
from fastapi import FastAPI
from pydantic import BaseModel # Quan trọng: import BaseModel từ pydantic
app = FastAPI()

# Một model đơn giản có thể có forward reference (để kiểm tra)
class Item(BaseModel):
    name: str
    # Nếu bạn muốn test kỹ hơn về forward ref, thêm dòng sau:
    # sub_item: 'SubItem' = None 
    pass # Giữ đơn giản nhất có thể ban đầu

# class SubItem(BaseModel):
# id: int
    # pass

# Nếu bạn đã thêm sub_item ở trên, bỏ comment khối này và dòng Item.model_rebuild()
# if 'SubItem' in locals(): # Kiểm tra SubItem có được định nghĩa không
# Item.model_rebuild() # Trong Pydantic V1 là update_forward_refs()

@app.get("/")
async def read_root():
    return {"Hello": "World"}

print("Minimal FastAPI app object created and imports successful.")