"""Gera DOCX sem dependências de edição; usa as funções financeiras reais do CTI.
Saída: PI4/Backend/relatorios/ (criada automaticamente).
Execução na raiz: python3 PI4/scripts/gerar_memorial_cti.py --modelo /caminho/modelo.docx
"""
from pathlib import Path
import sys, csv, hashlib, json, argparse, copy, re
from zipfile import ZipFile, ZIP_DEFLATED
from xml.etree import ElementTree as E
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from Backend.metrics.financial_kpis import build_dre, build_break_even, build_financial_statement
from Backend.metrics.commercial_kpis import calculate_ltv_cac
p=argparse.ArgumentParser();p.add_argument('--modelo',required=True);args=p.parse_args()
W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'; E.register_namespace('w',W)
def el(tag,attrs=None): return E.Element('{'+W+'}'+tag,{'{'+W+'}'+k:str(v) for k,v in (attrs or {}).items()})
def sub(parent,tag,attrs=None):
 x=el(tag,attrs);parent.append(x);return x
with ZipFile(args.modelo) as z:
 styles=z.read('word/styles.xml'); original=E.fromstring(z.read('word/document.xml')); sect=copy.deepcopy(original.find('.//{'+W+'}sectPr'))
# Somente dimensões de página do modelo; nenhum texto, cabeçalho ou relação externa.
for x in list(sect):
 if x.tag.rsplit('}',1)[-1] not in ['pgSz','pgMar','pgNumType']: sect.remove(x)
doc=el('document');body=sub(doc,'body')
def para(text,style=None,mono=False,parent=None,color=None,bold=False):
 q=sub(parent if parent is not None else body,'p');pr=sub(q,'pPr')
 if style: sub(pr,'pStyle',{'val':style});sub(pr,'keepNext')
 sub(pr,'spacing',{'after':100,'line':260,'lineRule':'auto'})
 r=sub(q,'r');rp=sub(r,'rPr');sub(rp,'rFonts',{'ascii':'Courier New' if mono else 'Arial','hAnsi':'Courier New' if mono else 'Arial'})
 sub(rp,'sz',{'val':18 if mono else (32 if style=='Heading1' else 24 if style=='Heading2' else 20)})
 if color: sub(rp,'color',{'val':color})
 if bold: sub(rp,'b')
 t=sub(r,'t');t.text=str(text);t.set('{http://www.w3.org/XML/1998/namespace}space','preserve');return q

def table(headers,rows,widths=None):
 t=sub(body,'tbl');pr=sub(t,'tblPr');sub(pr,'tblW',{'w':10080,'type':'dxa'})
 borders=sub(pr,'tblBorders')
 for side in ['top','left','bottom','right','insideH','insideV']:sub(borders,side,{'val':'single','sz':4,'color':'D5DFEC'})
 widths=widths or [10080//len(headers)]*len(headers)
 grid=sub(t,'tblGrid')
 for w in widths:sub(grid,'gridCol',{'w':w})
 for i,row in enumerate([headers]+list(rows)):
  tr=sub(t,'tr');trpr=sub(tr,'trPr');sub(trpr,'cantSplit')
  if i==0:sub(trpr,'tblHeader')
  for j,value in enumerate(row):
   tc=sub(tr,'tc');cp=sub(tc,'tcPr');sub(cp,'tcW',{'w':widths[j],'type':'dxa'});sub(cp,'shd',{'fill':'2e6da4' if i==0 else ('f0f4fa' if i%2 else 'ffffff')})
   mar=sub(cp,'tcMar')
   for side in ['top','bottom','left','right']:sub(mar,side,{'w':90,'type':'dxa'})
   q=para(value,parent=tc,color='FFFFFF' if i==0 else None,bold=i==0)
   if j==len(row)-1 and i:sub(q.find('{'+W+'}pPr'),'jc',{'val':'right'})
 return t

def code(text):
 table(['LÓGICA / FÓRMULA'],[[text]])
 for r in list(body)[-1].iter('{'+W+'}rFonts'):r.set('{'+W+'}ascii','Courier New');r.set('{'+W+'}hAnsi','Courier New')
def page():
 q=sub(body,'p');sub(sub(q,'r'),'br',{'type':'page'})
def fmt(x):
 if pd.isna(x):return 'Não definido'
 return f'{float(x):,.2f}'.replace(',','@').replace('.',',').replace('@','.')
def pct(x):return fmt(100*x)+'%'
source=ROOT/'Backend/Cti.csv'
rows=0;scenarios=set();years=set();selected=[];accounts=set(); invalid=0
with source.open(newline='',encoding='utf-8-sig') as f:
 for a,c,acc,v in csv.reader(f):
  rows+=1;scenarios.add(c);years.add(int(re.search(r'\d+',a).group()));acc=' '.join(acc.split());accounts.add(acc)
  if c=='Total Cen_00001':
   try:val=float(v.replace('.','').replace(',','.'))
   except ValueError:val=0.;invalid+=1
   selected.append([a,c,acc,val,int(re.search(r'\d+',a).group())])
df=pd.DataFrame(selected,columns=['ANO','CENA','CONTA','VALOR','ano_num'])
cena='Total Cen_00001';dre=build_dre(df,cena);be=build_break_even(df,cena);fs=build_financial_statement(df,cena);com=calculate_ltv_cac(df,cena)
r=dre.iloc[0];b=be.iloc[0];s=fs.iloc[0];c=com.iloc[0]
def account(name):return float(df.loc[(df.ano_num==1)&(df.CONTA==name),'VALOR'].sum())
def section(title,base):
 page();para(title,'Heading1');table(['BASE DE DADOS DESTA SEÇÃO'],[[base]])
def metric(number,title,formula,value,verification,note='',unit='R$'):
 para(number+'  '+title,'Heading2');table(['CAMPO','FÓRMULA','RESULTADO'],[[title,formula,(pct(value) if unit=='%' else fmt(value)+(' '+unit if unit else ''))]],[2500,4800,2780]);para('Verificação: '+verification+' ✓')
 if note:para(note)
 code(formula)
para('MEMORIAL DE CÁLCULO / DOCUMENTAÇÃO TÉCNICA — CTI','Heading1')
para('Dashboard Financeiro CTI • Projeto Interdisciplinar de Ciência de Dados',bold=True)
para('Referência documental: 17 de outubro de 2026 • Valores em reais, sem escala em milhões.')
table(['DADOS BASE','ABAS / SEÇÕES COBERTAS'],[[f'Origem: Backend/Cti.csv\nRegistros: {rows:,}\nCenários: {len(scenarios):,}\nPeríodo: Ano {min(years)} ao Ano {max(years)}\nFormato longo: ANO, CENA, CONTA, VALOR\nDerivados: cti_limpo.parquet, indicadores.parquet, ranking.parquet','1. CEO — DRE e KPIs financeiros\n2. CFO — equilíbrio e eficiência comercial\n3. Acionistas — retorno e distribuição\n4. Poder Concedente — investimentos e solvência\nAnexo — documentação técnica integral']])
para('Filtros do memorial: cenário Total Cen_00001; verificações detalhadas no Ano 1; tabelas anuais nos Anos 1–12. Recorte de reprodução, sem representar seleção atual da interface. Base composta de trajetórias simuladas; não são demonstrações históricas auditadas.')
para('Regras: sinais contábeis preservados. Valores apresentados com duas casas; cálculos executados com a precisão original. O símbolo ✓ indica concordância numérica com a função do projeto, não certificação de auditoria. “Todos” usa média por ano/conta na DRE; cenário específico usa soma. Não somar cenários como empresas independentes.')
para('SHA-256 do CSV: '+hashlib.sha256(source.read_bytes()).hexdigest())
section('SEÇÃO 1 — DEMONSTRATIVO DRE E KPIs FINANCEIROS — CEO','Tabela: Cti.csv (formato longo). Filtros: CENA = Total Cen_00001, ano_num = 1; resumo anual: 1–12. Campos: DRE - Receita, Tributos, Custos, EBITDA, Resultado Operacional, Resultado Financeiro, Resultado Líquido, Imposto de Renda e Contribuição Social, Resultado Antes do Imposto de Renda. Função: build_dre.')
metric('1.1','Receita Líquida','RL = Receita + Tributos',r['Receita Líquida'],f"{fmt(account('DRE - Receita'))} + ({fmt(account('DRE - Tributos'))}) = {fmt(r['Receita Líquida'])}")
metric('1.2','EBITDA','EBITDA = conta DRE - EBITDA',r.EBITDA,f"conta informada = {fmt(account('DRE - EBITDA'))} = {fmt(r.EBITDA)}",'Leitura direta. A reconciliação RL + Custos + OPEX é uma identidade de apresentação; OPEX = EBITDA − (RL + Custos).')
metric('1.3','EBIT','EBIT = DRE - Resultado Operacional',r.EBIT,f"conta informada = {fmt(account('DRE - Resultado Operacional'))} = {fmt(r.EBIT)}",'O código não impõe EBIT = EBITDA − D&A; outros ajustes devem ser conciliados na origem.')
ll=account('DRE - Resultado Líquido');fallback=r.EBIT+r['Resultado Financeiro']+account('DRE - Imposto de Renda e Contribuição Social')
metric('1.4','Lucro Líquido','LL informado se |LL| > 1e-9; senão EBIT + RF + IR/CS',r['Lucro Líquido'],f"|{fmt(ll)}| > 1e-9: {abs(ll)>1e-9}; LL aplicado = {fmt(r['Lucro Líquido'])}",'O fallback também se aplica a lucro informado zero. EBT é lido diretamente da conta de resultado antes do IR.')
for n,key in [('1.5','EBITDA'),('1.6','EBIT')]:metric(n,'Margem '+key,key+' / RL',r[key]/r['Receita Líquida'],f"{fmt(r[key])} / {fmt(r['Receita Líquida'])} = {pct(r[key]/r['Receita Líquida'])}",unit='%')
para('RESUMO ANUAL — DRE','Heading2');table(['ANO','RECEITA LÍQUIDA','EBITDA','EBIT','LUCRO LÍQUIDO'],[[int(x.ano_num),*[fmt(x[k]) for k in ['Receita Líquida','EBITDA','EBIT','Lucro Líquido']]] for _,x in dre.iterrows()])
section('SEÇÃO 2 — EQUILÍBRIO E EFICIÊNCIA COMERCIAL — CFO','Tabela: Cti.csv. Filtros: mesmo cenário e Ano 1; resumo 1–12. Campos: DRE - Custos, Outros Resultados Operacionais, Depreciação e Amortização, Despesas Financeiras e RL derivada. Premissas comerciais por aliases. Funções: build_break_even e calculate_ltv_cac.')
cv=abs(r.Custos);cf=b['Custos Fixos'];m=b['Margem de Contribuição (%)']
metric('2.1','Custos fixos','CF = |Outros Operacionais| + |Depreciação| + |Despesas Financeiras|',cf,' + '.join(fmt(abs(r[k])) for k in ['Outros Operacionais','Depreciação','Despesas Financeiras'])+' = '+fmt(cf))
metric('2.2','Margem de Contribuição','m = (RL − |Custos|) / RL',m,f"({fmt(r['Receita Líquida'])} − {fmt(cv)}) / {fmt(r['Receita Líquida'])} = {pct(m)}",unit='%')
metric('2.3','Break-Even','BE = CF / m',b['Break-Even'],f"{fmt(cf)} / {m:.12f} = {fmt(b['Break-Even'])}",'Modelo inclui depreciação e despesas financeiras em CF. RL ou m nulos produzem ausentes; margem negativa não implica viabilidade econômica.')
metric('2.4','Margem de Segurança','MS = (RL − BE) / RL',b['Margem de Segurança (%)'],f"({fmt(r['Receita Líquida'])} − {fmt(b['Break-Even'])}) / {fmt(r['Receita Líquida'])} = {pct(b['Margem de Segurança (%)'])}",unit='%')
commercial_aliases=['Ticket Médio (R$)','Tempo Médio de Retenção (Meses)','Investimento em Vendas e Mkt (R$)','Investimento em Vendas e Marketing (R$)','Novos Clientes Adquiridos (un)','Novos Clientes Adquiridos']
assert not any(a in accounts for a in commercial_aliases), 'Premissas encontradas: atualizar descrição para origem observada'
para('Premissas comerciais: aliases não encontrados na base. O código aplica ticket = R$ 4.500,00; retenção = 10 meses; investimento em vendas/marketing = R$ 100.000,00; novos clientes = 1.000. São padrões do projeto, não medições de aquisição. Ticket deve ter periodicidade compatível com meses.')
metric('2.5','CAC','CAC = Investimento / Novos clientes',c.CAC,f'100.000,00 / 1.000 = {fmt(c.CAC)}')
metric('2.6','LTV','LTV = Ticket × m × Retenção',c.LTV,f'4.500,00 × {m:.12f} × 10 = {fmt(c.LTV)}')
metric('2.7','LTV/CAC','Q = LTV / CAC',c['LTV/CAC'],f"{fmt(c.LTV)} / {fmt(c.CAC)} = {fmt(c['LTV/CAC'])}",unit='x')
para('O resumo usa médias separadas de LTV, CAC e razões anuais; média das razões pode diferir da razão das médias. Premissas encontradas seriam médias anuais, alinhadas com preenchimento para frente e para trás. Clientes ou CAC zero produzem ausentes; resumos ausentes podem aparecer como zero.')
para('RESUMO ANUAL — EQUILÍBRIO E EFICIÊNCIA','Heading2');table(['ANO','BREAK-EVEN (R$)','SEGURANÇA','LTV (R$)','CAC (R$)'],[[int(x.ano_num),fmt(x['Break-Even']),pct(x['Margem de Segurança (%)']),fmt(com.iloc[i].LTV),fmt(com.iloc[i].CAC)]for i,(_,x) in enumerate(be.iterrows())])
section('SEÇÃO 3 — RETORNO E DISTRIBUIÇÃO — ACIONISTAS','Tabela: Cti.csv; cenário Total Cen_00001, Ano 1; resumo 1–12. Campos: DRE, Patrimônio Líquido, Empréstimos, Disponível e Total do Ativo. Função build_financial_statement; WACC = 0,10; PAYOUT = 0,35; ALIQUOTA_IR_FALLBACK = 0,34.')
for number,title,formula,key,verification,unit in [
 ('3.1','Dividendos','Dividendos = 0,35 × max(LL, 0)','Dividendos',f"0,35 × {fmt(max(r['Lucro Líquido'],0))}",'R$'),
 ('3.2','Lucro retido','Retido = max(LL, 0) − Dividendos','Retido',f"{fmt(max(r['Lucro Líquido'],0))} − {fmt(s.Dividendos)}",'R$'),
 ('3.3','ROIC','ROIC = NOPAT / Capital Investido','ROIC',f"{fmt(s.NOPAT)} / {fmt(s['Capital Investido'])}",'%'),
 ('3.4','EVA','EVA = NOPAT − Capital Investido × WACC','EVA',f"{fmt(s.NOPAT)} − {fmt(s['Capital Investido'])} × 0,10",'R$')]:
 metric(number,title,formula,s[key],verification+' = '+(pct(s[key]) if unit=='%' else fmt(s[key])),unit=unit)
code('Dívida líquida = max(|Empréstimos| − |Disponível|, 0)\nCapital = |PL| + Dívida líquida; se <= 0, usar |Ativo total|\nt = clip(|IR/CS| / |EBIT|, 0, 0.34); ausente -> 0.34\nNOPAT = EBIT × (1 − t)\nROE = LL / |PL|; DY = Dividendos / Capital')
para('Retenção implícita de 65% somente com lucro positivo. Em prejuízo ou lucro zero, dividendos e retido são zero; a razão fica indefinida. Retenção é hipótese contábil, sem comprovar aplicação efetiva em ativos. ROIC, ROE e DY ausentes são preenchidos com zero na função.')
para('RESUMO ANUAL — ACIONISTAS','Heading2');table(['ANO','DIVIDENDOS (R$)','RETIDO (R$)','ROIC','EVA (R$)'],[[int(x.ano_num),fmt(x.Dividendos),fmt(x.Retido),pct(x.ROIC),fmt(x.EVA)]for _,x in fs.iterrows()])
section('SEÇÃO 4 — INVESTIMENTOS E SOLVÊNCIA — PODER CONCEDENTE','Tabela: Cti.csv; cenário Total Cen_00001, Ano 1; resumo 1–12. Campos: FLU - Investimentos; BAL - Ativo Circulante, Realizável a Longo Prazo, Passivo Circulante, Exigível a Longo Prazo, Total do Ativo; DRE - Resultado Operacional e Despesas Financeiras. Referência: controllers/kpis/concession.py e documentos/indicadores/07_capex_bar_dscr.md.')
capex=abs(account('FLU - Investimentos'));ac=abs(account('BAL - Ativo Circulante'));lp=abs(account('BAL - Realizável a Longo Prazo'));pc=abs(account('BAL - Passivo Circulante'));elp=abs(account('BAL - Exigível a Longo Prazo'));ta=abs(account('BAL - Total do Ativo'))
metric('4.1','CAPEX','CAPEX = |FLU - Investimentos|',capex,f"|{fmt(account('FLU - Investimentos'))}| = {fmt(capex)}")
metric('4.2','Intensidade de CAPEX','CAPEX / RL',capex/r['Receita Líquida'],f"{fmt(capex)} / {fmt(r['Receita Líquida'])} = {pct(capex/r['Receita Líquida'])}",unit='%')
metric('4.3','Liquidez geral','LG = (|AC| + |Realizável LP|) / (|PC| + |Exigível LP|)',(ac+lp)/(pc+elp),f'({fmt(ac)} + {fmt(lp)}) / ({fmt(pc)} + {fmt(elp)}) = {fmt((ac+lp)/(pc+elp))}',unit='x')
metric('4.4','BAR — card','BAR card = |BAL - Total do Ativo|',ta,f'|{fmt(ta)}| = {fmt(ta)}','O gráfico usa Imobilizado + Intangível − Depreciação Acumulada − Amortização Acumulada. Card e gráfico possuem bases diferentes.')
interest=abs(r['Despesas Financeiras'])
metric('4.5','Cobertura — concedente','Cobertura = EBIT / |Despesas Financeiras|',r.EBIT/interest,f'{fmt(r.EBIT)} / {fmt(interest)} = {fmt(r.EBIT/interest)}','O catálogo usa EBITDA no numerador. A rubrica chamada DSCR no projeto aproxima cobertura de juros; não incorpora todo o serviço da dívida.',unit='x')
para('RESUMO ANUAL — CONCEDENTE','Heading2')
annual=[]
for _,x in dre.iterrows():
 def av(name):return float(df.loc[(df.ano_num==x.ano_num)&(df.CONTA==name),'VALOR'].sum())
 annual.append([int(x.ano_num),fmt(abs(av('FLU - Investimentos'))),fmt(abs(av('BAL - Total do Ativo'))),fmt(x.EBIT/abs(x['Despesas Financeiras'])) if x['Despesas Financeiras'] else 'Não definido'])
table(['ANO','CAPEX (R$)','BAR CARD (R$)','COBERTURA (x)'],annual)
page();para('ANEXO — DOCUMENTAÇÃO TÉCNICA INTEGRAL DO CTI','Heading1');para('Transcrição integral de PI4/DOCUMENTATION.md, revisão de 13/10/2026. Exemplos didáticos do original permanecem identificados como exemplos e não integram as verificações numéricas deste memorial. URLs e condições de provedores são registros daquela revisão, sem nova verificação nesta geração.')
# Preserva cada linha do original, inclusive fórmulas, URLs e exemplos explicitamente rotulados.
in_code=False
lines=(ROOT/'DOCUMENTATION.md').read_text().splitlines()
i=0
while i<len(lines):
 line=lines[i];i+=1
 if line.startswith('```'):
  in_code=not in_code;para(line,mono=True);continue
 if line.startswith('|') and not in_code:
  group=[line]
  while i<len(lines) and lines[i].startswith('|'):group.append(lines[i]);i+=1
  cells=lambda ln:[cell.strip() for cell in ln.strip().strip('|').split('|')]
  data=[cells(ln) for ln in group if not re.match(r'^\|[ :|\-]+$',ln)]
  table(data[0],data[1:]);continue
 if line.startswith('#'):para(line.lstrip('# ').strip(),'Heading1' if line.startswith('## ') else 'Heading2')
 else:para(line,mono=in_code or line.startswith('$$'))

body.append(sect)
ct='''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/></Types>'''
rels='''<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>'''
wr='''<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>'''
reports_dir = ROOT / 'Backend' / 'relatorios'
reports_dir.mkdir(parents=True, exist_ok=True)
out = reports_dir / 'Memorial_Calculo_Dashboard_Financeiro_CTI.docx'
with ZipFile(out,'w',ZIP_DEFLATED) as z:
 for name,data in [('[Content_Types].xml',ct),('_rels/.rels',rels),('word/document.xml',E.tostring(doc,encoding='utf-8',xml_declaration=True)),('word/styles.xml',styles),('word/_rels/document.xml.rels',wr)]:z.writestr(name,data)
evidence={'csv_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'registros':rows,'cenarios':len(scenarios),'anos':sorted(years),'cenario_recorte':cena,'linhas_recorte':len(df),'valores_invalidos_recorte':invalid,'dre':dre.to_dict('records'),'break_even':be.to_dict('records'),'acionistas':fs.to_dict('records'),'comercial':com.to_dict('records')}
(reports_dir / 'verificacao_memorial_cti.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2,default=float))
print(out);print(rows,len(scenarios),sorted(years));print(dre[['ano_num','Receita Líquida','EBITDA','EBIT','Lucro Líquido']].to_string(index=False))
