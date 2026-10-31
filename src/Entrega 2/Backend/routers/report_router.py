"""Download dinâmico do memorial financeiro com filtros validados."""
from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field
from Backend.services.dashboard_pipeline import prepare_dashboard_data
from Backend.services.memorial_report import gerar_memorial_pdf

router = APIRouter(prefix='/api/v1/relatorio', tags=['relatorios'])


class MemorialIn(BaseModel):
    scenario: str = Field(default='Todos', max_length=200)
    year: int | None = Field(default=None, ge=1, le=127)


@router.post('/memorial')
def memorial(body: MemorialIn):
    try:
        df, _, ranking = prepare_dashboard_data()
        pdf = gerar_memorial_pdf(df, ranking, scenario=body.scenario, year=body.year)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except (OSError, RuntimeError) as exc:
        raise HTTPException(status_code=503, detail='Base CTI indisponível para gerar o memorial.') from exc
    return Response(pdf, media_type='application/pdf', headers={
        'Content-Disposition': 'attachment; filename="Memorial_Calculo_CTI.pdf"',
        'Cache-Control': 'no-store',
    })
