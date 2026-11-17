# ADR-0001 — Python local em vez de GEE

**Status:** aceito
**Data:** 2026-11-17

## Contexto

Requisito de ferramentas gratuitas, reprodutibilidade e independência de plataforma. GEE é
gratuito para pesquisa, mas tem termos que podem restringir uso comercial/redistribuição.

## Decisão

Python local (rasterio, GeoPandas, scikit-learn, XGBoost) como trilha principal. GEE apenas como
alternativa documentada.

## Consequências

- Mais engenharia e infraestrutura necessárias.
- Controle total, reprodutibilidade e ausência de dependência de termos.
- Redflag RF05 permanece registrada.

Ver `docs/26_registro_de_decisoes.md`.
