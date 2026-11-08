"""Teste de ponta a ponta da API publicada (local, Docker ou Railway), pelo HTTP, como o app chama.

    $env:ASSISTENTE_URL="https://assistente-production-307b.up.railway.app"; $env:ASSISTENTE_TOKEN="<token>"
    python scripts/11_testar_api.py                       # contrato, erros e as 15 perguntas dev
    python scripts/11_testar_api.py --saida docs/execucao/api_railway_e2e.txt

Confere o contrato (saúde, 401, 422, 400, formato da resposta, cache, métricas) e manda as 15
perguntas DEV com o critério escrito de cada uma. As 45 de teste ficam para o placar (notebook 05).
O token nunca é impresso.
"""

import argparse
import os
import sys
import time
from datetime import datetime, timezone

import httpx

import _comum  # noqa: F401
from passo_genai.avaliacao import atende_criterio, carregar_teste

CAMPOS = {"resposta", "fontes", "confianca", "recusou"}


class Relatorio:
    def __init__(self):
        self.linhas, self.falhas = [], 0

    def __call__(self, texto=""):
        print(texto, flush=True)
        self.linhas.append(texto)

    def checar(self, nome, ok, detalhe=""):
        self.falhas += not ok
        self(f"[{'OK' if ok else 'FALHOU'}] {nome}" + (f"  ({detalhe})" if detalhe else ""))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default=os.getenv("ASSISTENTE_URL", "http://localhost:8002"))
    ap.add_argument("--token", default=os.getenv("ASSISTENTE_TOKEN", ""))
    ap.add_argument("--timeout", type=float, default=30)
    ap.add_argument("--saida")
    args = ap.parse_args()
    url = args.url.rstrip("/")
    auth = {"Authorization": f"Bearer {args.token}"}
    cli = httpx.Client(timeout=args.timeout)
    out = Relatorio()

    out(f"# Teste de ponta a ponta da API: {url}")
    out(f"# {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC · token omitido")

    _comum.titulo("contrato e erros"); out("\n## Contrato e erros")
    r = cli.get(f"{url}/saude")
    saude = r.json()
    out.checar("GET /saude → 200 com a base carregada", r.status_code == 200 and saude.get("status") == "ok", r.text)
    out.checar("GET /docs (Swagger) → 200", cli.get(f"{url}/docs").status_code == 200)
    corpo = {"pergunta": "oi"}
    r = cli.post(f"{url}/assistente", json=corpo)
    out.checar("sem token → 401 nao_autenticado", r.status_code == 401 and r.json().get("codigo") == "nao_autenticado")
    r = cli.post(f"{url}/assistente", json=corpo, headers={"Authorization": "Bearer errado"})
    out.checar("token errado → 401", r.status_code == 401)
    r = cli.post(f"{url}/assistente", json={"pergunta": ""}, headers=auth)
    out.checar("pergunta vazia → 422 dados_invalidos", r.status_code == 422 and r.json().get("codigo") == "dados_invalidos", r.text[:120])
    r = cli.post(f"{url}/assistente", json={"pergunta": "a" * 501}, headers=auth)
    out.checar("pergunta com 501 caracteres → 422", r.status_code == 422)
    r = cli.post(f"{url}/assistente", content="{\"pergunta\": \"cal\xe7ada\"}".encode("latin-1"),
                 headers={**auth, "Content-Type": "application/json"})
    out.checar("corpo fora de UTF-8 → 400 requisicao_invalida", r.status_code == 400 and r.json().get("codigo") == "requisicao_invalida")

    _comum.titulo("perguntas dev"); out("\n## 15 perguntas dev (critério escrito de avaliacao/criterio.md)")
    itens = carregar_teste(split="dev")
    tempos, certas = [], 0
    for item in itens:
        inicio = time.perf_counter()
        r = cli.post(f"{url}/assistente", json={"pergunta": item.pergunta}, headers=auth)
        dt = time.perf_counter() - inicio
        d = r.json()
        if r.status_code != 200 or set(d) != CAMPOS:
            out.checar(f"{item.id}: resposta no contrato", False, f"HTTP {r.status_code} {r.text[:120]}")
            continue
        tempos.append(dt)
        if item.tipo == "nao_consta":
            acertou = d["recusou"]
        else:
            acertou = not d["recusou"] and atende_criterio(d["resposta"], item.criterio)
        certas += acertou
        fontes = "; ".join(f["titulo"] for f in d["fontes"]) or "—"
        out(f"\n[{'certa' if acertou else 'errada'}] {item.id} ({item.tipo}, {dt:.1f} s)")
        out(f"  P: {item.pergunta}")
        out(f"  R: {d['resposta']}")
        out(f"  fontes: {fontes} · confiança {d['confianca']} · recusou {d['recusou']}")
    out.checar("todas as respostas no contrato {resposta, fontes, confianca, recusou}", len(tempos) == len(itens))

    _comum.titulo("cache e métricas"); out("\n## Cache e métricas")
    inicio = time.perf_counter()
    cli.post(f"{url}/assistente", json={"pergunta": itens[0].pergunta.upper() + "  "}, headers=auth)
    dt_cache = time.perf_counter() - inicio
    out.checar("pergunta repetida (maiúsculas e espaços) sai do cache", dt_cache < 1.5, f"{dt_cache:.2f} s")
    r = cli.get(f"{url}/metrics")
    out.checar("GET /metrics → 200 (Prometheus)", r.status_code == 200 and "assistente_respostas_total" in r.text)
    out(r.text.strip())

    o = sorted(tempos)
    out("\n## Resumo")
    out(f"config {saude.get('config')} · modelo {saude.get('modelo')} · limiar {saude.get('limiar')} · {saude.get('trechos')} trechos")
    if o:
        out(f"latência: mediana {o[len(o) // 2]:.1f} s · máxima {o[-1]:.1f} s · {sum(t > 15 for t in o)} acima de 15 s")
    out(f"perguntas dev certas pelo critério: {certas}/{len(itens)}")
    out(f"checagens que falharam: {out.falhas}")

    if args.saida:
        texto = "\n".join(out.linhas) + "\n"
        assert not args.token or args.token not in texto
        with open(args.saida, "w", encoding="utf-8") as f:
            f.write(texto)
    return 1 if out.falhas else 0


if __name__ == "__main__":
    sys.exit(main())
