# Contador Diferencial

Contador diferencial de células em HTML puro — sem servidor, sem instalação.
Abre no navegador, funciona como um contador de bancada digital.

**Demo:** [abrir no GitHub Pages](https://thiagowzs.github.io/ContadorDiferencial/)

---

## Como usar com as suas imagens

**Pré-requisitos:** Python 3.8+

### 1. Adicione as imagens

Crie uma pasta dentro de `celulas/` para cada tipo de célula e coloque as imagens dentro:

```
celulas/
  Segmentado/
    001.jpg
    002.jpg
  Linfócito/
  Monócito/
  Eosinófilo/
  Basófilo/
```

O nome da pasta vira o nome da tecla. Formatos aceitos: JPG, PNG, WebP, GIF, BMP.

### 2. Ajuste o padrão (opcional)

`banco/celulas.json` define as teclas, os sinônimos de pasta e as faixas de referência usadas para sortear a proporção de cada rodada. O arquivo já vem configurado para o diferencial normal do adulto (HC-FMUSP).

### 3. Gere o banco

```bash
python build.py
```

O script renomeia as imagens pelos seus hashes SHA-1 (para não revelar o tipo pela URL) e gera `docs/banco.json`.

### 4. Abra no navegador

```
docs/index.html
```

---

## Como publicar no GitHub Pages

1. Crie um repositório no GitHub e suba o código (sem `celulas/` — ela está no `.gitignore`)
2. Se quiser uma demo pública, inclua algumas imagens de exemplo e rode `python build.py` antes do commit:
   - Edite `.gitignore` e remova as linhas `docs/celulas/` e `docs/banco.json`
   - Commit e push
3. No GitHub → Settings → Pages → Branch `main`, pasta `/docs`
4. O link fica em `https://<seu-usuario>.github.io/<nome-do-repo>/`

---

## Configuração do banco (`banco/celulas.json`)

| Campo | Descrição |
|---|---|
| `celulas` | Lista de nomes das teclas, na ordem do pianinho |
| `pastas` | Mapa de `"NOME_DA_PASTA"` → `"nome_da_tecla"` (sem diferença de maiúsculas) |
| `referencia` | Faixas de referência `[mínimo, máximo]` em % para cada célula |
| `ingles` | Nomes em inglês para o modo English |

Imagens fora das pastas mapeadas são ignoradas. Imagens duplicadas (mesmo conteúdo) entram uma vez.
