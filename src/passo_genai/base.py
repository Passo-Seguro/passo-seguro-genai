"""Base de conhecimento: download das fontes oficiais, limpeza e fatiamento em trechos.

Regras de fatiamento (Fase 2 do guia):
- leis e decretos: por ARTIGO (o artigo inteiro, com incisos e parágrafos);
- páginas: por SEÇÃO (títulos h1–h4);
- PDF: por bloco de páginas;
- cada trecho com 300 a 500 tokens; artigo maior que isso é dividido com sobreposição de ~50.
O texto de cada trecho começa com "<título da fonte> — Art. N", o que ajuda a busca e a citação.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from functools import lru_cache
from pathlib import Path

from passo_genai.config import BRUTOS, TRECHOS, Config
from passo_genai.esquemas import Trecho

MIN_TOKENS, MAX_TOKENS, SOBREPOSICAO = 300, 500, 50
CABECALHO_NAVEGADOR = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9",
}


# --------------------------------------------------------------------------- tokens
@lru_cache(maxsize=1)
def _tokenizador():
    try:
        from transformers import AutoTokenizer

        return AutoTokenizer.from_pretrained(Config().modelo_embeddings)
    except Exception:
        return None


def contar_tokens(texto: str) -> int:
    tok = _tokenizador()
    if tok is not None:
        return len(tok.encode(texto, add_special_tokens=False))
    return int(len(texto.split()) * 1.6)  # aproximação para português sem o tokenizador


# --------------------------------------------------------------------------- download
def caminho_bruto(fonte: dict) -> Path:
    ext = {"lei_html": ".html", "pagina": ".html", "servico_sp156": ".html", "pdf": ".pdf"}[fonte["tipo"]]
    return BRUTOS / f"{fonte['id']}{ext}"


def baixar(fonte: dict, forcar: bool = False) -> dict:
    """Baixa a fonte para base/brutos/ e grava <id>.meta.json com URL, data de acesso e sha256.
    Se o arquivo já existir (inclusive salvo à mão pelo navegador), só registra os metadados."""
    import httpx

    destino = caminho_bruto(fonte)
    meta_arq = destino.with_suffix(".meta.json")
    BRUTOS.mkdir(parents=True, exist_ok=True)
    origem = "local"
    if forcar or not destino.exists():
        r = httpx.get(fonte["url"], headers=CABECALHO_NAVEGADOR, timeout=60, follow_redirects=True)
        r.raise_for_status()
        if fonte["tipo"] != "pdf" and len(r.content) < 3000:
            raise RuntimeError("página muito pequena: provável bloqueio (salve pelo navegador)")
        destino.write_bytes(r.content)
        origem = "download"
    conteudo = destino.read_bytes()
    meta = {
        "id": fonte["id"],
        "url": fonte["url"],
        "data_acesso": (json.loads(meta_arq.read_text())["data_acesso"] if meta_arq.exists() and not forcar and origem == "local"
                        else date.today().isoformat()),
        "sha256": hashlib.sha256(conteudo).hexdigest(),
        "bytes": len(conteudo),
        "origem": origem,
    }
    meta_arq.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    return meta


# --------------------------------------------------------------------------- limpeza
def _decodificar(bruto: bytes) -> str:
    for enc in ("utf-8", "windows-1252", "latin-1"):
        try:
            return bruto.decode(enc)
        except UnicodeDecodeError:
            continue
    return bruto.decode("utf-8", errors="replace")


def _limpar_espacos(texto: str) -> str:
    texto = texto.replace("\xa0", " ")
    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r"\n\s*\n+", "\n", texto)
    return texto.strip()


def html_para_linhas(html: str) -> list[str]:
    """Texto de uma página de lei. Remove o que foi REVOGADO (o Planalto mostra a redação antiga
    riscada com <strike>/<s>/<del>) e tudo que não é conteúdo."""
    from bs4 import BeautifulSoup

    sopa = BeautifulSoup(html, "html.parser")
    for tag in sopa(["script", "style", "noscript", "header", "footer", "nav", "strike", "s", "del", "form"]):
        tag.decompose()
    texto = sopa.get_text("\n")
    return [l.strip() for l in _limpar_espacos(texto).split("\n") if l.strip()]


RE_ARTIGO = re.compile(r"^Art\.?\s*(\d+)(?:\s*-\s*([A-Z]))?\s*[º°o]?\.?\s*(?:[-–—]\s*)?(.*)$", re.I)
RE_ANEXO = re.compile(r"^ANEXO(\s+(ÚNICO|UNICO|[IVX]+))?\b", re.I)


def dividir_artigos(linhas: list[str]) -> list[tuple[str, str]]:
    """[(artigo, texto)], com artigo = '7', '10-A' ou 'anexo'. O preâmbulo é descartado."""
    blocos: list[tuple[str, list[str]]] = []
    atual = None
    for linha in linhas:
        if linha.startswith("Este texto não substitui"):  # rodapé do portal de legislação
            atual = None
            continue
        m = RE_ARTIGO.match(linha)
        # dentro do anexo, "Art. 1º" é célula da tabela (coluna "Dispositivos violados"), não um artigo novo
        if m and not (atual is not None and atual[0] == "anexo"):
            num = m.group(1) + (f"-{m.group(2).upper()}" if m.group(2) else "")
            atual = (num, [linha])
            blocos.append(atual)
            continue
        if RE_ANEXO.match(linha) and len(linha) < 80:
            atual = ("anexo", [linha])
            blocos.append(atual)
            continue
        if atual is not None:
            atual[1].append(linha)
    # artigos repetidos (ex.: texto de lei alteradora citado dentro) -> fica o primeiro
    vistos, saida = set(), []
    for num, partes in blocos:
        chave = num if num != "anexo" else f"anexo{len([1 for n, _ in saida if n == 'anexo'])}"
        if num != "anexo" and num in vistos:
            continue
        vistos.add(chave)
        saida.append((num, "\n".join(partes)))
    return saida


# aviso de cookies, plugin de Libras e botões que o portal da Prefeitura repete em toda página
RE_RUIDO = re.compile(r"(?i)cookies|valoriza sua privacidade|aceitar todos|rejeitar todos|hand ?talk|"
                      r"configurações do plugin|política de privacidade|^saiba mais$|^compartilh")


def _sem_ruido(linhas: list[str]) -> list[str]:
    """Tira o ruído do portal: as linhas de aviso e o menu do topo (linhas curtas antes do 1º parágrafo)."""
    linhas = [l for l in linhas if not RE_RUIDO.search(l)]
    inicio = next((i for i, l in enumerate(linhas) if len(l) >= 60), len(linhas))
    return linhas[inicio:]


def pagina_para_secoes(html: str) -> list[tuple[str, str]]:
    """[(título da seção, texto)] de uma página de serviço, sem menu, aviso de cookies nem plugins."""
    from bs4 import BeautifulSoup

    sopa = BeautifulSoup(html, "html.parser")
    for tag in sopa(["script", "style", "noscript", "header", "footer", "nav", "form", "aside"]):
        tag.decompose()
    raiz = sopa.find("main") or sopa.find("article") or sopa.body or sopa
    secoes, titulo, buffer = [], "Introdução", []
    for el in raiz.find_all(["h1", "h2", "h3", "h4", "p", "li", "td"]):
        texto = _limpar_espacos(el.get_text(" "))
        if not texto:
            continue
        if el.name in ("h1", "h2", "h3", "h4"):
            if buffer:
                secoes.append((titulo, "\n".join(buffer)))
            titulo, buffer = texto, []
        else:
            buffer.append(texto)
    if buffer:
        secoes.append((titulo, "\n".join(buffer)))
    limpas = [(t, "\n".join(_sem_ruido(x.split("\n")))) for t, x in secoes if not RE_RUIDO.search(t)]
    return [(t, x) for t, x in limpas if len(x) > 40]


# seções da carta de serviços do SP156; o resto da página (menu, rodapé, FAQ do portal) fica de fora
SECOES_SP156 = ["O QUE É", "QUANDO SOLICITAR", "PÚBLICO-ALVO", "REQUISITOS, DOCUMENTOS E INFORMAÇÕES",
                "PRAZO MÁXIMO", "TAXAS OU PREÇO PÚBLICO", "CANAIS PARA SOLICITAR", "PRINCIPAIS ETAPAS",
                "LEGISLAÇÃO", "OBSERVAÇÕES", "ÓRGÃO RESPONSÁVEL"]


def servico_sp156_para_texto(html: str) -> tuple[str, str]:
    """(nome do serviço, texto) de uma página de serviço do portal SP156, de "O QUE É" a "ÓRGÃO
    RESPONSÁVEL". Junta os itens quebrados em várias linhas ("Eletrônico\\n:\\n- Portal...")."""
    from bs4 import BeautifulSoup

    sopa = BeautifulSoup(html, "html.parser")
    for tag in sopa(["script", "style", "noscript", "header", "footer", "nav", "form", "aside"]):
        tag.decompose()
    nome = _limpar_espacos((sopa.find("h1") or sopa.find("title")).get_text(" "))
    linhas = [l.strip() for l in _limpar_espacos(sopa.get_text("\n")).split("\n") if l.strip()]
    try:
        ini = linhas.index("O QUE É")
    except ValueError as e:
        raise RuntimeError("página do SP156 sem a seção 'O QUE É' (layout mudou?)") from e
    fim = next((i for i in range(ini, len(linhas)) if linhas[i].startswith("MANIFESTAÇÃO SOBRE")), len(linhas))
    blocos: list[str] = []
    for l in linhas[ini:fim]:
        if l in SECOES_SP156:
            blocos.append(f"\n{l.capitalize()}:")
        elif blocos and (l in (":", ";", ".", ")", "-") or l.startswith((":", ";", ")")) or blocos[-1].endswith(("(", ":", "-"))):
            blocos[-1] += " " + l
        else:
            blocos.append(l)
    texto = re.sub(r"\s+([:;.,)])", r"\1", "\n".join(blocos)).strip()
    texto = re.sub(r"\(\s*(link direciona[^)]*|endereços[^)]*)\)", "", texto)
    return nome, re.sub(r"\n{2,}", "\n", texto)


def pdf_para_secoes(caminho: Path) -> list[tuple[str, str]]:
    from pypdf import PdfReader

    secoes = []
    for i, pagina in enumerate(PdfReader(str(caminho)).pages, 1):
        texto = _limpar_espacos(pagina.extract_text() or "")
        if len(texto) > 80:
            secoes.append((f"página {i}", texto))
    return secoes


# --------------------------------------------------------------------------- fatiamento
def janelas(texto: str, max_tokens: int = MAX_TOKENS, sobreposicao: int = SOBREPOSICAO) -> list[str]:
    """Divide um texto longo em janelas de até max_tokens, cortando em fim de linha (inciso,
    parágrafo) e repetindo ~sobreposicao tokens do fim da janela anterior."""
    if contar_tokens(texto) <= max_tokens:
        return [texto]
    linhas = texto.split("\n")
    partes, atual, tam = [], [], 0
    for linha in linhas:
        t = contar_tokens(linha)
        if t > max_tokens:  # linha enorme: corta por frase
            for frase in re.split(r"(?<=[.;:])\s+", linha):
                ft = contar_tokens(frase)
                if tam + ft > max_tokens and atual:
                    partes.append("\n".join(atual))
                    atual, tam = _cauda(atual, sobreposicao)
                atual.append(frase)
                tam += ft
            continue
        if tam + t > max_tokens and atual:
            partes.append("\n".join(atual))
            atual, tam = _cauda(atual, sobreposicao)
        atual.append(linha)
        tam += t
    if atual:
        partes.append("\n".join(atual))
    return partes


def _cauda(linhas: list[str], sobreposicao: int) -> tuple[list[str], int]:
    cauda, tam = [], 0
    for l in reversed(linhas):
        t = contar_tokens(l)
        if tam + t > sobreposicao and cauda:
            break
        cauda.insert(0, l)
        tam += t
    return cauda, tam


def agrupar_pequenos(secoes: list[tuple[str, str]], min_tokens: int = MIN_TOKENS) -> list[tuple[str, str]]:
    """Junta seções vizinhas muito curtas (páginas e PDFs) até chegar perto de min_tokens."""
    saida: list[tuple[str, str]] = []
    for titulo, texto in secoes:
        if saida and contar_tokens(saida[-1][1]) < min_tokens:
            t0, x0 = saida[-1]
            saida[-1] = (t0, f"{x0}\n{titulo}: {texto}")
        else:
            saida.append((titulo, texto))
    return saida


def fatiar_fonte(fonte: dict, meta: dict) -> list[Trecho]:
    bruto = caminho_bruto(fonte)
    trechos: list[Trecho] = []
    comum = dict(fonte=fonte["id"], titulo=fonte["titulo"], url=fonte["url"], licenca=fonte["licenca"],
                 data_acesso=meta["data_acesso"])
    if fonte["tipo"] == "lei_html":
        filtro = {str(a).lower() for a in (fonte.get("artigos") or [])}
        artigos = dividir_artigos(html_para_linhas(_decodificar(bruto.read_bytes())))
        if not artigos:
            raise RuntimeError(f"{fonte['id']}: nenhum artigo encontrado (página bloqueada ou formato diferente?)")
        contagem_anexo = 0
        for num, texto in artigos:
            if filtro and num.lower() not in filtro:
                continue
            rotulo = f"Art. {num}" if num != "anexo" else "Anexo"
            base_id = f"{fonte['id']}-art{num.lower()}" if num != "anexo" else f"{fonte['id']}-anexo{contagem_anexo or ''}"
            contagem_anexo += num == "anexo"
            for k, parte in enumerate(janelas(texto), 1):
                trechos.append(Trecho(trecho_id=f"{base_id}-p{k}", artigo=rotulo,
                                      texto=f"{fonte['titulo']} — {rotulo}\n{parte}", **comum))
        faltando = filtro - {n.lower() for n, _ in artigos}
        if faltando:
            print(f"  AVISO {fonte['id']}: artigos pedidos e não encontrados: {sorted(faltando)}")
    elif fonte["tipo"] == "servico_sp156":
        nome, texto = servico_sp156_para_texto(_decodificar(bruto.read_bytes()))
        for k, parte in enumerate(janelas(texto), 1):
            trechos.append(Trecho(trecho_id=f"{fonte['id']}-p{k}", artigo="Carta de serviços",
                                  texto=f"{fonte['titulo']}\n{parte}", **comum))
    else:
        if fonte["tipo"] == "pagina":
            secoes = pagina_para_secoes(_decodificar(bruto.read_bytes()))
        else:
            secoes = pdf_para_secoes(bruto)
        for n, (titulo_secao, texto) in enumerate(agrupar_pequenos(secoes), 1):
            for k, parte in enumerate(janelas(texto), 1):
                trechos.append(Trecho(trecho_id=f"{fonte['id']}-s{n:02d}-p{k}", artigo=titulo_secao[:120],
                                      texto=f"{fonte['titulo']} — {titulo_secao}\n{parte}", **comum))
    return trechos


def salvar_trechos(trechos: list[Trecho], caminho: Path = TRECHOS) -> None:
    with open(caminho, "w", encoding="utf-8") as f:
        for t in trechos:
            f.write(t.model_dump_json() + "\n")


def carregar_trechos(caminho: Path = TRECHOS) -> list[Trecho]:
    with open(caminho, encoding="utf-8") as f:
        return [Trecho.model_validate_json(l) for l in f if l.strip()]
