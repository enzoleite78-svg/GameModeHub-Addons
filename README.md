# GameModeHub — Loja de Addons

Esta é a loja de addons do **GameModeHub** (por e_Almeida25). O app lê o arquivo `catalogo.json` daqui e mostra os addons na tela **🛒 Addons**.

## Como colocar no GitHub (uma vez)

1. No GitHub, crie um repositório **público** chamado exatamente `GameModeHub-Addons`.
2. Clique em **Add file → Upload files** e arraste **o conteúdo desta pasta** (`catalogo.json`, `README.md`, as pastas `addons` e `fontes`).
3. **Commit changes**. Pronto: em até 5 minutos a loja aparece no app (botão **↻ Atualizar loja**).

> A loja precisa ser pública para o app conseguir ler. Isso é de graça e seguro: ninguém consegue mudar nada sem a sua conta.

## O que tem aqui

```
catalogo.json        ← a lista que o app lê
addons/*.gmhaddon    ← os arquivos que o app baixa
fontes/<id>/         ← o "código" de cada addon (o manifest.json), para editar depois
```

## Publicar uma versão nova de um addon

1. Edite `fontes/<id>/manifest.json` e aumente o `"versao"` (ex.: 1.0 → 1.1).
2. Gere o `.gmhaddon`: selecione **o conteúdo** da pasta `fontes/<id>` → botão direito → **Compactar para arquivo ZIP** → renomeie para `<id>.gmhaddon` e coloque em `addons/`.
3. Pegue o SHA-256 do arquivo (PowerShell): `Get-FileHash addons\<id>.gmhaddon` e copie o valor.
4. No `catalogo.json`, atualize `versao` e `sha256` desse addon.
5. Envie os arquivos. Quem tem o addon vê o botão **↑ Atualizar**.

> Sem o `sha256` certo o app **recusa** o download (é a proteção contra arquivo trocado ou corrompido).

## Selo ✔ Oficial

Só aparece para itens com `"oficial": true` **neste** catálogo. Como só você mexe neste repositório, só você decide o que é oficial. Addons de outras pessoas entram com `"oficial": false` (seção "Da comunidade"). Mais tarde o **GameModeHub Studio** terá o botão **Postar**, que manda o addon para cá como um pedido (*pull request*) — você aprova ou recusa.

## Formato do addon (`manifest.json`)

```jsonc
{
  "formato": 1,
  "id": "seunome.meuaddon",          // minúsculas, números, ponto ou traço
  "nome": "Meu Addon",
  "versao": "1.0",
  "autor": "Seu nome",
  "autorLink": "https://github.com/voce",
  "icone": "🧩",
  "destino": "",                     // "" = aba na barra lateral; "aparencia" = a página aparece dentro da tela Aparência
  "descricao": "O que ele faz.",

  // se o addon traz o app de OUTRA pessoa (aparece no topo da aba):
  "appOriginal": { "nome": "App X", "autor": "Criador do X", "link": "https://github.com/criador/appx" },

  "pagina": {
    "titulo": "Meu Addon",
    "subtitulo": "Uma frase de ajuda.",
    "web": "https://site.com",        // ou "index.html" dentro do addon (opcional)
    "secoes": [
      { "titulo": "Botões", "itens": [
        { "tipo": "botao", "icone": "🟦", "texto": "Steam", "acao": { "tipo": "abrir", "alvo": "steam://open/main" } },
        { "tipo": "texto", "texto": "Um texto qualquer", "estilo": "sub" },
        { "tipo": "link", "texto": "Site", "url": "https://site.com" }
      ] }
    ]
  },

  // pacotes de temas (aparecem em Aparência → Tema)
  "temas": [ { "id": "meu", "nome": "Meu tema", "fundo": "#101014", "superficie": "#1A1A22", "texto": "#EEEEF5", "destaque": "#FF5577" } ]
}
```

### Itens da página

| tipo | o que faz |
|---|---|
| `texto` | um texto (`estilo`: `titulo`, `sub` ou normal) |
| `botao` | um botão (`estilo`: `primario`, `perigo` ou normal) que faz uma `acao` |
| `link` | abre um site `https://` no navegador |
| `temas` | mostra os temas do addon para escolher |
| `editorCores` | o editor de tema personalizado |
| `temasPacotes` | o gerenciador de temas baixados + botão **Loja de temas** (só addons ✔ Oficiais) |

### Ações dos botões

| tipo | alvo | observação |
|---|---|---|
| `abrir` | site, link de programa (`steam://`, `discord://`…) ou caminho completo de um programa do PC | o app **pergunta** antes, exceto sites |
| `modo` | id ou nome de um modo do GameModeHub | |
| `restaurar` | — | volta o desktop ao normal |
| `tecla` | ex.: `win+g`, `ctrl+shift+m` | |
| `texto` | texto para digitar | |
| `midia` | `tocar`, `proxima`, `anterior` | |
| `volume` | `+10`, `-10`, `50` ou `mudo` | |
| `http` | `http://localhost:porta/...` (`metodo`: GET/POST, `corpo`) | só o próprio PC |

Addons **não** podem rodar programas que vêm dentro deles, scripts ou instaladores.

## Componente integrado (só addons ✔ Oficiais)

Alguns apps de código aberto têm um "motor" (um programa) além da tela. Para o app ficar **todo dentro do GameModeHub**, um addon **oficial** pode trazer um `componente`: o GameModeHub baixa o pacote (um `.zip` publicado em **GitHub Releases**), confere o SHA-256, liga o motor escondido (ele fecha junto com o GameModeHub) e mostra a interface numa aba. Addons da comunidade **não** podem usar isso — o app recusa na hora de instalar.

```jsonc
"componente": {
  "url": "https://github.com/enzoleite78-svg/GameModeHub-Addons/releases/download/emusync-1.0.10/EmuSync-1.0.10-GameModeHub.zip",
  "sha256": "…64 caracteres…",       // do zip; sem ele o pacote é recusado
  "tamanhoMB": 47,
  "exe": "agent/EmuSync.Agent.exe",   // o motor, dentro do zip
  "porta": 5353,                      // porta local que o motor abre
  "pasta": "ui", "pagina": "index.html",   // a interface web, dentro do zip
  "ponte": "electron",                // a interface foi feita para Electron: o app fornece "escolher pasta" e "abrir link"
  "iniciarComApp": true,              // liga o motor junto com o GameModeHub
  "dados": "%ProgramData%\\.emusync-data",  // onde o programa original guarda dados (para a cópia de segurança)
  "licenca": "GPLv3 / MIT",
  "codigoFonte": "https://github.com/emu-sync/EmuSync/tree/v1.0.10"
}
```

**Publicar o pacote:** no GitHub, abra o repositório → **Releases → Draft a new release** → tag `emusync-1.0.10` → arraste o `.zip` → **Publish release**. (O arquivo é grande demais para a página de upload de arquivos comum, por isso vai em *Releases*.) Se o pacote mudar, o `sha256` do manifesto muda junto.

**Licenças:** o pacote deve levar o texto da licença do programa e um `LEIA-ME.txt` com o link do código-fonte da versão exata (o EmuSync usa GPLv3: pode redistribuir sem alterar, mantendo licença e crédito).


## Loja de temas (Temas+)

O addon **Temas+** tem um botão **Loja de temas** que lê `temas/catalogo.json` deste repositório. Cada tema é um arquivo `.gmhtema` (um `.zip` renomeado) **sem código**: só cores, estilo e uma imagem.

```
temas/catalogo.json            ← a lista que o app lê
temas/<id>.gmhtema             ← o tema (zip com tema.json + wallpaper)
temas/previews/<id>.jpg        ← prévia mostrada na loja (480×270)
```

**tema.json** (na raiz do zip, junto da imagem):

```jsonc
{
  "formato": 1,
  "id": "seunome.meutema",            // minúsculas, números, ponto ou traço
  "nome": "Meu tema", "versao": "1.0", "autor": "Seu nome", "icone": "🎨",
  "descricao": "Uma frase sobre o tema.",
  "cores": {                          // "#RRGGBB" ou "#AARRGGBB" (com transparência). Só fundo e texto são obrigatórios
    "fundo": "#0B0612", "texto": "#F5F1DC",
    "superficie": "#170B24", "superficie2": "#2B1840", "apagado": "#A596BD", "perigo": "#FF003C",
    "destaque": "#FCEE0A",            // vira a cor de destaque do app enquanto o tema estiver em uso
    "linha": "#80FCEE0A", "linhaFim": "",     // bordas; com linhaFim vira degradê (brilho de vidro)
    "cartao": "#DB120A1E", "cartaoFim": "",   // cartões; com cartaoFim vira degradê do canto de cima ao de baixo
    "lateral": "#EB080410", "lateralFim": ""  // barra lateral
  },
  "estilo": { "raioCartao": 6 },      // arredondamento dos cartões (8 a 32; 16 é o normal)
  "wallpaper": "wallpaper.jpg",       // .jpg, .png ou .webp na raiz do zip (opcional, até 14 MB)
  "wallpaperDesfoque": 12, "wallpaperEscurecer": 28
}
```

**Publicar um tema:** gere o `.gmhtema` (selecione `tema.json` + a imagem → *Compactar para arquivo ZIP* → renomeie para `<id>.gmhtema`), coloque em `temas/`, pegue o SHA-256 (`Get-FileHash temas\<id>.gmhtema`) e adicione ao `catalogo.json`:

```json
{ "id": "seunome.meutema", "nome": "Meu tema", "versao": "1.0", "autor": "Seu nome", "descricao": "…", "icone": "🎨",
  "oficial": false, "arquivo": "temas/seunome.meutema.gmhtema", "sha256": "…", "preview": "temas/previews/seunome.meutema.jpg" }
```

Sem `sha256` o app **recusa** o tema. O selo **✔ Oficial** só aparece para `"oficial": true` — como só você mexe neste repositório, só você decide. Temas de outras pessoas entram com `"oficial": false` (seção "Da comunidade"); confira o tema antes de aceitar um pull request. Usar **Desativar** no app devolve tema, cor de destaque e papel de parede de antes.

> Dica de ícone: use emojis comuns (🎨 🌃 💧). Emojis muito novos podem aparecer como um quadradinho no Windows.

## Créditos

GameModeHub por **e_Almeida25**. Cada addon mostra o autor no rodapé da aba e, quando traz o app de outra pessoa, o criador original e o link do GitHub no topo. Ao portar o app de alguém, confira se a licença permite e sempre credite.
