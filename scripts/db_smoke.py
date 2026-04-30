import asyncio

import asyncpg


async def main() -> None:
    # matches .env defaults
    conn = await asyncpg.connect(
        user="postgres",
        password="1234",
        database="finance_analyzer_db",
        host="localhost",
        port=5432,
    )
    try:
        tables = await conn.fetchval(
            "select count(*) from information_schema.tables where table_schema='public'"
        )
        print("tables", tables)
        uuid_ok = await conn.fetchval("select gen_random_uuid() is not null")
        print("gen_random_uuid_ok", uuid_ok)
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())

