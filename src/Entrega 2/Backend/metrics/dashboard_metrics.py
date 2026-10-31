"""Shared derived series used by dashboard views and the formula catalog."""
import pandas as pd

from Backend.metrics.financial_kpis import _conta


def operating_metrics(frame: pd.DataFrame) -> pd.DataFrame:
    data = frame.copy()
    revenue = data['Receita Líquida'].replace(0, float('nan'))
    data['Margem Bruta (%)'] = data['Margem Bruta'] / revenue
    data['Margem EBITDA (%)'] = data['EBITDA'] / revenue
    data['Margem EBIT (%)'] = data['EBIT'] / revenue
    opex = data['OPEX'].abs()
    data['YoY OPEX (%)'] = (opex.groupby(data['CENA'], observed=True).pct_change(fill_method=None)
                            if 'CENA' in data else opex.pct_change(fill_method=None))
    return data


def concession_metrics(frame: pd.DataFrame) -> pd.DataFrame:
    data = frame.copy()
    data['CAPEX'] = _conta(data, 'FLU - Investimentos').abs()
    data['CAPEX Acumulado'] = (data.groupby('CENA', observed=True)['CAPEX'].cumsum()
                               if 'CENA' in data else data['CAPEX'].cumsum())
    data['CAPEX / Receita Líquida'] = data['CAPEX'] / data['Receita Líquida'].replace(0, float('nan'))
    data['Liquidez Geral'] = (_conta(data, 'BAL - Ativo Circulante').abs() +
                             _conta(data, 'BAL - Realizável a Longo Prazo').abs()) / (
        _conta(data, 'BAL - Passivo Circulante').abs() +
        _conta(data, 'BAL - Exigível a Longo Prazo').abs()).replace(0, float('nan'))
    data['Endividamento'] = _conta(data, 'BAL - Total do Passivo').abs() / _conta(
        data, 'BAL - Total do Ativo').abs().replace(0, float('nan'))
    data['Cobertura de Juros'] = data['EBIT'] / _conta(data, 'DRE - Despesas Financeiras').abs().replace(0, float('nan'))
    data['Ativos Brutos'] = (_conta(data, 'BAL - Investimentos - Imobilizado').abs() +
                             _conta(data, 'BAL - Investimentos - Intangível').abs())
    data['Depreciação Acumulada'] = (_conta(data, 'BAL - Depreciação Acumulada').abs() +
                                    _conta(data, 'BAL - Amortização Acumulada').abs())
    data['Base Líquida de Ativos'] = data['Ativos Brutos'] - data['Depreciação Acumulada']
    return data
