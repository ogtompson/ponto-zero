# Roteiro de demonstração do MVP

**Caso guiado:** Farmácia em Água Fria e Boa Viagem  
**Duração sugerida:** 5 a 7 minutos

## 1. Preparação

Na raiz do repositório, com o Docker Desktop aberto:

```powershell
docker compose up -d --build --wait
docker compose ps
```

O resultado esperado é `healthy` para `db`, `api` e `web`, e `Exited (0)` para `migrate`. Abra <http://localhost:8080>.

Conta de demonstração:

- e-mail: `demo@pontozero.app`
- senha: `pontozero2026`

## 2. História que deve ser apresentada

1. Explique o problema em uma frase: dados de demanda e oferta estão dispersos e são difíceis de comparar territorialmente.
2. Entre na conta de demonstração. Se o onboarding aparecer, escolha:
   - **Abrir uma nova unidade**;
   - **Já estou comparando regiões**;
   - segmento **Farmácia**.
3. Em **Explorar**, mantenha Farmácia e selecione **Água Fria** e **Boa Viagem** em **Procurar bairro**.
4. Comece pela aba **Leitura**. Mostre que o produto:
   - evidencia os maiores contrastes mensuráveis;
   - separa sinais observados de limitações;
   - informa confiança e próximo passo;
   - não produz ranking nem promete sucesso.
5. Use **Comparar**, **Indicadores** e **Oferta** apenas para sustentar a leitura, sem percorrer todos os campos.
6. Mostre os números centrais do caso:

| Evidência | Água Fria | Boa Viagem |
|---|---:|---:|
| População residente | 39.012 | 125.805 |
| Renda média domiciliar | R$ 1.189,95 | R$ 7.108,69 |
| Farmácias formais associadas | 28 | 146 |
| Farmácias por 10 mil moradores | 7,18 | 11,61 |

7. Conclua: os dados mostram escalas e pressões de oferta diferentes, mas a decisão ainda exige validar microárea, concorrentes relevantes e fluxo nos horários do segmento.
8. Abra **Minhas análises** ou salve uma nova comparação. A análise preparada chama-se **Ensaio final — Água Fria x Boa Viagem**.
9. Exporte o snapshot em PDF ou CSV para demonstrar que dados, fontes e metodologia ficam preservados.

## 3. Persistência

Para demonstrar que o banco sobrevive ao reinício:

```powershell
docker compose down
docker compose up -d --wait
```

Entre novamente e abra **Minhas análises**. Não use `docker compose down -v`, pois `-v` remove o volume do banco.

O ensaio automatizado equivalente é:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\testar-persistencia.ps1 -Build -Ciclos 1
```

## 4. Contingência

Se o computador ou a internet falhar, use:

- `docs/evidencias/ensaio-farmacia-agua-fria-boa-viagem.png` para mostrar mapa, seleção e leitura;
- `output/pdf/pontozero-contingencia-farmacia.pdf` para apresentar comparação, fontes e avisos;
- `docs/evidencias/pontozero-contingencia-farmacia.csv` para comprovar a exportação estruturada.

Os dados, a API, o GeoJSON e a interface são locais. Sem internet, apenas os tiles externos do mapa-base podem não carregar.

## 5. Mensagem de encerramento

> O PontoZero não entrega uma promessa de sucesso nem apenas uma coleção de dados. Ele organiza evidências territoriais, torna os contrastes explicáveis e indica o que ainda precisa ser validado antes de uma decisão de abertura ou expansão.
