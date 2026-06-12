<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&height=200&color=gradient&customColorList=0:1F9BD4,50:2E75B6,100:16265F&text=OllamaBlenderBridge&fontColor=ffffff&fontSize=46&fontAlignY=38&desc=IA%20Local%20dentro%20do%20Blender%20com%20Ollama&descAlignY=58&descSize=18" width="100%"/>

[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Blender](https://img.shields.io/badge/Blender-E87D0D?style=for-the-badge&logo=blender&logoColor=white)](https://blender.org)
[![Ollama](https://img.shields.io/badge/Ollama-000000?style=for-the-badge&logo=ollama&logoColor=white)](https://ollama.ai)
[![LLM](https://img.shields.io/badge/LLM-Local-4B0082?style=for-the-badge)](.)

[![Versão](https://img.shields.io/badge/Versão-4.0-1F9BD4?style=flat-square)](.)
[![Blender](https://img.shields.io/badge/Blender-3.x%20%7C%204.x-E87D0D?style=flat-square)](.)
[![Licença](https://img.shields.io/badge/Licença-MIT-27ae60?style=flat-square)](.)
[![Ollama](https://img.shields.io/badge/Ollama-Required-000000?style=flat-square)](.)

</div>

---

## 🎯 O que é este projeto?

**OllamaBlenderBridge** é um add-on para o **Blender** que integra modelos de linguagem local via **Ollama**, permitindo usar a inteligência artificial diretamente dentro do ambiente 3D — sem enviar dados para a nuvem, sem custo por token, com total privacidade.

Converse com LLMs como **Llama 3**, **Mistral**, **CodeLlama** e outros modelos diretamente do painel do Blender para obter assistência criativa, gerar scripts Python automaticamente, descrever cenas, obter sugestões de materiais e muito mais.

> **Por que local?** Seus projetos 3D permanecem privados. Sem latência de rede. Sem custos de API. Funciona offline.

---

## ✨ Funcionalidades

<div align="center">

| Funcionalidade | v1 | v2 | v3 | v4 |
|---|---|---|---|---|
| Chat básico no painel | ✅ | ✅ | ✅ | ✅ |
| Seleção dinâmica de modelo | ❌ | ✅ | ✅ | ✅ |
| Histórico de conversa | ❌ | ✅ | ✅ | ✅ |
| Geração de scripts Blender | ❌ | ❌ | ✅ | ✅ |
| Execução automática de código | ❌ | ❌ | ❌ | ✅ |
| Descrição de cena 3D | ❌ | ❌ | ✅ | ✅ |
| Streaming de resposta | ❌ | ❌ | ❌ | ✅ |
| Suporte a múltiplos modelos | ❌ | ✅ | ✅ | ✅ |

</div>

---

## 📦 Evolução de Versões

<details>
<summary><strong>🔵 v1 — Prova de Conceito</strong></summary>

Primeira integração funcional entre Blender e Ollama. Painel lateral simples com campo de texto e botão de envio. Comunicação via `requests` com a API REST local do Ollama.

```python
# OllamaBlenderBridgev1.py — Conceito inicial
import bpy
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"

class OllamaQueryOperator(bpy.types.Operator):
    bl_idname  = "ollama.query"
    bl_label   = "Consultar IA"

    def execute(self, context):
        prompt = context.scene.ollama_prompt
        payload = {"model": "llama3", "prompt": prompt, "stream": False}
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        context.scene.ollama_response = response.json().get("response", "")
        return {'FINISHED'}
```

</details>

<details>
<summary><strong>🟡 v2 — Seleção de Modelo + Histórico</strong></summary>

Adicionada descoberta automática dos modelos instalados no Ollama, dropdown de seleção e painel de histórico de conversa com scroll.

```python
def get_modelos_instalados():
    """Busca modelos disponíveis no Ollama local."""
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=5)
        modelos = r.json().get("models", [])
        return [(m["name"], m["name"], "") for m in modelos]
    except Exception:
        return [("llama3", "llama3 (padrão)", "")]
```

</details>

<details>
<summary><strong>🟠 v3 — Contexto 3D + Scripts</strong></summary>

O add-on agora "enxerga" a cena: nome do objeto selecionado, tipo de geometria, materiais ativos e posição são enviados automaticamente como contexto para o LLM. O modelo pode sugerir scripts Python para Blender.

```python
def capturar_contexto_cena():
    """Captura contexto da cena Blender para enriquecer o prompt."""
    obj = bpy.context.active_object
    if not obj:
        return "Nenhum objeto selecionado."
    return (
        f"Objeto ativo: {obj.name} (tipo: {obj.type})\n"
        f"Vértices: {len(obj.data.vertices) if obj.type == 'MESH' else 'N/A'}\n"
        f"Materiais: {[m.name for m in obj.data.materials]}\n"
        f"Posição: {tuple(round(v,2) for v in obj.location)}"
    )
```

</details>

<details>
<summary><strong>🟢 v4 — Streaming + Execução de Código (Atual)</strong></summary>

Versão completa. Respostas em tempo real via streaming. O add-on detecta blocos de código Python nas respostas e oferece botão de execução direta no contexto do Blender.

```python
import bpy, requests, json, re

def stream_ollama(prompt, modelo, contexto=""):
    """Streaming de resposta do Ollama para o painel do Blender."""
    payload = {
        "model"  : modelo,
        "prompt" : f"Contexto Blender:\n{contexto}\n\nUsuário: {prompt}",
        "stream" : True
    }
    with requests.post("http://localhost:11434/api/generate",
                       json=payload, stream=True, timeout=120) as resp:
        buffer = ""
        for line in resp.iter_lines():
            if line:
                chunk = json.loads(line).get("response", "")
                buffer += chunk
                yield buffer

def extrair_e_executar_codigo(resposta):
    """Extrai blocos Python da resposta e executa no Blender."""
    padrao = r"```python\n(.*?)```"
    blocos = re.findall(padrao, resposta, re.DOTALL)
    for bloco in blocos:
        try:
            exec(bloco, {"bpy": bpy})
        except Exception as e:
            print(f"[OllamaBlenderBridge] Erro ao executar: {e}")
```

</details>

---

## 🚀 Instalação

### 1. Instalar o Ollama

```bash
# Linux / macOS
curl -fsSL https://ollama.ai/install.sh | sh

# Baixar um modelo (ex: Llama 3 8B)
ollama pull llama3
ollama pull mistral
ollama pull codellama
```

### 2. Instalar o Add-on no Blender

```
1. Baixe o arquivo ZIP da versão mais recente (v4)
2. Abra o Blender
3. Edit → Preferences → Add-ons → Install...
4. Selecione o ZIP baixado
5. Habilite "OllamaBlenderBridge" na lista de add-ons
6. O painel aparece em: View3D → Sidebar (N) → Ollama AI
```

### 3. Verificar conexão

```bash
# Confirme que o Ollama está rodando
curl http://localhost:11434/api/tags
# Deve retornar JSON com os modelos instalados
```

---

## 🎨 Como Usar

<div align="center">

```
Blender (View3D)
       │
       ├── Sidebar (tecla N)
       │       └── Aba "Ollama AI"
       │               ├── [Selecionar Modelo ▼]
       │               ├── [Campo de Prompt      ]
       │               ├── [Enviar para IA     🔵]
       │               ├── [Capturar Contexto  🟡]
       │               └── [Painel de Resposta   ]
       │                       └── [▶ Executar Código]
       │
       └── Console Python (opcional para debug)
```

</div>

### Exemplos de uso

```
💬 "Crie um cubo subdividido 3 vezes e aplique modificador Bevel"
💬 "Explique como funciona o modificador Subdivision Surface"
💬 "Gere um script para criar 50 esferas aleatórias na cena"
💬 "Descreva as possibilidades de material para este objeto metálico"
💬 "Como otimizar a geometria deste mesh para renderização?"
```

---

## 🗂️ Estrutura do Repositório

```
blenderOllama/
├── OllamaBlenderBridge/
│   ├── __init__.py          ← Manifest e registro do add-on
│   ├── operators.py         ← Operadores Blender (Executar, Capturar)
│   ├── panels.py            ← UI do painel lateral
│   └── ollama_client.py     ← Comunicação com API Ollama
├── OllamaBlenderBridgev1.py ← Versão 1 (script único)
├── OllamaBlenderBridgev2.zip
├── OllamaBlenderBridgev3.zip
├── OllamaBlenderBridgev4.zip ← Versão atual (instalar este)
└── README.md
```

---

## 🛠️ Stack Tecnológica

<div align="center">

[![My Skills](https://skillicons.dev/icons?i=python,blender&theme=dark)](https://skillicons.dev)

</div>

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](.)
[![Blender API](https://img.shields.io/badge/Blender_API-bpy-E87D0D?style=flat-square&logo=blender&logoColor=white)](.)
[![Ollama](https://img.shields.io/badge/Ollama-API_REST-000000?style=flat-square)](.)
[![Llama3](https://img.shields.io/badge/Llama_3-Meta_AI-0668E1?style=flat-square)](.)
[![Mistral](https://img.shields.io/badge/Mistral-7B-FF7000?style=flat-square)](.)
[![CodeLlama](https://img.shields.io/badge/CodeLlama-Code_Gen-4B0082?style=flat-square)](.)

---

## ⚙️ Requisitos do Sistema

| Componente | Mínimo | Recomendado |
|---|---|---|
| **Blender** | 3.6 LTS | 4.1+ |
| **Python** | 3.10 (embutido Blender) | 3.11 |
| **RAM** | 8 GB | 16 GB+ |
| **GPU VRAM** (opcional) | — | 6 GB+ |
| **Ollama** | 0.1.x | Última versão |
| **Modelo LLM** | llama3:8b | llama3:70b / mistral |

---

## 👤 Autor

<div align="center">

| | |
|---|---|
| **Nome** | Fabio Piassi |
| **LinkedIn** | [linkedin.com/in/fabio-piassi](https://linkedin.com/in/fabio-piassi) |
| **GitHub** | [github.com/fassir](https://github.com/fassir) |

</div>

---

<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&height=120&color=gradient&customColorList=0:16265F,50:2E75B6,100:1F9BD4&section=footer" width="100%"/>

*Desenvolvido por [Fabio Piassi](https://github.com/fassir) • OllamaBlenderBridge — IA local para criação 3D*

</div>
