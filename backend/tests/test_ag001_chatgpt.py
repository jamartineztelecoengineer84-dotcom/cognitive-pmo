"""
ARQ-04 F6c — Test AG-001 Dispatcher con ChatGPT Codex Provider (gpt-5.4)
Ejecutar dentro del container:
  docker exec cognitive-pmo-api-1 python /app/tests/test_ag001_chatgpt.py
"""
import asyncio
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def main():
    import asyncpg

    # 1. Read OAuth token from DB
    print("=" * 60)
    print("ARQ-04 F6c — AG-001 via ChatGPT Codex (gpt-5.4)")
    print("=" * 60)

    conn = await asyncpg.connect(
        host="postgres", port=5432, database="cognitive_pmo",
        user="jose_admin", password="REDACTED-old-password"
    )
    row = await conn.fetchrow(
        "SELECT config_json FROM primitiva.llm_provider_config WHERE provider_name = 'openai'"
    )
    config = json.loads(row["config_json"])
    token = config.get("oauth_token", "")
    if not token:
        print("ERROR: No oauth_token in DB config for openai provider")
        return
    print(f"1. OAuth token loaded ({len(token)} chars, expires in token)")

    # 2. Set env var so ChatGPTCodexProvider picks it up
    os.environ["CHATGPT_OAUTH_TOKEN"] = token

    # 3. Create AG-001 config with chatgpt provider
    from agents.config import AgentConfig, load_prompt, AGENT_CONFIGS

    original_config = AGENT_CONFIGS["AG-001"]
    chatgpt_config = AgentConfig(
        agent_id="AG-001-GPT54",
        agent_name="Dispatcher (GPT-5.4 Test)",
        system_prompt=original_config.system_prompt,
        tools=original_config.tools,
        model="gpt-5.4",
        max_tokens=original_config.max_tokens,
        temperature=original_config.temperature,
        cache_system=False,  # Codex endpoint doesn't support cache_control
        provider="chatgpt",
    )
    print(f"2. Config created: provider={chatgpt_config.provider}, model={chatgpt_config.model}")
    print(f"   Tools: {[t['name'] for t in chatgpt_config.tools]}")

    # 4. Create engine with DB pool
    from database import get_pool, init_pool
    pool = get_pool()
    if not pool:
        await init_pool()
        pool = get_pool()

    from agents.engine import AgentEngine
    engine = AgentEngine(chatgpt_config, pool)
    print(f"3. Engine created with provider: {type(engine.provider).__name__}")

    # 5. Invoke AG-001
    test_msg = "Caída del servidor Oracle de producción, afecta a Core Banking"
    session_id = "test-f6c-gpt54"
    print(f"\n4. Invoking AG-001 with: '{test_msg}'")
    print("-" * 60)

    t0 = time.monotonic()
    try:
        result = await engine.invoke(test_msg, session_id)
        elapsed = int((time.monotonic() - t0) * 1000)

        print(f"\n{'=' * 60}")
        print(f"RESULTADO ({elapsed}ms):")
        print(f"{'=' * 60}")
        print(result[:1500])
        print(f"\n--- Stats ---")
        print(f"Input tokens:  {engine.last_input_tokens}")
        print(f"Output tokens: {engine.last_output_tokens}")
        print(f"Latency:       {elapsed}ms")

        # Check for ticket and tasks
        has_ticket = "INC-" in result
        has_tasks = "tarea" in result.lower() or "Backlog" in result or "En Progreso" in result
        print(f"\n--- Verification ---")
        print(f"Has ticket ID:  {'YES' if has_ticket else 'NO'}")
        print(f"Has tasks:      {'YES' if has_tasks else 'NO'}")

        if has_ticket and has_tasks:
            print(f"\n*** AG-001 con GPT-5.4 via ChatGPT Plus: EXITO ***")
        else:
            print(f"\nPartial success — response received but may be missing ticket/tasks")

    except Exception as e:
        elapsed = int((time.monotonic() - t0) * 1000)
        print(f"\nERROR after {elapsed}ms: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

    await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
