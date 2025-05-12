from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from sqlmodel import select
import logging

from app.schemas import ContractCreate, ContractRead, ContractDelete
from app.auth.jwt import get_current_user
from app.core.db import get_session
from app.models import Contract, User
from app.contracts.get_contract_name import get_contract_name, ContractVerificationError, NetworkAccessError

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/add", response_model=ContractRead)
async def add_contract(
    data: ContractCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    if not current_user.is_verified or current_user.telegram_user_id is None:
        raise HTTPException(status_code=400, detail="Требуется привязка Telegram для добавления контрактов")
    
    existing_contract_stmt = select(Contract).where(
        Contract.user_id == current_user.telegram_user_id,
        Contract.network == data.network,
        Contract.address == data.address
    )
    result = await session.exec(existing_contract_stmt)
    existing_contract = result.first()

    if existing_contract:
        raise HTTPException(
            status_code=409,
            detail=f"Контракт {data.address} в сети {data.network} уже отслеживается."
        )

    name = None
    try:
        name = await get_contract_name(data.address, data.network)
        if name is None:
             raise HTTPException(
                 status_code=404, 
                 detail=f"Контракт с адресом {data.address} не найден в сети {data.network}."
            )

    except ContractVerificationError as e:
        raise HTTPException(
            status_code=400, 
            detail=f"Проблема с верификацией контракта {data.address} в сети {data.network}: {e}"
        )
    except NetworkAccessError as e:
        raise HTTPException(
            status_code=503, 
            detail=f"Временная ошибка при проверке контракта {data.address} в сети {data.network}: {e}"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error adding contract {data.address} for network {data.network}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Внутренняя ошибка при проверке контракта {data.address}."
        )

    contract = Contract(
        address=data.address,
        network=data.network,
        name=name,
        user_id=current_user.telegram_user_id
    )
    session.add(contract)
    await session.commit()
    await session.refresh(contract)
    return contract

@router.delete("/{contract_id}", status_code=204)
async def delete_contract(
    contract_id: int = Path(..., title="The ID of the contract to delete", ge=1),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    contract_to_delete = await session.get(Contract, contract_id)

    if not contract_to_delete:
        raise HTTPException(status_code=404, detail=f"Контракт с ID {contract_id} не найден.")

    if not current_user.telegram_user_id or contract_to_delete.user_id != current_user.telegram_user_id:
        logger.warning(f"User {current_user.id} (TG: {current_user.telegram_user_id}) attempted to delete contract {contract_id} owned by user {contract_to_delete.user_id}")
        raise HTTPException(status_code=403, detail="У вас нет прав на удаление этого контракта.")

    try:
        await session.delete(contract_to_delete)
        await session.commit()
        logger.info(f"Contract {contract_id} ({contract_to_delete.address} on {contract_to_delete.network}) deleted successfully by user {current_user.id}")
        return None
    except Exception as e:
        await session.rollback()
        logger.error(f"Error deleting contract {contract_id} for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при удалении контракта.")

@router.get("/", response_model=List[ContractRead])
async def list_contracts(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    stmt = select(Contract).where(Contract.user_id == current_user.telegram_user_id)
    result = await session.exec(stmt)
    return result.all()
