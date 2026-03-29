#!/usr/bin/env python3
"""
Лаунчер: запускает gen_batch_v4.py на 4 ключах параллельно.
Каждый ключ пишет в свою папку, но проверяет articles_v4 чтобы не дублировать.

Запуск:
  python launch_gen.py
"""
import subprocess
import sys
import os

SCRIPT = os.path.join(os.path.dirname(__file__), "gen_batch_v4.py")
BASE_DIR = r"B:\antigravity\dori\site1_tv"
CHECK_DIR = os.path.join(BASE_DIR, "articles_v4")

KEYS = [
    {
        "key": "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",
        "output": os.path.join(BASE_DIR, "articles_v4_key1"),
    },
    {
        "key": "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",
        "output": os.path.join(BASE_DIR, "articles_v4_key2"),
    },
    {
        "key": "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",
        "output": os.path.join(BASE_DIR, "articles_v4_key3"),
    },
    {
        "key": "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",
        "output": os.path.join(BASE_DIR, "articles_v4_key4"),
    },
]


def main():
    processes = []

    for i, cfg in enumerate(KEYS):
        os.makedirs(cfg["output"], exist_ok=True)

        env = os.environ.copy()
        env["NVIDIA_API_KEY"] = cfg["key"]
        env["OUTPUT_DIR"] = cfg["output"]
        env["CHECK_DIR"] = CHECK_DIR

        # Также проверяем папки ДРУГИХ ключей, чтобы не дублировать между собой
        all_other_dirs = ";".join(
            k["output"] for j, k in enumerate(KEYS) if j != i
        )
        env["CHECK_EXTRA_DIRS"] = all_other_dirs

        # Шардирование: каждый ключ получает свой кусок списка запросов
        env["SHARD_ID"] = str(i)
        env["SHARD_TOTAL"] = str(len(KEYS))

        print(f"🚀 Запуск key{i+1} (shard {i+1}/{len(KEYS)}): {cfg['key'][:20]}... → {cfg['output']}")

        proc = subprocess.Popen(
            [sys.executable, SCRIPT],
            env=env,
            cwd=BASE_DIR,
        )
        processes.append((f"key{i+1}", proc))

    print(f"\n✅ Запущено {len(processes)} процессов. Ожидание завершения...\n")

    for name, proc in processes:
        proc.wait()
        status = "✅" if proc.returncode == 0 else f"❌ (code {proc.returncode})"
        print(f"  {name}: {status}")

    print("\n🏁 Все процессы завершены!")


if __name__ == "__main__":
    main()
