from fastapi import FastAPI, Depends, Request
from sqlalchemy.orm import Session
from model import ReviewTable, UserTable, StoreTable, OrderTable, MenuTable
from db import session
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import os
import uvicorn

order = FastAPI()

order.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False, 
    allow_methods=["*"],
    allow_headers=["*"],
)

order.add_middleware(SessionMiddleware, secret_key="your-secret-key")

def get_db():
    db = session()
    try:
        yield db
    finally:
        db.close()

#로그인 상태 확인, 로그인 중인 유저 아이디 반환
@order.get("/check_login/")
async def check_login(request: Request):
    # 세션에서 사용자 정보 확인
    if "user_id" not in request.session:
        return False
    
    return {"user_id": f"{request.session['user_id']}"}

#총 수량 반환. 유저 아이디일치, 오더 테이블에서 완료 여부 false 만 계산 반환
@order.get("/total_count/{user_id}")
async def read_total_count(user_id: str, db: Session = Depends(get_db)):
    orders = db.query(
                        OrderTable.quantity,
                        OrderTable.is_completed,
                        UserTable.user_id
                    ).join(UserTable, UserTable.user_id == OrderTable.user_id).filter(OrderTable.user_id == user_id, OrderTable.is_completed == False).all()
    
    counts = [row[0] for row in orders] 
    total = sum(counts)
    
    return total

#주문 메뉴 이름, 수량 딕셔너리 반환
@order.get("/order_list/{user_id}")
async def read_order_list(user_id: str, db: Session = Depends(get_db)):
    orders = db.query(
                        OrderTable.quantity,
                        OrderTable.is_completed,
                        MenuTable.menu_name,
                        MenuTable.price,
                        UserTable.user_id
                    ).join(MenuTable, MenuTable.menu_id == OrderTable.menu_id) \
                    .join(UserTable, UserTable.user_id == OrderTable.user_id) \
                    .filter(OrderTable.user_id == user_id, OrderTable.is_completed == False).all()
    
    order_list = [
        {
            "menu_name": order.menu_name,
            "quantity": order.quantity,
        }
        for order in orders
    ]
    
    return order_list

#총 금액 반환
@order.get("/total_price/{user_id}")
async def read_total_price(user_id: str, db: Session = Depends(get_db)):
    orders = db.query(
                        OrderTable.quantity,
                        OrderTable.is_completed,
                        MenuTable.price,
                        UserTable.user_id
                    ).join(MenuTable, MenuTable.menu_id == OrderTable.menu_id) \
                    .join(UserTable, UserTable.user_id == OrderTable.user_id) \
                    .filter(OrderTable.user_id == user_id, OrderTable.is_completed == False).all()
    
    total_price = sum(row[0] * row[2] for row in orders)
    
    return total_price

#주문하기 버튼 처리
@order.put("/pay/{user_id}")
async def update_state(user_id: str, db: Session = Depends(get_db)):
    unpaid_orders = db.query(OrderTable).filter(
        OrderTable.user_id == user_id,
        OrderTable.is_completed == False
    ).all()
    
    for order in unpaid_orders:
        order.is_completed = True

    db.commit()

if __name__ == "__order__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)