import asyncpg
from asyncpg.exceptions import UniqueViolationError
from typing import List, Tuple, Union, Optional

_pool: Union[asyncpg.Pool, None] = None

async def init_db(dsn: str):
    global _pool
    _pool = await asyncpg.create_pool(dsn)
    async with _pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS contracts (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                network TEXT NOT NULL,
                address TEXT NOT NULL,
                name TEXT,
                UNIQUE (user_id, network, address)
            );
        """)

async def save_contract(user_id: int, network: str, address: str, name: Optional[str]) -> bool:
    """Сохранить новый контракт в PostgreSQL. Возвращает True при успехе, False если уже существует."""
    try:
        await _pool.execute(
            "INSERT INTO contracts(user_id, network, address, name) VALUES($1, $2, $3, $4)",
            user_id, network, address, name
        )
        return True
    except UniqueViolationError:
        return False

async def get_user_contracts(user_id: int) -> List[Tuple[str, str, Optional[str]]]:
    """Получить все контракты пользователя (network, address, name)."""
    rows = await _pool.fetch(
        "SELECT network, address, name FROM contracts WHERE user_id = $1 ORDER BY id",
        user_id
    )
    return [(r['network'], r['address'], r['name']) for r in rows]

async def delete_contract(user_id: int, network: str, address: str) -> bool:
    """Удалить контракт пользователя. Возвращает True если строка удалена, False иначе."""
    result = await _pool.execute(
        "DELETE FROM contracts WHERE user_id = $1 AND network = $2 AND address = $3",
        user_id, network, address
    )
    return result != 'DELETE 0'

async def get_all_contracts() -> List[Tuple[int, str, str, Optional[str]]]:
    """Получить все записи (user_id, network, address, name) для фонового мониторинга."""
    rows = await _pool.fetch(
        "SELECT user_id, network, address, name FROM contracts ORDER BY id"
    )
    return [(r['user_id'], r['network'], r['address'], r['name']) for r in rows]

# --- Функции для привязки Telegram --- 

async def get_user_by_verification_code(code: str) -> Optional[asyncpg.Record]:
    """Найти пользователя по коду верификации."""
    query = "SELECT * FROM users WHERE verification_code = $1 AND is_verified = FALSE LIMIT 1"
    user_record = await _pool.fetchrow(query, code)
    return user_record

async def update_user_telegram_link(telegram_user_id: int, user_id: int) -> bool:
    """Обновить telegram_user_id и статус верификации пользователя."""
    query = """
        UPDATE users 
        SET telegram_user_id = $1, is_verified = TRUE, verification_code = NULL
        WHERE id = $2 AND (telegram_user_id IS NULL OR telegram_user_id != $1)
        RETURNING id; 
        """ 
    try:
        result = await _pool.fetchval(query, telegram_user_id, user_id)
        return result is not None
    except Exception as e:
        print(f"Error updating user telegram link: {e}")
        return False