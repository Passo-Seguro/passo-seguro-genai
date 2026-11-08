# Relatório — Assistente do pedestre (Generative AI for Engineering)

> O relatório fica no GitHub (este arquivo ou o README). Preencha os `[ ]` com os números de
> `avaliacao/` e `base/`. A ordem segue o checklist da Fase 9.

## 01. Integrantes

Guilherme Morais (RM 551981) · Júlia Marques (RM 98680) · Matheus Gusmão (RM 550826)

## 02. Ficha Técnica: o que a IA resolve

**Tarefa:** responder dúvidas de pedestres de São Paulo sobre calçadas, travessias e como
reclamar, citando a fonte, em JSON.

[Problema em 2 frases: 49.215 solicitações de calçada no SP156 entre 2020 e 2025, um aumento de
mais de 200%, e canais confusos; o pedestre não sabe quem resolve. Cidadão-alvo: idosos, PcD,
quem empurra carrinho. Restrição da disciplina: mobilidade e segurança.]

## 03. Pipeline

[Diagrama Mermaid do README + 1 parágrafo: busca → recusa por limiar → LLM com JSON forçado →
validação → checagem de citação → contrato `{resposta, fontes, confianca, recusou}`.]

## 04. Base de conhecimento

[Tabela de `base/tabela_base.md`: fonte, formato, licença, número de trechos e data de acesso.]

Fatiamento: leis por artigo e páginas por seção, com 300 a 500 tokens e sobreposição de 50.
Removemos a redação revogada (texto riscado no Planalto). A NBR 9050 ficou de fora por direitos
autorais.

**Busca:** recall@1 = [ ] e recall@3 = [ ] nas 40 respondíveis. [Se houve revisão dos trechos
porque recall@3 ficou abaixo de 0,8, conte o que mudou.]

**Limiar:** [valor]. ![curva](../avaliacao/resultados/curva_limiar.png)
[Justificativa em 2–3 frases: equilíbrio entre acerto e recusa, escolhido no dev; por que a
varredura passou de 0,8 com o e5.]

## 05. Performance das três configurações

[Tabela de `avaliacao/resultados/placar.md`]

Critério de julgamento: [resumo de `avaliacao/criterio.md`].

Interpretação:
- **A → B (efeito do RAG):** [2–3 frases sobre exatidão e alucinação.]
- **B → C (efeito do LoRA):** [onde ganhou (JSON válido? recusa? citação?), onde não ganhou, e por quê.]
- **Custo:** [recusas indevidas e latência.]
- **IA responsável — linguagem informal:** [formal × informal de `placar_por_registro.csv`. O
  modelo erra mais com quem escreve fora do padrão formal? O que fazer: mais exemplos informais
  no LoRA, sinônimos populares na base.]

Treino do LoRA: [n] exemplos ([n]% recusas), [épocas], perda de validação [ ], [min] na [GPU]
(`treino/treino_lora.json`).

## 06. Os cinco erros

[Conteúdo de `avaliacao/resultados/cinco_erros.md`: pergunta, saída, causa, correção.]

## 07. Conclusão técnica e links

[O que funciona, limites (base pequena, CTB sem valores de multa em reais, SP156 muda de URL),
próximos passos. Links: repositório, vídeo, adapter.]
