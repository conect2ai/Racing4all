# POC de validação de construto e calibração de limiares

Prova de conceito para o motor heurístico do projeto de análise de telemetria iRacing
(framework *Behavior-First*): valida, por rotulagem humana cega, se as 12 regras de
`DRIVING_RULES` (definidas em `heuristics_activation_pipeline_v2.ipynb`, conteúdo v3)
medem comportamentos reais de pilotagem, e calibra os limiares de `THRESHOLD_SPEC`
contra esse rótulo humano. Especificação completa em `../prompt.md`.

## Três tipos de validação (não confundir)

- **Validade de construto**: a regra mede o comportamento que ela diz medir? Testada em
  `04_analysis.ipynb` (item 1) comparando a ativação da regra no limiar atual contra o
  rótulo humano cego (kappa de Cohen). É a pergunta central da POC.
- **Validade de critério**: a regra prediz algo externo relevante (tempo perdido no
  setor)? Testada em `01_gap_closure.ipynb` (item 2), sem depender de rotulagem humana
  — usa `dts` (Δt do setor) do próprio `pair_cache`.
- **Não-redundância**: a regra adiciona informação além das outras 11? Testada em
  `01_gap_closure.ipynb` (item 3) via Jaccard/phi entre pares de regras.

Uma regra pode passar em um critério e falhar em outro — a tabela final
(`results/table_validation_summary.csv`) reporta os três separadamente por regra.

## Ordem de execução

1. **`00_core.ipynb`** — carrega `config`, copia (sem reimplementar) descritores/regras/
   motor de avaliação do v3, constrói e cacheia `interp_cache`, `pair_cache`,
   `pair_cache_self` (negativo B vs. B), `df_sector`. Roda uma vez; execuções seguintes
   reaproveitam o cache em disco.
2. **`01_gap_closure.ipynb`** — varredura de descritores, validade de critério por
   regra, matriz de co-ocorrência, decisão de poda (`results/rules_in_poc.csv`: quais
   regras entram na rotulagem cega).
3. **`02_panel_generator.ipynb`** — amostra pares de setor estratificados, cega com
   hash SHA-256, renderiza painéis PNG de 5 canais brutos (`data/panels/`,
   `data/blind_map.csv`).
4. **`03_labeling_tool.ipynb`** — instrumento de rotulagem cega (`ipywidgets`) sobre os
   painéis. Uso interativo do avaliador; produz `data/labels_poc.csv`.
5. **`04_analysis.ipynb`** — concordância regra×humano, controle negativo, calibração
   ROC/Youden (com IC via grade de fatores), leave-one-track-out, decisão go/no-go,
   tabela-resumo para o artigo. **Exige ≥100 rótulos reais** em `labels_poc.csv`; com
   menos, para e avisa.

## Regras anti-circularidade

- O avaliador rotula **apenas pelos canais brutos** do painel (speed, brake, throttle,
  steering, yaw rate) — nunca vê o `Rule_ID`, o valor de nenhum descritor, ou qual
  parâmetro motivou a amostragem daquele par.
- **`data/poc_threshold_validation/blind_map.csv` não deve ser aberto pelo avaliador
  antes do fim da rotulagem.** Esse arquivo é o único link entre o hash de um painel e
  sua identidade (piloto, pista, stint, setor) e ativações de regra — abri-lo antes de
  terminar contamina o julgamento e invalida a validação de construto. Ele **é
  versionado** (não está no `.gitignore`) justamente para ficar auditável depois —
  apenas não deve ser consultado durante a rotulagem.
- Painéis são amostrados em ordem embaralhada (seed fixa) e cegados por hash — nenhuma
  informação de piloto/pista/stint/setor aparece no painel.
- Controles "B vs. B (self)" (`Tomaz/stint_ref` comparado contra os próprios stints de
  `Tomaz`) entram na mesma amostra que os pares cross-driver, na mesma proporção
  cega — servem para medir a taxa de falso-positivo do próprio avaliador humano (item 2
  de `04_analysis.ipynb`).

## Critério go/no-go (registrado antes da rotulagem, em `01`/`04`)

**GO** se, e somente se: **≥8 regras com kappa > 0,4** E **θ* dentro de
f ∈ [0,5; 1,5] para a maioria dos limiares avaliáveis** (limiares de regras com
`RULE_BEHAVIOR = None` não têm rótulo humano e ficam fora da contagem). Calculado e
registrado em `results/go_no_go.md` por `04_analysis.ipynb`, célula 5 — o critério em si
está fixado no código antes de qualquer rótulo existir, não é ajustado post-hoc.

## Dependências

- `pip install pyirsdk` (o pacote no PyPI **não** se chama `irsdk`, mas expõe o módulo
  `import irsdk` usado por `config/ibt_loader.py` para ler os `.ibt`).
- `.ibt` originais em `G:/Meu Drive/Estudos/Datasets - Simracing/...` (ver
  `config/datasets.py`) — não estão no repositório.

## Status desta implementação (ver commits para detalhes por notebook)

- **`00_core.ipynb`**: executado com um subconjunto real pequeno (3 stints, decisão
  do usuário para não gastar os 10-20 min da carga completa nesta sessão). O sanity
  check contra `heuristic_activations_long.csv` do v3 bateu exatamente (47/47) nesse
  subconjunto. **Para usar a POC de verdade, rode `00_core.ipynb` com
  `RUN_FULL_BUILD = True`** antes de tudo o mais.
- **`01`, `02`**: executados de ponta a ponta contra esse mesmo cache parcial (dados
  reais, não sintéticos) — a lógica está validada, mas os números (kappa, Cliff's delta,
  poda, amostra de 36 painéis em vez de 180) não são conclusivos até rodar com o cache
  completo.
- **`03`**: interface construída e validada (cria `labels_poc.csv` com 36 hashes
  reais); nenhuma rotulagem humana foi realizada nesta sessão.
- **`04`**: para corretamente no guard de `< 100 rótulos` (0 rótulos existentes). As
  células de análise foram verificadas offline contra a telemetria real cacheada usando
  um conjunto de rótulos sintético apenas em memória (nunca gravado em `labels_poc.csv`
  nem versionado) — todas rodaram sem erro. Precisam ser executadas de novo, do início,
  depois de coletar rótulos reais.

Próximos passos para uma rodada real: `00_core` com `RUN_FULL_BUILD = True` → `01` → `02`
(agora com universo completo, deve atingir os 180 pares e as cotas de ≥30) → sessões de
rotulagem em `03` até ≥100 rótulos → `04`.
