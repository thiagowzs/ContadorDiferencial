"""Prepara docs/ para o GitHub Pages.

Lê celulas/ e banco/celulas.json, renomeia cada imagem pelo seu código SHA-1
(para não revelar a célula pela URL) e gera docs/banco.json com o mapa completo.

Uso:
    python build.py
    python build.py --limpar   # apaga docs/celulas/ antes de copiar
"""

import hashlib
import json
import os
import shutil
import sys
import unicodedata
from pathlib import Path

EXTENSOES = (".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp")
TAMANHOS_RODADA = [50, 100, 200]
LIMITES_RODADA = [10, 1000]

RAIZ = Path(__file__).parent
PASTA_CELULAS = RAIZ / "celulas"
CAMINHO_PADRAO = RAIZ / "banco" / "celulas.json"
CAMINHO_PERFIS = RAIZ / "banco" / "perfis.json"
DOCS = RAIZ / "docs"
DOCS_CELULAS = DOCS / "celulas"


def chave(nome):
    return unicodedata.normalize("NFC", nome).casefold()


def codigo(caminho_relativo):
    return hashlib.sha1(caminho_relativo.encode("utf-8")).hexdigest()[:12]


def conteudo_md5(caminho):
    return hashlib.md5(caminho.read_bytes()).hexdigest()


def listar_imagens(pasta):
    achadas = []
    for atual, subs, arquivos in os.walk(pasta):
        subs[:] = sorted(s for s in subs if not s.startswith("."))
        for nome in sorted(arquivos):
            if not nome.startswith(".") and Path(nome).suffix.lower() in EXTENSOES:
                achadas.append(str((Path(atual) / nome).relative_to(pasta)))
    return achadas


def carregar_padrao():
    if not CAMINHO_PADRAO.exists():
        return None, ["banco/celulas.json não encontrado"]
    try:
        bruto = json.loads(CAMINHO_PADRAO.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return None, [f"celulas.json: JSON inválido: {e}"]

    teclas = bruto.get("celulas") if isinstance(bruto, dict) else None
    if not (isinstance(teclas, list) and teclas):
        return None, ['celulas.json: "celulas" deve ser uma lista de nomes']
    teclas = [c.strip() for c in teclas]

    pastas_bruto = bruto.get("pastas", {})
    pastas = {chave(p): c.strip() for p, c in pastas_bruto.items() if c.strip() in teclas}

    referencia = bruto.get("referencia", {})
    ingles = bruto.get("ingles", {})
    a_parte = {c.strip() for c in bruto.get("a_parte", [])} & set(teclas)
    return {"teclas": teclas, "pastas": pastas, "referencia": referencia, "ingles": ingles, "a_parte": a_parte}, []


def carregar_perfis():
    """Os perfis de doença do painel e o contato do convite. Sem o arquivo, o painel mostra só o sangue normal."""
    if not CAMINHO_PERFIS.exists():
        return [], None, []
    try:
        bruto = json.loads(CAMINHO_PERFIS.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [], None, [f"perfis.json: JSON inválido: {e}"]
    perfis = bruto.get("perfis") if isinstance(bruto, dict) else None
    if not isinstance(perfis, list):
        return [], None, ['perfis.json: "perfis" deve ser uma lista']
    validos = [p for p in perfis if isinstance(p, dict) and isinstance(p.get("nome"), str) and p["nome"].strip()]
    avisos = [f"perfis.json: {len(perfis) - len(validos)} perfil(is) sem nome ignorado(s)"] if len(validos) < len(perfis) else []
    contato = bruto.get("contato") if isinstance(bruto.get("contato"), dict) else None
    return validos, contato, avisos


def classificar(partes, pastas):
    for pasta in reversed(partes[:-1]):
        k = chave(pasta)
        if k in pastas:
            return pastas[k]
    return None


def main():
    limpar = "--limpar" in sys.argv

    if not PASTA_CELULAS.is_dir():
        print("celulas/ não encontrada. Crie a pasta e adicione imagens.")
        return

    padrao, erros = carregar_padrao()
    if erros:
        for e in erros:
            print(f"AVISO: {e}")
    if padrao is None:
        print("Sem padrão, abortando.")
        return

    if limpar and DOCS_CELULAS.exists():
        shutil.rmtree(DOCS_CELULAS)
        print("docs/celulas/ limpa.")
    DOCS_CELULAS.mkdir(parents=True, exist_ok=True)

    grupos = {nome: [] for nome in padrao["teclas"]}
    vistas = set()
    motivos = {"pasta": 0, "fora": 0, "repetida": 0}

    for rel in listar_imagens(PASTA_CELULAS):
        partes = Path(rel).parts
        celula = classificar(partes, padrao["pastas"])
        if celula is None:
            motivos["fora"] += 1
            continue
        md5 = conteudo_md5(PASTA_CELULAS / rel)
        if md5 in vistas:
            motivos["repetida"] += 1
            continue
        vistas.add(md5)
        motivos["pasta"] += 1
        grupos[celula].append(rel)

    tipos = []
    por_codigo = {}
    por_tipo = {}

    # Toda tecla vai para o banco, mesmo sem imagem: ela aparece no pianinho
    for nome in padrao["teclas"]:
        imagens = grupos[nome]
        codigos = [codigo(rel) for rel in imagens]
        ext = Path(imagens[0]).suffix.lower() if imagens else None
        tipo = {
            "nome": nome,
            "imagens": len(imagens),
            "referencia": padrao["referencia"].get(nome),
            "ingles": padrao["ingles"].get(nome),
            "a_parte": nome in padrao["a_parte"],
            "codigos": codigos,
            "ext": ext,
        }
        tipos.append(tipo)
        por_tipo[nome] = codigos
        for rel, cod in zip(imagens, codigos):
            por_codigo[cod] = nome

    if not por_codigo:
        print("Nenhuma imagem encontrada em celulas/.")
        return

    # Copia as imagens renomeadas para docs/celulas/
    copiadas = 0
    for nome in padrao["teclas"]:
        for rel in grupos.get(nome, []):
            cod = codigo(rel)
            ext = Path(rel).suffix.lower()
            destino = DOCS_CELULAS / f"{cod}{ext}"
            if not destino.exists():
                shutil.copy2(PASTA_CELULAS / rel, destino)
                copiadas += 1

    perfis, contato, avisos_perfis = carregar_perfis()
    for aviso in avisos_perfis:
        print(f"AVISO: {aviso}")

    banco = {
        "tipos": tipos,
        "perfis": perfis,
        "contato": contato,
        "por_codigo": por_codigo,
        "resumo": motivos,
        "avisos": [],
        "tamanhos": TAMANHOS_RODADA,
        "limites": LIMITES_RODADA,
    }
    (DOCS / "banco.json").write_text(json.dumps(banco, ensure_ascii=False, indent=2), encoding="utf-8")

    total = sum(t["imagens"] for t in tipos)
    print(f"OK: {len(tipos)} teclas, {sum(1 for t in tipos if t['imagens'])} com imagem, {total} imagens em docs/celulas/.")
    print(f"    {copiadas} novas, {motivos['fora']} de fora do padrão, {motivos['repetida']} repetidas ignoradas.")
    print(f"    {len(perfis)} perfis de doença. docs/banco.json gerado.")


if __name__ == "__main__":
    main()
