#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Confere os temas (.gmhtema) da loja e gera o temas/catalogo.json.

  --validar            confere todos os temas (formato, tamanhos, so imagens + tema.json)
  --gerar [--saida X]  gera o catalogo (por padrao temas/catalogo.json); --sem-previas nao grava imagens
  --revisar BASE       avisa se o pedido mexe em arquivos que so o dono deve alterar
"""
import argparse
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import zipfile

RAIZ = pathlib.Path(__file__).resolve().parents[2]
TEMAS = RAIZ / "temas"
PREVIAS = TEMAS / "previews"
RX_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{2,63}$")
RX_COR = re.compile(r"^#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")
EXT_IMG = {".jpg", ".jpeg", ".png", ".webp"}
MAX_ZIP = 25 * 1024 * 1024
MAX_IMG = 14 * 1024 * 1024
MAX_PREVIA = 3 * 1024 * 1024
CAMPOS_COR = ["fundo", "superficie", "superficie2", "texto", "apagado", "linha", "linhaFim",
              "perigo", "destaque", "cartao", "cartaoFim", "lateral", "lateralFim"]


def anota(nivel, msg, arq=None):
    local = " file=" + arq if arq else ""
    print("::" + nivel + local + "::" + msg, flush=True)


def corta(v, n):
    return str(v or "").strip()[:n]


def ler_tema(caminho):
    """Devolve (metadados, lista de erros)."""
    rel = caminho.relative_to(RAIZ).as_posix()
    erros = []
    if caminho.stat().st_size > MAX_ZIP:
        return None, ["arquivo maior que 25 MB"]
    try:
        z = zipfile.ZipFile(caminho)
    except zipfile.BadZipFile:
        return None, ["nao e um arquivo .zip valido"]
    with z:
        nomes = {}
        for info in z.infolist():
            if info.is_dir():
                continue
            n = info.filename.replace("\\", "/")
            if "/" in n or n.startswith("."):
                erros.append("arquivo fora da raiz do zip ou oculto: " + n)
                continue
            ext = pathlib.PurePosixPath(n).suffix.lower()
            if n != "tema.json" and ext not in EXT_IMG:
                erros.append("tipo de arquivo nao permitido: " + n + " (so tema.json e imagens)")
                continue
            if info.file_size > MAX_IMG:
                erros.append("arquivo grande demais: " + n)
            nomes[n] = info
        if "tema.json" not in nomes:
            return None, erros + ["falta o tema.json na raiz do zip"]
        if nomes["tema.json"].file_size > 128 * 1024:
            return None, erros + ["tema.json grande demais"]
        try:
            meta = json.loads(z.read("tema.json").decode("utf-8-sig"))
        except Exception as ex:  # noqa: BLE001
            return None, erros + ["tema.json invalido: " + str(ex)]
    if not isinstance(meta, dict):
        return None, erros + ["tema.json precisa ser um objeto"]

    tid = str(meta.get("id", "")).strip().lower()
    if not RX_ID.match(tid):
        erros.append("id invalido (use letras minusculas, numeros, ponto ou traco; 3 a 64 caracteres)")
    elif caminho.stem != tid:
        erros.append("o nome do arquivo deve ser " + tid + ".gmhtema (o arquivo e " + caminho.name + ")")
    nome = corta(meta.get("nome"), 32)
    if not nome:
        erros.append("o tema precisa de um nome")
    cores = meta.get("cores") or {}
    if not isinstance(cores, dict):
        erros.append("'cores' precisa ser um objeto")
        cores = {}
    for c in CAMPOS_COR:
        v = str(cores.get(c, "") or "").strip()
        if v and not RX_COR.match(v):
            erros.append("cor invalida em '" + c + "': " + v)
    for obrigatoria in ("fundo", "texto"):
        if not str(cores.get(obrigatoria, "") or "").strip():
            erros.append("falta a cor '" + obrigatoria + "'")
    wall = str(meta.get("wallpaper", "") or "").strip()
    if wall:
        if wall != pathlib.PurePosixPath(wall).name or wall.startswith(".") or pathlib.PurePosixPath(wall).suffix.lower() not in EXT_IMG:
            erros.append("imagem de fundo invalida (use .jpg, .png ou .webp na raiz do zip)")
        elif wall not in nomes:
            erros.append("a imagem '" + wall + "' nao esta dentro do zip")
    estilo = meta.get("estilo") or {}
    if not isinstance(estilo, dict) or not isinstance(estilo.get("raioCartao", 16), int):
        erros.append("'estilo.raioCartao' precisa ser um numero inteiro")
    if erros:
        return None, erros
    return {
        "id": tid, "nome": nome, "versao": corta(meta.get("versao"), 16) or "1.0", "autor": corta(meta.get("autor"), 40),
        "descricao": corta(meta.get("descricao"), 300), "icone": corta(meta.get("icone"), 4) or "\U0001F3A8",
        "arquivo": rel, "tem_previa": "preview.jpg" in nomes,
    }, []


def todos_os_temas():
    return sorted(TEMAS.glob("*.gmhtema"))


def validar():
    ruim = False
    vistos = {}
    for arq in todos_os_temas():
        meta, erros = ler_tema(arq)
        rel = arq.relative_to(RAIZ).as_posix()
        if erros:
            ruim = True
            for e in erros:
                anota("error", arq.name + ": " + e, rel)
            continue
        if meta["id"] in vistos:
            ruim = True
            anota("error", "id repetido: " + meta["id"] + " (" + arq.name + " e " + vistos[meta["id"]] + ")", rel)
        vistos[meta["id"]] = arq.name
        print("ok  " + arq.name + "  (" + meta["nome"] + ")")
    return 1 if ruim else 0


def oficiais():
    f = TEMAS / "oficiais.txt"
    if not f.exists():
        return set()
    return {l.strip() for l in f.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")}


def gerar(saida=None, gravar_previas=True):
    ofi = oficiais()
    itens, vistos = [], set()
    for arq in todos_os_temas():
        meta, erros = ler_tema(arq)
        rel = arq.relative_to(RAIZ).as_posix()
        if erros:
            for e in erros:
                anota("warning", arq.name + " ficou de fora do catalogo: " + e, rel)
            continue
        if meta["id"] in vistos:
            anota("warning", arq.name + ": id repetido, ficou de fora")
            continue
        vistos.add(meta["id"])
        sha = hashlib.sha256(arq.read_bytes()).hexdigest()
        previa = ""
        arq_previa = PREVIAS / (meta["id"] + ".jpg")
        if arq_previa.exists():
            previa = "temas/previews/" + meta["id"] + ".jpg"
        elif meta["tem_previa"]:
            with zipfile.ZipFile(arq) as z:
                dados = z.read("preview.jpg")
            if dados[:3] == b"\xff\xd8\xff" and len(dados) <= MAX_PREVIA:
                if gravar_previas:
                    PREVIAS.mkdir(parents=True, exist_ok=True)
                    arq_previa.write_bytes(dados)
                previa = "temas/previews/" + meta["id"] + ".jpg"
            else:
                anota("warning", arq.name + ": a previa nao e um JPEG valido (ou passa de 3 MB); ficou sem previa")
        itens.append({
            "id": meta["id"], "nome": meta["nome"], "versao": meta["versao"], "autor": meta["autor"],
            "descricao": meta["descricao"], "icone": meta["icone"], "oficial": meta["id"] in ofi,
            "arquivo": meta["arquivo"], "sha256": sha, "preview": previa,
        })
    itens.sort(key=lambda i: i["id"])
    texto = json.dumps({"formato": 1, "temas": itens}, ensure_ascii=False, indent=2) + "\n"
    destino = pathlib.Path(saida) if saida else TEMAS / "catalogo.json"
    destino.write_text(texto, encoding="utf-8", newline="\n")
    print("catalogo: " + str(len(itens)) + " tema(s) -> " + str(destino))
    return 0


def revisar(base):
    out = subprocess.run(["git", "diff", "--name-status", base + "...HEAD"], cwd=str(RAIZ), capture_output=True,
                         text=True, check=True).stdout
    protegidos = []
    for linha in out.splitlines():
        partes = linha.split("\t")
        status, arquivos = partes[0][:1], partes[1:]
        for a in arquivos:
            if a in ("temas/catalogo.json", "temas/oficiais.txt") or a.startswith(".github/"):
                protegidos.append(a + " (so o dono deve alterar)")
            elif a.startswith("temas/") and status != "A":
                protegidos.append(a + " (ja existia e foi alterado/removido)")
            elif a.startswith("temas/") and not (a.endswith(".gmhtema") or a.startswith("temas/previews/")):
                protegidos.append(a + " (tipo de arquivo inesperado)")
    if protegidos:
        anota("error", "Este pedido mexe em arquivos protegidos: " + "; ".join(protegidos)
              + ". Se foi voce (o dono) que fez isso, pode aprovar mesmo assim.")
        return 1
    print("ok: o pedido so adiciona temas novos.")
    return 0


def main():
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--validar", action="store_true")
    g.add_argument("--gerar", action="store_true")
    g.add_argument("--revisar", metavar="BASE")
    p.add_argument("--saida")
    p.add_argument("--sem-previas", action="store_true")
    a = p.parse_args()
    if a.validar:
        return validar()
    if a.gerar:
        return gerar(a.saida, not a.sem_previas)
    return revisar(a.revisar)


if __name__ == "__main__":
    sys.exit(main())
