"""Validacao e calculo de formulas do construtor por blocos, sem eval de codigo."""
from functools import lru_cache
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator

from Backend.services.dashboard_pipeline import prepare_dashboard_data
from Backend.services.formula_blocks import (
    MAX_BLOCKS, BlockError, block_palette, blocks_to_expression, expression_to_blocks,
)
from Backend.services.formula_metrics import FormulaError, evaluate_formula, formula_variables

router = APIRouter(prefix='/api/v1/formulas', tags=['formulas'])
Aggregation = Literal['mean', 'sum', 'min', 'max']


class BlockIn(BaseModel):
    type: Literal['var', 'num', 'op', 'paren']
    value: str = Field(max_length=300)


class FormulaIn(BaseModel):
    expression: str | None = Field(default=None, max_length=4000)
    blocks: list[BlockIn] | None = Field(default=None, max_length=MAX_BLOCKS)
    scenario: str = Field(default='Todos', max_length=200)
    year: int | None = Field(default=None, ge=1, le=127)
    aggregation: Aggregation = 'mean'
    choices: dict[str, str] = Field(default_factory=dict, max_length=50)

    @model_validator(mode='after')
    def _one_source(self):
        if (self.expression is None) == (self.blocks is None):
            raise ValueError('Envie apenas expression ou apenas blocks.')
        return self


@lru_cache(maxsize=16)
def _variables(scenario: str, year: int | None, aggregation: str) -> dict[str, float]:
    df, ind, _ = prepare_dashboard_data()
    return formula_variables(df, ind, scenario, 'Todos' if year is None else year, aggregation)


def _load(scenario: str, year: int | None, aggregation: str) -> dict[str, float]:
    try:
        return _variables(scenario, year, aggregation)
    except FormulaError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except (OSError, RuntimeError) as exc:
        raise HTTPException(status_code=503, detail='Base CTI indisponível para calcular fórmulas.') from exc


@router.get('/variables')
def variables(scenario: str = 'Todos', year: int | None = None, aggregation: Aggregation = 'mean'):
    return {'variables': block_palette(_load(scenario, year, aggregation))}


@router.post('/validate')
def validate(body: FormulaIn):
    """Erros de formula voltam com 200 e valid=false para o construtor marcar o bloco."""
    values = _load(body.scenario, body.year, body.aggregation)
    response = {'valid': False, 'expression': body.expression, 'blocks': None,
                'value': None, 'resolved': {}, 'error': None, 'error_index': None}
    try:
        if body.blocks is not None:
            response['blocks'] = [block.model_dump() for block in body.blocks]
            response['expression'] = blocks_to_expression(response['blocks'], values)
        else:
            response['blocks'] = expression_to_blocks(body.expression, values, choices=body.choices)
        response['value'] = evaluate_formula(response['expression'], values, choices=body.choices,
                                             resolved=response['resolved'])
        response['valid'] = True
    except FormulaError as exc:
        response['error'] = str(exc)
        response['error_index'] = getattr(exc, 'index', None)
    return response
