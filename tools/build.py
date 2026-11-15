#!/usr/bin/env python3
"""Genera toda la web de Tu Amigo Inversor (v55) a partir de datos/ y articulos/.
Uso:  python3 tools/build.py      (desde la carpeta raíz de la web)
Qué tocar cada mes (entre el 10 y el 15), y nada más:
  datos/series.json   añade al final de cada estrategia la rentabilidad del mes cerrado, en % y en euros.
                      Si el dato definitivo del mes anterior difiere del que enviaste, corrígelo aquí.
                      GEN-Z y CRYPTO tienen además "nueva": el historial de la versión nueva del método
                      (GEN-Z desde 2026-11, CRYPTO desde 2026-12). Sus meses van ahí, NO en "r".
  datos/pos.json      añade el mes en "labels" y ajusta los tramos: [bloque, ticker, mes_inicio, mes_fin]
  datos/informes.json enlace al informe de cada mes (PDF en /informes/); vacío = «pendiente de enlazar»
Las fechas («datos a…», «ene–oct»…) salen solas del último mes de series.json: no hay que tocarlas.
"""
import json, os, re, html, glob, math, datetime, calendar
import yaml, markdown

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
BASE = 'https://tuamigoinversor.com'
BREVO = 'https://ae99983a.sibforms.com/v2/serve/MUIFADqtOa2VOOZHxYbPei5J0q2r1eBXyYKcBJTvpitk1ikl83_7wPL_7v9WzIYbIjXDAAlbuE0NrwLksKJWMfV9MewqJzd5sp4xZePrhdDPALZ--D02hgsImOVn7WBUruTIoYqERk6gaM-MomxKNx8fEVuLR63EEMUG-cQbYHCjNgHZG-g24ImYZeiwFB2lP-UEb0r3jIyMzjK0Rg=='
MES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
ME3 = [m[:3] for m in MES]

SER = json.load(open('datos/series.json'))
POS = json.load(open('datos/pos.json'))
TXT = json.load(open('datos/content.json'))
INF = json.load(open('datos/informes.json'))

E = {  # orden = orden de riesgo
 'ROCA': dict(url='/cartera-permanente-conservadora-roca/', perfil='Conservador', riesgo=1, lab=False, una='Renta fija, oro y bolsa en fondos. Se toca una o dos veces al año.'),
 'IMPULSO': dict(url='/cartera-inversion-crecimiento-impulso/', perfil='Moderado', riesgo=2, lab=False, una='Oro y bolsa, sin renta fija. Se toca una o dos veces al año.'),
 'HORIZONTE': dict(url='/plan-pensiones-moderado-horizonte/', perfil='Moderado', riesgo=2, lab=False, una='Para el plan de pensiones: cada mes, bolsa de EE. UU. o renta fija.'),
 'GEDA': dict(url='/inversion-tactica-geda/', perfil='Agresivo', riesgo=4, lab=False, una='Cada mes, los 7 activos con más fuerza. Es mi estrategia principal.'),
 'GEN-Z': dict(url='/inversion-tematica-gen-z/', perfil='Muy agresivo', riesgo=5, lab=True, una='Cuatro acciones de temas de futuro, elegidas por momentum.'),
 'CRYPTO': dict(url='/inversion-criptomonedas-crypto/', perfil='Especulativo', riesgo=5, lab=True, una='Mitad Bitcoin, mitad Ethereum. Se revisa en enero y julio.'),
}

# Cambios de método: lo más reciente arriba. Se muestran en /metodologia/ y en la ficha de cada estrategia.
CAMBIOS = [
 dict(k='HORIZONTE', fecha='Noviembre de 2026', t='Publico la regla de HORIZONTE y la serie con mis traspasos desde 2020', p=[
  '<b>Qué estaba mal.</b> Hasta noviembre de 2026 esta web mostraba una serie de HORIZONTE que no correspondía a mis traspasos reales. En 2022, por ejemplo, figuraba un −19,3&nbsp;%.',
  '<b>Cómo la he rehecho.</b> Con las fechas de mis traspasos, que tengo en los extractos del plan, y los valores liquidativos diarios de los dos planes de Santander que uso: el de bolsa de EE. UU. y el monetario. Desde 2020 han sido seis traspasos: junio y julio de 2020, abril y mayo de 2022, septiembre de 2022 y febrero de 2023.',
  '<b>La regla.</b> La que he seguido con mi plan desde enero de 2020 y que hasta ahora no estaba escrita entera en la web: MACD semanal sobre el S&amp;P 500 con dividendos, revisado a fin de mes (detalle en la ficha). En 2022 la serie corregida da un −0,6&nbsp;%. Las cifras de 2026 no cambian: todo el año ha estado en el plan de bolsa.',
  '<b>Cómo se calcula.</b> Los meses sin traspaso son exactamente la rentabilidad del plan en el que estaba. En los meses con traspaso supongo que se vende al cierre del tercer día hábil y se compra al cierre del quinto, sin rentabilidad entre medias. Los plazos reales dependen de cada entidad, y ese mes el resultado puede variar bastante.']),
 dict(k='GEDA', fecha='Noviembre de 2026', t='Las acciones candidatas pasan a salir de una regla automática', p=[
  '<b>De dónde sale el cambio.</b> En octubre de 2026 revisé GEDA de arriba abajo: datos, cálculo, señal y posiciones publicadas mes a mes. La señal y el cálculo aguantaron la revisión. El punto débil era otro: de qué acciones podía elegir el sistema.',
  '<b>Qué hacía antes.</b> La lista de acciones de EE. UU. y de Europa entre las que elige el sistema la actualizaba yo a mano una vez al año, a principios de enero, con las altas y bajas de los índices. En 2026 hice además una actualización a mitad de año. Era la única parte de GEDA que dependía de mí. Al revisarla a fondo vi dos problemas: la lista se quedaba desfasada durante meses y, al hacerla a mano, cometí errores.',
  '<b>Qué hace ahora.</b> Una acción es candidata si, a cierre de mes, forma parte de alguno de los índices (S&amp;P 500, Nasdaq-100 o Dow Jones en EE. UU.; Euro Stoxx 50, IBEX 35, CAC 40, DAX, FTSE MIB o AEX en Europa) y lleva más de tres meses dentro. Se comprueba cada mes con la composición real de los índices, sin que yo intervenga. Los tres meses son una regla de prudencia: evitan comprar una acción justo cuando acaba de entrar en el índice. La señal de momentum no cambia, y los bloques de índices y sectores tampoco.',
  '<b>Lo que eso dice de 2026.</b> Las cifras publicadas son las de las posiciones que comuniqué y tuve cada mes, y no las voy a recalcular. Pero aplicando la regla actual a todo 2026, la rentabilidad a cierre de septiembre habría sido de alrededor del +67&nbsp;%, frente al +100,1&nbsp;% publicado. La diferencia viene de tres posiciones: SanDisk (SNDK) de enero a marzo, que estaba en mi lista de enero recién incorporada a su índice; Western Digital (WDC) en julio y agosto, donde la regla pedía Lumentum (LITE), que no entró en mi lista hasta la actualización de mitad de año; y ASML en agosto, donde la regla pedía Infineon. La cifra de la regla es la que debes usar para hacerte una idea del método.',
  '<b>Años anteriores.</b> Publiqué y tuve posiciones europeas que no estaban en su índice: Rheinmetall (abril de 2022 a abril de 2023), argenx (octubre a diciembre de 2022), Brunello Cucinelli (mayo de 2023) y Banca Popolare di Sondrio (febrero y marzo de 2024). Con la regla nueva no habrían entrado.',
  '<b>Probado y descartado.</b> Limitar a una acción por sector: recortaba la caída máxima unos dos puntos y costaba más de tres puntos de rentabilidad anual. No cumplía el criterio que fijé antes de probarlo y GEDA se queda como está.']),
 dict(k='GEN-Z', fecha='Noviembre de 2026', t='Las acciones candidatas pasan a salir de una regla, con dos por tema como máximo', p=[
  '<b>Qué hacía antes.</b> El universo era una lista de unas 100 empresas agrupadas por temas que elegía yo y actualizaba de vez en cuando. Incluía muchas empresas pequeñas y muy volátiles. Además, sin límite por tema, GEN-Z acabó desde julio de 2026 con las cuatro acciones en el mismo sector: cuando cayeron los semiconductores, cayeron las cuatro.',
  '<b>Qué hace ahora.</b> Solo son candidatas las acciones que forman parte de los mismos índices que GEDA, con más de tres meses dentro, y que pertenecen a uno de los temas de la estrategia: semiconductores, software y ciberseguridad, videojuegos, metales críticos, energía para la IA, salud con IA, aeroespacial y defensa, y robótica/IA y cuántica; en estos dos últimos temas, las candidatas se toman de las mayores posiciones de sus ETF de referencia. Compro las cuatro con más momentum, un 25&nbsp;% cada una, con dos del mismo tema como máximo para no concentrar toda la cartera en uno solo.',
  '<b>El historial.</b> Este cambio es más profundo que el de GEDA. Al exigir que las empresas estén en un índice grande, salen las compañías pequeñas que protagonizaron la versión anterior. La GEN-Z actual es una estrategia distinta: las cifras de esta página, hasta octubre de 2026, son de la versión anterior y no dicen nada de la nueva. La cartera de noviembre de 2026 es la primera con la regla nueva; su historial empieza ahí y lo publico separado del anterior. Sigue siendo una estrategia muy agresiva, con caídas posibles del 30&nbsp;% o más.',
  '<b>Anunciado y descartado.</b> En octubre anuncié aquí una versión con dos ETF temáticos y tres acciones para enero de 2027. No la voy a aplicar: los ETF temáticos que necesitaba no tienen una versión europea (UCITS) fácil de comprar. La configuración de arriba es la definitiva.']),
 dict(k='CRYPTO', fecha='Noviembre de 2026', t='CRYPTO pasa a ser una cartera permanente: 50 % Bitcoin y 50 % Ethereum', p=[
  '<b>Qué hacía antes.</b> Desde enero de 2023, un 30&nbsp;% en Bitcoin, un 30&nbsp;% en Ethereum y un 40&nbsp;% en tres altcoins elegidas cada mes por momentum dentro de una lista que mantenía yo a mano. Usé más de una lista y el criterio para incluir una moneda no siempre fue el mismo.',
  '<b>Qué he revisado.</b> He sustituido la lista por una regla automática (las 100 criptomonedas de mayor capitalización cada mes) y he comparado el resultado con una cartera solo de Bitcoin y Ethereum, con un criterio fijado antes de ver los números. He probado también ventanas de momentum más cortas (de 2 a 12 meses) y limitar las altcoins a las que se pueden comprar en Revolut X o Coinbase.',
  '<b>Resultado.</b> En estos años las altcoins han sumado rentabilidad, pero casi toda en tres o cuatro meses excepcionales. Con reglas automáticas, la ventaja no se mantiene: quitando esos pocos meses, ninguna versión bate a Bitcoin y Ethereum, y las caídas son más profundas. Las ventanas cortas tampoco mejoraban nada.',
  '<b>Qué hace ahora.</b> 50&nbsp;% Bitcoin y 50&nbsp;% Ethereum. En enero y julio compruebo que ninguno se aleje más de un 15&nbsp;% de su peso y, si se aleja, rebalanceo. Sin altcoins y sin rotaciones mensuales. Sigue siendo una estrategia de riesgo muy alto: una cartera de Bitcoin y Ethereum ha llegado a caer cerca de un 70&nbsp;% desde máximos en los últimos años.',
  '<b>Desde cuándo.</b> Desde diciembre de 2026. Las cifras de esta página, hasta noviembre de 2026, son de la versión con altcoins y no las voy a recalcular. El historial de la versión nueva lo publicaré separado.',
  '<b>En el Laboratorio.</b> He probado también a pasar a liquidez cuando Bitcoin o Ethereum cierran el mes por debajo de su media ponderada de 150 días, un filtro de tendencia parecido al de HORIZONTE. En simulación reducía la peor caída a la mitad, pero desde 2020 costaba unos 8–10 puntos de rentabilidad al año y no cumplió el criterio. La sigo sin dinero, mes a mes.']),
 dict(k='WEB', fecha='Noviembre de 2026', t='La web se actualiza una vez al mes, a mediados de mes', p=[
  '<b>Cómo queda.</b> El día 1 envío el informe por correo, con la cartera del mes. La web recoge esa cartera y los resultados del mes cerrado entre el 10 y el 15. Antes la actualizaba cada trimestre.',
  '<b>Datos provisionales y definitivos.</b> El informe sale el día 1 con los datos disponibles ese día. Algunos llegan después: el cierre del tipo de cambio y, sobre todo, el valor liquidativo de fondos y planes de pensiones, que se publica con días de retraso. La web usa los definitivos, así que una cifra puede diferir de la del informe. Septiembre de 2026 quedó en ROCA −0,76&nbsp;% (informe: −1,06&nbsp;%), IMPULSO −2,76&nbsp;% (−2,88&nbsp;%), GEDA +7,56&nbsp;% (+7,65&nbsp;%) y CRYPTO +21,29&nbsp;% (+20,52&nbsp;%). Octubre de 2026 en HORIZONTE quedó en −0,96&nbsp;% (informe: +1,69&nbsp;%).',
  '<b>Fuera el seguimiento diario.</b> Durante unos días hubo una página con la evolución diaria de GEDA. La he quitado: la revisión es mensual y mirar la cartera cada día no ayuda a seguir la regla.']),
 dict(k='WEB', fecha='Noviembre de 2026', t='Fuera el test de riesgo y el simulador', p=[
  'He quitado de la web el test de riesgo, el simulador de mezclas y la guía para combinar estrategias. Eran herramientas que podían leerse como una recomendación a tu medida, y eso no es lo que hago aquí.']),
 dict(k='GEDA', fecha='Octubre de 2026', t='Retiro el histórico simulado de 2016 a 2020', p=[
  'La web mostraba una simulación de GEDA para 2016–2020. No era válida: usaba la lista europea con su composición actual, así que «compraba» empresas antes de que entraran en los índices. La he retirado. En esta web GEDA solo muestra lo publicado y operado desde enero de 2021.']),
]

# ---------- utilidades ----------
def n(x, d=1, sign=True):
    s = f'{abs(x):,.{d}f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    pre = ('+' if x > 0 else '−' if x < 0 else '') if sign else ('−' if x < 0 else '')
    return pre + s
def pct(x, d=1, sign=True): return n(x, d, sign) + '&nbsp;%'
def cls(x): return 'pos' if x > 0 else 'neg' if x < 0 else ''
def cpct(x, d=1): return f'<span class="{cls(x)}">{pct(x, d)}</span>'
def esc(s): return html.escape(str(s), quote=True)
def ym(start, i):
    y, m = map(int, start.split('-')); t = y * 12 + m - 1 + i
    return t // 12, t % 12 + 1
def mes_txt(y, m, corto=False): return f'{ME3[m-1]} {y}' if corto else f'{MES[m-1]} de {y}'

def stats(k):
    s = SER[k]; r = s['r']; N = len(r)
    eq = [100.0]
    for x in r: eq.append(eq[-1] * (1 + x / 100))
    years = {}
    for i, x in enumerate(r):
        y, _ = ym(s['start'], i); years[y] = years.get(y, 1) * (1 + x / 100)
    years = {y: (v - 1) * 100 for y, v in years.items()}
    peak, dd, worst, wi = eq[0], [0.0], 0, 0
    for i, v in enumerate(eq[1:], 1):
        peak = max(peak, v); d = (v / peak - 1) * 100; dd.append(d)
        if d < worst: worst, wi = d, i
    mean = sum(r) / N; vol = math.sqrt(sum((x - mean) ** 2 for x in r) / (N - 1)) * math.sqrt(12)
    y0 = int(s['start'][:4]); ly, lm = ym(s['start'], N - 1)
    return dict(eq=eq, dd=dd, years=years, cagr=((eq[-1] / 100) ** (12 / N) - 1) * 100, total=eq[-1] - 100,
                worst=worst, worst_ym=ym(s['start'], wi - 1), now=dd[-1], vol=vol, ytd=years[ly], y0=y0, N=N,
                last=r[-1], last_ym=(ly, lm), m12=(eq[-1] / eq[-13] - 1) * 100 if N >= 12 else None,
                negs=sum(1 for x in r if x < 0))
ST = {k: stats(k) for k in E}

def fecha_k(k, corto=False):
    """Último día del último mes con datos de la estrategia k."""
    y, m = ST[k]['last_ym']; d = calendar.monthrange(y, m)[1]
    return f'{d} {ME3[m-1]} {y}' if corto else f'{d} de {MES[m-1]} de {y}'
FECHA_DATOS, FECHA_CORTA = fecha_k('GEDA'), fecha_k('GEDA', True)
def tramo(k):
    m = ST[k]['last_ym'][1]; return 'año completo' if m == 12 else f'ene–{ME3[m-1]}'
def idx_nueva(k):
    """Posición (en meses desde el inicio de la serie) del primer mes de la versión nueva, o None."""
    nv = SER[k].get('nueva')
    if not nv: return None
    y0, m0 = map(int, SER[k]['start'].split('-')); y1, m1 = map(int, nv['start'].split('-'))
    i = (y1 - y0) * 12 + m1 - m0
    assert len(SER[k]['r']) <= i, f'{k}: "r" llega más allá del inicio de la versión nueva ({nv["start"]}); esos meses van en "nueva"'
    return i
def res(k, i):
    """Resultado del mes i: serie principal, versión nueva o None si el mes aún no ha cerrado."""
    r = SER[k]['r']
    if i < len(r): return r[i]
    j = idx_nueva(k)
    if j is not None and 0 <= i - j < len(SER[k]['nueva']['r']): return SER[k]['nueva']['r'][i - j]
    return None
for _k in E: idx_nueva(_k)

def chart(k, w=660):
    """Curva de 100 € (escala logarítmica) y, debajo, caída desde el máximo anterior. SVG fijo, sin JavaScript."""
    s = ST[k]; eq, dd = s['eq'], s['dd']; N = len(eq) - 1
    l, r_, t, h1, gap, h2, b = 44, 78, 12, 230, 26, 84, 24
    H = t + h1 + gap + h2 + b; pw = w - l - r_
    lo, hi = math.log(min(eq) * .94), math.log(max(eq) * 1.06)
    X = lambda i: l + pw * i / N
    Y = lambda v: t + h1 * (1 - (math.log(v) - lo) / (hi - lo))
    dmin = min(min(dd), -5) * 1.12; y2 = t + h1 + gap
    D = lambda d: y2 + h2 * (d / dmin)
    o = [f'<svg viewBox="0 0 {w} {H}" role="img" aria-label="{k}: evolución de 100 euros y caídas desde máximos, de {s["y0"]} a {fecha_k(k, True)}" font-family="IBM Plex Mono,monospace" font-size="11">']
    for g in [25, 50, 100, 200, 400, 800, 1600, 3200, 6400]:
        if math.exp(lo) <= g <= math.exp(hi):
            o.append(f'<line x1="{l}" x2="{l+pw}" y1="{Y(g):.1f}" y2="{Y(g):.1f}" stroke="{"#111417" if g==100 else "#C9CED1"}" stroke-width="1" {"stroke-dasharray=\"2 3\"" if g==100 else ""}/><text x="{l-6}" y="{Y(g)+4:.1f}" text-anchor="end" fill="#565D66">{g}</text>')
    for i in range(N + 1):
        y, m = ym(SER[k]['start'], i)
        if m == 1:
            o.append(f'<line x1="{X(i):.1f}" x2="{X(i):.1f}" y1="{t}" y2="{y2+h2}" stroke="#E6E9EA"/><text x="{X(i)+3:.1f}" y="{H-7}" fill="#565D66">{y}</text>')
    pts = ' '.join(f'{X(i):.1f},{Y(v):.1f}' for i, v in enumerate(eq))
    o.append(f'<polyline points="{pts}" fill="none" stroke="#111417" stroke-width="2.2" stroke-linejoin="round"/>')
    o.append(f'<circle cx="{X(N):.1f}" cy="{Y(eq[-1]):.1f}" r="4" fill="#111417"/><text x="{X(N)+8:.1f}" y="{Y(eq[-1])+4:.1f}" font-weight="700" font-size="13" fill="#111417">{n(eq[-1],0,False)} €</text>')
    o.append(f'<text x="{l}" y="{t+10}" fill="#565D66" dx="4">100 € al empezar · escala logarítmica</text>')
    dp = f'{X(0):.1f},{D(0):.1f} ' + ' '.join(f'{X(i):.1f},{D(v):.1f}' for i, v in enumerate(dd)) + f' {X(N):.1f},{D(0):.1f}'
    o.append(f'<line x1="{l}" x2="{l+pw}" y1="{y2}" y2="{y2}" stroke="#111417"/><polygon points="{dp}" fill="#C2281D" fill-opacity=".2"/><polyline points="{" ".join(f"{X(i):.1f},{D(v):.1f}" for i, v in enumerate(dd))}" fill="none" stroke="#C2281D" stroke-width="1.6"/>')
    wi = dd.index(min(dd)); anchor = 'end' if wi > N * .8 else 'start'
    o.append(f'<circle cx="{X(wi):.1f}" cy="{D(dd[wi]):.1f}" r="3.5" fill="#C2281D"/><text x="{X(wi)+(-7 if anchor=="end" else 7):.1f}" y="{D(dd[wi])+4:.1f}" text-anchor="{anchor}" font-weight="700" fill="#C2281D">{pct(dd[wi]).replace("&nbsp;"," ")}</text>')
    o.append(f'<text x="{l-6}" y="{y2+4}" text-anchor="end" fill="#565D66">0</text><text x="{l+4}" y="{y2+h2-4}" fill="#565D66">caída desde el máximo anterior</text></svg>')
    return ''.join(o)

def risk(r): return '<span class="risk" aria-label="Riesgo %d de 5">%s %d/5</span>' % (r, ''.join(f'<i class="{"on" if i < r else ""}"></i>' for i in range(5)), r)

# ---------- posiciones ----------
def cartera(k, i):
    p = POS[k]; return [(b, tk, a, z) for b, tk, a, z in p['stints'] if a <= i <= z]
def movimientos(k, i):
    p = POS[k]
    ent = [tk for b, tk, a, z in p['stints'] if a == i] if i > 0 else []
    sal = [tk for b, tk, a, z in p['stints'] if z == i - 1]
    both = set(ent) & set(sal)   # mismo valor que cambia de tramo: no es rotación
    return [x for x in ent if x not in both], [x for x in sal if x not in both]
NOMBRE_H = {'RV': 'Bolsa de EE. UU. (RV)', 'RF': 'Renta fija (RF)'}
def tk(k, t): return f'<span class="tk">{esc(NOMBRE_H.get(t, t) if k == "HORIZONTE" else t)}</span>'

def pos_ym(k): return ym(SER[k]['start'], len(POS[k]['labels']) - 1)

def tabla_cartera(k):
    p = POS[k]; i = len(p['labels']) - 1; rows = ''
    for b, t, a, z in sorted(cartera(k, i)):
        y, m = ym(SER[k]['start'], a)
        rows += f'<tr><td>{esc(p["blocks"][b])}</td><td>{tk(k,t)}</td><td class="n">{mes_txt(y,m,True)}</td></tr>'
    y, m = pos_ym(k)
    extra = '<p class="note">Además de estas tres, la cartera llevaba siempre Bitcoin y Ethereum. Desde diciembre de 2026 es 50&nbsp;% Bitcoin y 50&nbsp;% Ethereum, sin altcoins: <a href="/metodologia/#cambios">por qué</a>.</p>' if k == 'CRYPTO' else ''
    return f'<div class="tw"><table><thead><tr><th>Bloque</th><th>Posición en {mes_txt(y,m)}</th><th class="n">En cartera desde</th></tr></thead><tbody>{rows}</tbody></table></div>{extra}'

def enlace_informe(y, m):
    key = f'{y}-{m:02d}'
    if key not in INF: return '<span class="muted">sin informe</span>'
    return f'<a href="{esc(INF[key])}">informe</a>' if INF[key] else '<span class="muted">pendiente de enlazar</span>'

def filas_registro(k, desde=0, hasta=None):
    p = POS[k]; N = len(p['labels']); out = []
    for i in range(N - 1, -1, -1):
        y, m = ym(SER[k]['start'], i); ent, sal = movimientos(k, i)
        if i == 0: cambio = 'Cartera inicial: ' + ', '.join(tk(k, t) for b, t, a, z in cartera(k, 0))
        elif not ent and not sal: cambio = '<span class="muted">Sin cambios</span>'
        else: cambio = ' · '.join(x for x in [('<span class="in">Entra</span> ' + ', '.join(tk(k, t) for t in ent)) if ent else '', ('<span class="out">Sale</span> ' + ', '.join(tk(k, t) for t in sal)) if sal else ''] if x)
        out.append((y, m, f'<tr><th scope="row" class="mono">{ME3[m-1]} {y}</th><td>{cambio}</td><td class="n">{cpct(res(k, i), 2) if res(k, i) is not None else "<span class=\"muted\">en curso</span>"}</td><td>{enlace_informe(y,m)}</td></tr>'))
    return out
REG_HEAD = '<thead><tr><th>Mes</th><th>Cambio el día 1</th><th class="n">Resultado del mes</th><th>Informe</th></tr></thead>'

# ---------- plantilla ----------
NAV = [('/inversion-tactica-geda/', 'GEDA'), ('/comparador/', 'Las carteras'), ('/registro/', 'Registro'), ('/como-seguirlo/', 'Cómo seguirlo'), ('/blog/', 'Blog'), ('/sobre-mi/', 'Sobre mí')]
SITEMAP = []
def relativas(h, path):
    """Convierte los enlaces internos (/assets/..., /registro/...) en relativos a la página, para que la web
    funcione igual en tuamigoinversor.com que en una dirección de pruebas con subcarpeta (usuario.github.io/repo/)."""
    d = path.strip('/'); pre = '../' * (len(d.split('/')) if d else 0) or './'
    h = re.sub(r'(href|src)="/(?!/)', lambda m: f'{m.group(1)}="{pre}', h)
    return re.sub(r'(content="0; url=)/(?!/)', lambda m: m.group(1) + pre, h)
def page(path, title, desc, body, index=True, og='/assets/img/og-tuamigoinversor.jpg', kind='website'):
    url = BASE + path
    nav = ''.join(f'<a href="{u}"{" aria-current=\"page\"" if u == path else ""}>{t}</a>' for u, t in NAV)
    h = f'''<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}">
{'' if index else '<meta name="robots" content="noindex">'}
<meta property="og:type" content="{kind}"><meta property="og:locale" content="es_ES"><meta property="og:site_name" content="Tu Amigo Inversor">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{url}"><meta property="og:image" content="{BASE}{og}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' fill='%23111417'/%3E%3Crect x='6' y='18' width='20' height='8' fill='%23FFD84D'/%3E%3C/svg%3E">
<link rel="alternate" type="application/rss+xml" title="Tu Amigo Inversor" href="/feed.xml">
<link rel="preload" href="/assets/fonts/archivo-latin-800-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/css/site.css">
</head>
<body>
<a class="skip" href="#contenido">Saltar al contenido</a>
<header class="top"><div class="wrap">
<a class="logo" href="/">Tu Amigo <b>Inversor</b></a>
<nav class="nav" aria-label="Principal">{nav}<a class="btn y" href="/#suscribirme">Recibir el informe</a></nav>
</div></header>
<main id="contenido">
{body}
</main>
<footer><div class="wrap">
<nav aria-label="Pie"><a href="/laboratorio/">Laboratorio</a><a href="/metodologia/">Metodología y cambios de método</a><a href="/informes/">Informes publicados</a><a href="/recomendaciones/">Cómo elaboro los informes</a><a href="/aviso-legal/">Aviso legal</a><a href="/privacidad/">Privacidad</a><a href="mailto:info@tuamigoinversor.com">info@tuamigoinversor.com</a></nav>
<p>Tu Amigo Inversor es un proyecto divulgativo de José Manuel García, inversor particular. Cuento lo que hago con mi dinero: no es asesoramiento ni una recomendación adaptada a tu caso, y no gestiono dinero de nadie. Invertir conlleva riesgo y puedes perder parte o todo el capital. Las rentabilidades pasadas no garantizan las futuras.</p>
<p>Las cifras son las de las posiciones publicadas, valoradas a precio de cierre en euros, con dividendos y sin comisiones ni impuestos. No son extractos de una cuenta. Datos a {FECHA_DATOS}.</p>
<p>¿Antes de seguir estrategias necesitas poner en orden tus ahorros? Eso lo enseño en <a href="https://ordenatusahorros.com/">Ordena tus ahorros</a>.</p>
</div></footer>
<script data-goatcounter="https://tuamigoinversor.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>
</body>
</html>
'''
    d = path.strip('/'); os.makedirs(d, exist_ok=True) if d else None
    open(os.path.join(d, 'index.html') if not path.endswith('.html') else d, 'w').write(relativas(h, path))
    if index: SITEMAP.append(path)

def redirect(path, to):
    d = path.strip('/'); os.makedirs(d, exist_ok=True)
    full = to if to.startswith('http') else BASE + to
    open(d + '/index.html', 'w').write(relativas(f'<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Página trasladada</title><meta name="robots" content="noindex"><link rel="canonical" href="{full}"><meta http-equiv="refresh" content="0; url={to}"></head><body><p>Esta página ya no existe. <a href="{to}">Sigue por aquí</a>.</p></body></html>', path))

def suscripcion(h='Recibe el informe el día 1'):
    return f'''<section class="band" id="suscribirme"><div class="wrap g2">
<div><span class="eyebrow">Suscripción · gratis</span><h2>{h}</h2>
<p class="lead">Un correo al mes con qué tengo en cada cartera, qué cambio y cómo fue el mes anterior. Lo lees y decides tú.</p>
<ul class="plain"><li>Es gratis.</li><li>Un correo al mes, el día 1. Sin ofertas ni cursos.</li><li>Te das de baja con un clic desde cualquier correo.</li><li>Recibes la cartera el día 1. La web no la recoge hasta mediados de mes, entre el 10 y el 15.</li></ul>
<p class="note">Antes de apuntarte puedes ver <a href="/informes/">los informes ya enviados</a>.</p></div>
<div class="sub-form"><iframe title="Formulario de suscripción al informe mensual" loading="lazy" height="610" src="{BREVO}" scrolling="auto" allowfullscreen></iframe></div>
</div></section>'''

def stats_box(k):
    s = ST[k]; y, m = s['worst_ym']
    largo = s['N'] >= 60
    a = f'<div><small>Anualizada desde {s["y0"]}</small><b class="{cls(s["cagr"])}">{pct(s["cagr"])}</b></div>' if largo else f'<div><small>Acumulado desde {s["y0"]}</small><b class="{cls(s["total"])}">{pct(s["total"],0)}</b></div>'
    return f'''<div class="stats">
<div><small>{s["last_ym"][0]} · {tramo(k)}</small><b class="{cls(s["ytd"])}">{pct(s["ytd"])}</b></div>{a}
<div><small>Peor caída ({ME3[m-1]} {y})</small><b class="neg">{pct(s["worst"])}</b></div>
<div><small>Ahora, frente a su máximo</small><b class="{cls(s["now"])}">{pct(s["now"]) if s["now"] < -0.05 else "en máximos"}</b></div>
<div><small>Meses en negativo</small><b>{s["negs"]} de {s["N"]}</b></div>
</div>'''
def years_box(k):
    s = ST[k]; ly = s['last_ym'][0]
    return '<div class="yrs">' + ''.join(f'<div><small>{y}{(" · " + tramo(k)) if y == ly and s["last_ym"][1] < 12 else ""}</small><b class="{cls(v)}">{pct(v)}</b></div>' for y, v in s['years'].items()) + '</div>'
def nueva_box(k):
    """Historial de la versión nueva del método, separado del anterior."""
    nv = SER[k].get('nueva')
    if not nv: return ''
    y, m = map(int, nv['start'].split('-'))
    if not nv['r']:
        return f'<p class="note" style="margin-top:22px"><b>Versión nueva del método.</b> Empieza en {mes_txt(y, m)}. Todo lo de arriba es de la versión anterior. El historial de la nueva irá aquí debajo, separado, cuando cierre su primer mes.</p>'
    filas = ''; ac = 1.0
    for i, x in enumerate(nv['r']):
        t = y * 12 + m - 1 + i; ac *= 1 + x / 100
        filas += f'<tr><th scope="row" class="mono">{ME3[t % 12]} {t // 12}</th><td class="n">{cpct(x, 2)}</td><td class="n">{cpct((ac - 1) * 100, 1)}</td></tr>'
    return f'<h3 style="margin-top:30px">Versión nueva del método, desde {mes_txt(y, m)}</h3><p class="sub">Historial separado del anterior. Con tan pocos meses no dice nada todavía del método.</p><div class="tw" style="margin-top:14px;max-width:34rem"><table><thead><tr><th>Mes</th><th class="n">Resultado</th><th class="n">Acumulado</th></tr></thead><tbody>{filas}</tbody></table></div>'
def log_html(items):
    return ''.join(f'<div class="log"><time>{c["fecha"]}</time><h3>{c["t"]}</h3>' + ''.join(f'<p>{x}</p>' for x in c['p']) + '</div>' for c in items)
NOTA_HORIZONTE = 'Rentabilidad calculada con el valor liquidativo de los dos planes de Santander, en euros, sin impuestos. En los meses con traspaso supongo venta al cierre del tercer día hábil y compra al cierre del quinto; los plazos reales dependen de cada entidad y ese mes pueden dar un resultado distinto. <b>Serie corregida en noviembre de 2026:</b> antes figuraba una serie que no correspondía a mis traspasos. <a href="/metodologia/#cambios">Qué cambié</a>.'
NOTA_GEDA = 'A cierre de septiembre lo publicado sumaba un +100,1&nbsp;% en el año. Con la regla que aplico desde noviembre de 2026, esos nueve meses habrían dado alrededor de un +67&nbsp;%. <a href="/metodologia/#cambios">Por qué</a>.'

# ---------- fichas ----------
def ficha(k):
    e, c, s = E[k], TXT['estrategias'][k], ST[k]
    camb = [x for x in CAMBIOS if x['k'] == k]
    lab = '<div class="warn" style="margin-top:22px"><h3>Está en el Laboratorio</h3><p>La opero con mi dinero, pero no la doy por probada: lleva menos de cinco años, ha caído más de un 40&nbsp;% y su método acaba de cambiar. <a href="/laboratorio/">Qué significa eso</a>.</p></div>' if e['lab'] else ''
    if POS[k]:
        ult = ''.join(r for _, _, r in filas_registro(k)[:6])
        pos_html = f'''<section><div class="wrap g2"><div><span class="eyebrow">En cartera</span><h2>Qué tengo ahora</h2><p class="sub">Cartera de {mes_txt(*pos_ym(k))}. Los suscriptores la reciben el día 1; la web la recoge entre el 10 y el 15 de cada mes.</p><div style="margin-top:18px">{tabla_cartera(k)}</div></div>
<div><span class="eyebrow">Registro</span><h2>Últimos seis meses</h2><p class="sub">Qué entró y qué salió cada día 1, y cómo acabó el mes.</p><div class="tw" style="margin-top:18px"><table>{REG_HEAD}<tbody>{ult}</tbody></table></div><p class="note"><a href="/registro/#{k.lower()}">Ver el registro completo de {k}</a></p></div></div></section>'''
    else:
        pos_html = f'''<section><div class="wrap"><span class="eyebrow">En cartera</span><h2>Qué tengo</h2><p class="sub">La composición es fija. Solo cambia cuando rebalanceo, una o dos veces al año.</p><div class="tw" style="margin-top:18px;max-width:46rem"><table><thead><tr><th>Activo</th><th>Peso</th></tr></thead><tbody>{"".join(f"<tr><td>{esc(a)}</td><td>{esc(b)}</td></tr>" for a, b in c["composicion"])}</tbody></table></div></div></section>'''
    comp = '' if not POS[k] else f'<div class="tw" style="margin-top:14px"><table><thead><tr><th>Bloque</th><th>Peso</th></tr></thead><tbody>{"".join(f"<tr><td>{esc(a)}</td><td>{esc(b)}</td></tr>" for a, b in c["composicion"])}</tbody></table></div>'
    cap = dict(TXT['como_seguirlo']['capital']).get(k, '')
    nota = f'<p class="note"><b>Sobre las cifras de 2026:</b> {NOTA_GEDA}</p>' if k == 'GEDA' else (f'<p class="note">{NOTA_HORIZONTE}</p>' if k == 'HORIZONTE' else '')
    body = f'''<section class="hero"><div class="wrap">
<span class="eyebrow">{e["perfil"]} · {risk(e["riesgo"])} · con mi dinero desde {s["y0"]}</span>
<h1>{k}</h1><p class="lead">{esc(c["que_es"])}</p>{lab}
<div style="margin-top:28px">{stats_box(k)}</div>{nota}
<p class="note">Datos a {fecha_k(k)}, en euros, con dividendos y sin comisiones ni impuestos. Posiciones publicadas valoradas a precio de cierre; no es el extracto de una cuenta. La caída se mide con datos de fin de mes: dentro de un mes puede ser mayor.</p>
</div></section>
<section class="band"><div class="wrap"><span class="eyebrow">Historial{" · versión anterior del método" if SER[k].get("nueva") else ""}</span><h2>100 € desde {s["y0"]}, y lo que hubo que aguantar</h2>
<figure class="chart" style="margin-top:20px">{chart(k)}<figcaption>Arriba, cuánto valdrían 100 € puestos al empezar. Abajo, cuánto caía la cartera respecto a su máximo anterior. La peor: {pct(s["worst"])}.</figcaption></figure>
{years_box(k)}{nueva_box(k)}</div></section>
<section><div class="wrap g2">
<div><span class="eyebrow">La regla</span><h2>Cómo decide</h2><ol class="rules">{"".join(f"<li>{esc(x)}</li>" for x in c["reglas"])}</ol>{comp}</div>
<div><span class="eyebrow">Sus límites</span><h2>Cuándo lo pasa mal</h2><ul class="plain">{"".join(f"<li>{esc(x)}</li>" for x in c["limites"])}</ul>
<h3 style="margin-top:28px">Lo práctico</h3><ul class="plain"><li><b>Cada cuánto la miro:</b> {esc(c["revision"])}.</li><li><b>Con qué se hace:</b> {esc(c["vehiculos"])}</li>{f"<li><b>Importe:</b> {esc(cap)}</li>" if cap else ""}</ul>
<p class="note"><a href="/como-seguirlo/">Cómo aplico el informe el día 1</a></p></div>
</div></section>
{pos_html}
{f'<section class="band"><div class="wrap"><span class="eyebrow">Cambios de método</span><h2>Lo que he cambiado en {k}</h2>{log_html(camb)}</div></section>' if camb else ''}
{suscripcion(f"Las posiciones de {k}, cada día 1")}'''
    page(e['url'], f'{k}: reglas, historial y cartera | Tu Amigo Inversor', c['que_es'], body)

# ---------- inicio ----------
def home():
    k = 'GEDA'; s = ST[k]; p = POS[k]; i = len(p['labels']) - 1; ent, sal = movimientos(k, i)
    lis = ''.join(f'<li><span class="muted">{esc(p["blocks"][b])}</span><span>{tk(k,t)}{" <b class=\"in\">entra</b>" if t in ent else ""}</span></li>' for b, t, a, z in sorted(cartera(k, i)))
    rows = ''
    for kk, e in E.items():
        if e['lab']: continue
        t = ST[kk]
        rows += f'''<tr class="{"feat" if kk=="GEDA" else ""}"><th scope="row" class="st"><a href="{e["url"]}">{kk}</a><small>{e["una"]}</small></th><td>{risk(e["riesgo"])}</td><td class="n">{t["y0"]}</td><td class="n">{cpct(t["ytd"])}</td><td class="n">{cpct(t["cagr"])}</td><td class="n neg">{pct(t["worst"])}</td><td class="n">{cpct(t["now"]) if t["now"] < -0.05 else "en máximos"}</td></tr>'''
    reg = ''.join(r for _, _, r in filas_registro(k)[:4])
    posts = ''.join(f'<div class="item"><span class="num">{a["fecha"].strftime("%d.%m.%Y")}</span><h3><a href="{a["url"]}">{esc(a["title"])}</a></h3><p>{esc(a["resumen"])}</p></div>' for a in ARTS[:3])
    body = f'''<section class="hero"><div class="wrap hero-grid">
<div><span class="eyebrow">Cuaderno público de un inversor particular · desde 2017</span>
<h1>El día 1 cuento qué tengo en cartera. <span class="hl">Luego el mes decide.</span></h1>
<p class="lead">Invierto mi dinero con reglas escritas y cuento por correo qué compro y qué vendo el día 1 de cada mes. Aquí queda el registro, también de los meses malos.</p>
<div class="cta"><a class="btn" href="#suscribirme">Recibir el informe gratis</a><a class="btn g" href="/registro/">Ver el registro</a></div>
<p class="note">No es asesoramiento: es lo que hago yo. Qué haces con tu dinero lo decides tú.</p></div>
<div class="sheet"><div class="sheet-h"><span>GEDA · cartera de {mes_txt(*pos_ym(k))}</span><span>{MES[s["last_ym"][1]-1]}: {cpct(s["last"],2)}</span></div>
<ul class="chg">{lis}</ul>
<p class="note">{("Salió: " + ", ".join(tk(k,t) for t in sal) + ". ") if sal else ""}Los suscriptores reciben la cartera el día 1. La web la recoge a mediados de mes, entre el 10 y el 15.</p></div>
</div></section>

<section class="band"><div class="wrap">
<span class="eyebrow">La estrategia principal</span><h2>GEDA: siete posiciones, una revisión al mes</h2>
<p class="sub">Un programa mira precios y se queda con lo que más fuerza tiene: un índice global, dos sectores de EE. UU., dos acciones americanas y dos europeas. Sin opiniones ni noticias. Siempre invertida, también cuando el mercado cae.</p>
<div class="g2" style="margin-top:26px;align-items:start">
<figure class="chart">{chart(k,470)}<figcaption>100 € en enero de 2021 y las caídas desde máximos por el camino.</figcaption></figure>
<div>{stats_box(k)}<p class="note"><b>Sobre las cifras de 2026:</b> {NOTA_GEDA}</p>
<p class="note">{s["negs"]} de sus {s["N"]} meses acabaron en negativo. El peor tramo fue {pct(s["worst"])}, medido a fin de mes.</p>
<div class="cta"><a class="btn" href="/inversion-tactica-geda/">Ver la ficha de GEDA</a><a class="btn g" href="/registro/#geda">Registro de GEDA</a></div></div>
</div></div></section>

<section id="carteras"><div class="wrap">
<span class="eyebrow">Las carteras</span><h2>Cuatro carteras, de la más tranquila a la más movida</h2>
<p class="sub">Todas con mi dinero y con reglas que puedes leer enteras. Ninguna es para todo el mundo y aquí no te digo cuál te toca.</p>
<div class="tw" style="margin-top:22px"><table><thead><tr><th>Cartera</th><th>Riesgo</th><th class="n">Desde</th><th class="n">{ST["GEDA"]["last_ym"][0]} {tramo("GEDA")}</th><th class="n">Anualizada</th><th class="n">Peor caída</th><th class="n">Ahora vs. máximo</th></tr></thead><tbody>{rows}</tbody></table></div>
<p class="note">Datos a {FECHA_DATOS}, en euros. Posiciones publicadas valoradas a cierre, con dividendos y sin comisiones ni impuestos. <a href="/metodologia/">Cómo calculo cada cifra</a>.</p>
<div class="warn" style="margin-top:26px"><h3>Aparte: el Laboratorio</h3><p>GEN-Z y CRYPTO también las opero con mi dinero, pero no las pongo en esta tabla: llevan menos de cinco años, han caído más de un 40&nbsp;% y su método acaba de cambiar. <a href="/laboratorio/">Están en el Laboratorio</a>, con sus cifras y sus avisos.</p></div>
</div></section>

<section class="band"><div class="wrap"><span class="eyebrow">Cómo funciona</span><h2>Lo que hago y lo que no</h2>
<div class="g3" style="margin-top:26px">
<div class="item"><span class="num">01</span><h3>Reglas escritas antes</h3><p>Cada cartera decide con una regla que puedes leer en su ficha. Yo la ejecuto. Si la cambio, lo anoto con fecha en <a href="/metodologia/#cambios">cambios de método</a>.</p></div>
<div class="item"><span class="num">02</span><h3>El día 1, por correo</h3><p>El informe dice qué entra, qué sale y cómo fue el mes anterior. La mayoría de los meses toca hacer poco o nada.</p></div>
<div class="item"><span class="num">03</span><h3>Todo queda apuntado</h3><p>Cada cambio va al <a href="/registro/">registro</a>, con su resultado. Los errores míos también.</p></div>
</div>
<div class="g3" style="margin-top:38px">
<div class="item"><h3>No te digo qué te conviene</h3><p>No conozco tu situación. No respondo consultas sobre casos personales ni gestiono dinero de nadie.</p></div>
<div class="item"><h3>No vendo cursos ni señales</h3><p>El informe es gratis. No hay enlaces de afiliado ni cobro de ningún bróker.</p></div>
<div class="item"><h3>No prometo resultados</h3><p>Lo que pasó no dice lo que pasará. Varias de estas carteras han perdido más de un 15&nbsp;% y volverán a hacerlo.</p></div>
</div></div></section>

<section><div class="wrap g2">
<div><span class="eyebrow">Registro</span><h2>Lo último que cambió en GEDA</h2><div class="tw" style="margin-top:18px"><table>{REG_HEAD}<tbody>{reg}</tbody></table></div><p class="note"><a href="/registro/">Registro completo, mes a mes desde 2021</a></p></div>
<div><span class="eyebrow">Quién escribe</span><h2>José Manuel García</h2><p class="sub">Ingeniero y profesor de matemáticas. Invierto mi dinero desde 2006 y programo yo las estrategias, en Python. No soy una entidad autorizada por la CNMV ni asesor: soy un inversor particular que enseña su cuaderno.</p><p class="note"><a href="/sobre-mi/">Más sobre mí</a> · <a href="/recomendaciones/">Cómo elaboro los informes y qué intereses tengo</a></p></div>
</div></section>

<section class="band"><div class="wrap"><span class="eyebrow">Blog</span><h2>Para entender lo que lees en el informe</h2><div class="g3" style="margin-top:26px">{posts}</div><p class="note"><a href="/blog/">Todos los artículos</a></p></div></section>
{suscripcion()}'''
    page('/', 'Tu Amigo Inversor: mis carteras, contadas cada día 1', 'Invierto mi dinero con reglas escritas y cuento cada día 1 qué tengo en cartera y qué cambio. Registro público, informe mensual gratis.', body)

# ---------- páginas ----------
def laboratorio():
    cards = ''
    for k in ['GEN-Z', 'CRYPTO']:
        s = ST[k]; c = TXT['estrategias'][k]
        cards += f'''<div class="sheet"><div class="sheet-h"><span>{E[k]["perfil"]} · desde {s["y0"]}</span>{risk(5)}</div><h3 style="font-size:1.6rem">{k}</h3><p>{esc(c["que_es"])}</p>
<div style="margin-top:14px">{years_box(k)}</div>
<ul class="plain"><li>Peor caída a fin de mes: <b class="neg">{pct(s["worst"])}</b>.</li><li>A {fecha_k(k, True)} seguía un <b class="neg">{pct(s["now"])}</b> por debajo de su máximo.</li><li>{s["negs"]} de sus {s["N"]} meses en negativo.</li></ul>
<div class="cta"><a class="btn g" href="{E[k]["url"]}">Ver la ficha de {k}</a></div></div>'''
    body = f'''<section class="hero"><div class="wrap"><span class="eyebrow">Laboratorio</span><h1>Lo que opero, pero todavía no doy por probado</h1>
<p class="lead">Aquí van las estrategias en las que tengo dinero y que aún no han pasado el tiempo suficiente, han tenido caídas muy fuertes o acaban de cambiar de método.</p>
<div class="warn" style="margin-top:24px"><h3>Cómo leer esta página</h3><p>Los años buenos de estas dos estrategias salen de muy pocos meses y de muy pocas posiciones. Con tan poco historial no se puede distinguir un buen método de una buena racha. Yo las sigo con una parte pequeña de mi dinero, la que puedo ver caer a la mitad.</p></div></div></section>
<section class="band"><div class="wrap g2">{cards}</div></section>
<section><div class="wrap"><span class="eyebrow">Cómo sale una estrategia del Laboratorio</span><h2>Tres condiciones</h2>
<div class="g3" style="margin-top:22px"><div class="item"><span class="num">01</span><h3>Cinco años con dinero real</h3><p>Antes de eso no doy rentabilidad anualizada, solo lo acumulado y los años uno a uno.</p></div><div class="item"><span class="num">02</span><h3>Método congelado</h3><p>Sin cambios de reglas en los últimos doce meses. Cada cambio pone el contador a cero.</p></div><div class="item"><span class="num">03</span><h3>Historial separado por versión</h3><p>Si cambia la regla, el historial nuevo se publica aparte del anterior.</p></div></div>
<p class="note">En seguimiento sin dinero: CRYPTO con filtro de tendencia (sale a liquidez si Bitcoin o Ethereum cierran el mes por debajo de su media ponderada de 150 días). En estudio, sin fecha: una versión táctica hecha solo con fondos de inversión.</p></div></section>
<section class="band"><div class="wrap"><span class="eyebrow">Cambios de método</span><h2>Lo que ha cambiado</h2>{log_html([c for c in CAMBIOS if c["k"] in ("GEN-Z","CRYPTO")])}</div></section>
{suscripcion()}'''
    page('/laboratorio/', 'Laboratorio: GEN-Z y CRYPTO | Tu Amigo Inversor', 'Las estrategias que opero con mi dinero pero aún no doy por probadas: GEN-Z y CRYPTO, con sus cifras, sus caídas y sus cambios de método.', body)

def registro():
    secs = ''; tabs = ''
    for k in ['GEDA', 'HORIZONTE', 'GEN-Z', 'CRYPTO']:
        tabs += f'<a href="#{k.lower()}">{k}</a>'
        filas = filas_registro(k); years = sorted({y for y, _, _ in filas}, reverse=True); det = ''
        for j, y in enumerate(years):
            yr = ST[k]['years'].get(y)
            det += f'<details{" open" if j == 0 else ""}><summary><span>{y}</span><span class="mono {cls(yr or 0)}">{pct(yr) if yr is not None else ""}</span></summary><div class="tw"><table>{REG_HEAD}<tbody>{"".join(r for yy, _, r in filas if yy == y)}</tbody></table></div></details>'
        extra = {'GEN-Z': ' Hasta octubre de 2026, versión anterior del método (lista hecha a mano). La de noviembre de 2026 es la primera cartera con la regla nueva.', 'CRYPTO': ' Solo las tres criptomonedas que rotaban; Bitcoin y Ethereum estaban siempre. Desde diciembre de 2026 CRYPTO es 50&nbsp;% Bitcoin y 50&nbsp;% Ethereum y ya no rota.', 'HORIZONTE': ' Cada mes el plan está en bolsa de EE. UU. (RV) o en renta fija (RF).', 'GEDA': ''}[k]
        secs += f'<section id="{k.lower()}"{" class=\"band\"" if k in ("HORIZONTE","CRYPTO") else ""}><div class="wrap"><span class="eyebrow">{E[k]["perfil"]} · desde {ST[k]["y0"]}</span><h2>{k}</h2><p class="sub">{extra.strip() or "Siete posiciones; cada mes puede cambiar una, varias o ninguna."} <a href="{E[k]["url"]}">Ficha de {k}</a>.</p>{det}</div></section>'
    body = f'''<section class="hero"><div class="wrap"><span class="eyebrow">Registro público</span><h1>Cada cambio, mes a mes</h1>
<p class="lead">Qué entró y qué salió de cada cartera el día 1, y cómo acabó ese mes. El último año está abierto; los anteriores se despliegan.</p>
<p class="note">Resultados hasta {mes_txt(*ST["GEDA"]["last_ym"])} y carteras hasta {mes_txt(*pos_ym("GEDA"))}. Los suscriptores reciben cada cartera el día 1; la web la recoge a mediados de mes, entre el 10 y el 15. La columna «Informe» enlaza el correo o el PDF de ese mes cuando lo tengo subido; los informes empiezan en julio de 2025. ROCA e IMPULSO no aparecen porque su cartera es fija y solo se rebalancean una o dos veces al año.</p>
<p class="note">El resultado de cada mes es el de las posiciones publicadas valoradas a precio de cierre, en euros. No es el extracto de una cuenta ni incluye comisiones o impuestos.</p>
<div class="tabs">{tabs}</div></div></section>{secs}{suscripcion()}'''
    page('/registro/', 'Registro de cambios de cada cartera | Tu Amigo Inversor', 'Todas las entradas y salidas de GEDA, HORIZONTE, GEN-Z y CRYPTO, mes a mes, con el resultado de cada mes.', body)

def comparador():
    ks = list(E); ys = sorted({y for k in ks for y in ST[k]['years']}, reverse=True)
    def row(lbl, f): return f'<tr><th scope="row">{lbl}</th>' + ''.join(f'<td class="n">{f(k)}</td>' for k in ks) + '</tr>'
    rows = row('Perfil', lambda k: f'<span style="font-family:var(--f-b)">{E[k]["perfil"]}</span>') + row('Riesgo', lambda k: f'{E[k]["riesgo"]}/5') + row('Con mi dinero desde', lambda k: ST[k]['y0'])
    rows += row('Anualizada', lambda k: cpct(ST[k]['cagr']) if ST[k]['N'] >= 60 else '<span class="muted">menos de 5 años</span>')
    rows += row('Peor caída', lambda k: f'<span class="neg">{pct(ST[k]["worst"])}</span>') + row('Ahora vs. máximo', lambda k: cpct(ST[k]['now']) if ST[k]['now'] < -.05 else 'en máximos')
    rows += row('Volatilidad anual', lambda k: pct(ST[k]['vol'], 1, False)) + row('Meses en negativo', lambda k: f'{ST[k]["negs"]} de {ST[k]["N"]}')
    gl = ST['GEDA']['last_ym']
    def otro(k, y): return f'<br><span class="muted">hasta {ME3[ST[k]["last_ym"][1]-1]}</span>' if y == ST[k]['last_ym'][0] and ST[k]['last_ym'] != gl else ''
    for y in ys: rows += row(f'{y}{(" · " + tramo("GEDA")) if y == gl[0] and gl[1] < 12 else ""}', lambda k: cpct(ST[k]['years'][y]) + otro(k, y) if y in ST[k]['years'] else '<span class="muted">·</span>')
    rows += row('Revisión', lambda k: f'<span style="font-family:var(--f-b);white-space:normal">{"Mensual" if TXT["estrategias"][k]["revision"].startswith("Cada mes") else "Enero y julio"}</span>')
    head = ''.join(f'<th class="n"><a href="{E[k]["url"]}">{k}</a>{"<br><span class=\"muted\">Laboratorio</span>" if E[k]["lab"] else ""}</th>' for k in ks)
    body = f'''<section class="hero"><div class="wrap"><span class="eyebrow">Las carteras</span><h1>Las seis, en una tabla</h1><p class="lead">Mismas columnas y mismas reglas de cálculo para todas. Fíjate antes en la peor caída que en la rentabilidad: es lo que hay que aguantar para llegar a lo otro.</p>
<div class="tw" style="margin-top:26px"><table><thead><tr><th></th>{head}</tr></thead><tbody>{rows}</tbody></table></div>
<p class="note">Datos a {FECHA_DATOS}, en euros. Posiciones publicadas valoradas a cierre, con dividendos y sin comisiones ni impuestos. Caída y volatilidad con datos de fin de mes. GEN-Z y CRYPTO llevan menos de cinco años y no doy su anualizada. En GEDA, a cierre de septiembre de 2026 lo publicado sumaba un +100,1&nbsp;%; con la regla actual habría sido de alrededor del +67&nbsp;%: <a href="/metodologia/#cambios">cambios de método</a>.</p>
<p class="note">Esta tabla no sirve para elegir una cartera para ti. Eso depende de tu situación, y no la conozco.</p></div></section>{suscripcion()}'''
    page('/comparador/', 'Las seis carteras en una tabla | Tu Amigo Inversor', 'Riesgo, peor caída, rentabilidad año a año y revisión de las seis carteras de Tu Amigo Inversor, con el mismo cálculo para todas.', body)

def como_seguirlo():
    c = TXT['como_seguirlo']
    body = f'''<section class="hero"><div class="wrap"><span class="eyebrow">Operativa</span><h1>Qué hago yo el día 1</h1><p class="lead">El informe trae muchas tablas. Lo que toca hacer cabe en pocas líneas, y la mayoría de los meses es nada.</p></div></section>
<section class="band"><div class="wrap g2"><div><span class="eyebrow">Paso a paso</span><h2>Cuando llega el informe</h2><ol class="rules">{"".join(f"<li>{esc(x)}</li>" for x in c["dia_1"])}</ol></div>
<div><span class="eyebrow">Si empiezo de cero</span><h2>Una cartera nueva</h2><ul class="plain">{"".join(f"<li>{esc(x)}</li>" for x in c["empezar_de_cero"])}</ul></div></div></section>
<section><div class="wrap"><span class="eyebrow">Importes</span><h2>Con cuánto tiene sentido cada una</h2><p class="sub">Lo que pesa son las comisiones: cuantas más operaciones al año y menos importe por posición, más se comen.</p>
<div class="tw" style="margin-top:18px"><table><thead><tr><th>Cartera</th><th>Importe orientativo</th></tr></thead><tbody>{"".join(f"<tr><th scope=row>{esc(a)}</th><td>{esc(b)}</td></tr>" for a, b in c["capital"])}</tbody></table></div>
<p class="note">Más detalle en <a href="/aprende/con-cuanto-dinero-seguir-cada-estrategia/">Con cuánto dinero seguir cada estrategia</a>.</p></div></section>
<section class="band"><div class="wrap"><span class="eyebrow">Dónde</span><h2>Los brókers que uso yo</h2><ul class="plain">{"".join(f"<li>{esc(x)}</li>" for x in c["brokers"])}</ul>
<p class="note">No cobro de ninguno ni hay enlaces de afiliado. Lo cuento entero en <a href="/aprende/que-brokers-utilizo/">Qué brókers utilizo</a>.</p></div></section>{suscripcion()}'''
    page('/como-seguirlo/', 'Cómo aplico el informe el día 1 | Tu Amigo Inversor', 'Qué miro cuando llega el informe, cómo ejecuto una rotación, con qué importes y en qué brókers. Lo que hago yo, paso a paso.', body)

def prosa(path, f, title, desc, extra='', pre='', rep=None):
    txt = open("datos/paginas/" + f).read()
    for a, b in (rep or {}).items():
        assert a in txt, f'{f}: falta el marcador {a}'
        txt = txt.replace(a, b)
    assert '{{' not in txt, f'{f}: queda un marcador sin sustituir'
    page(path, title, desc, f'<section class="hero"><div class="wrap">{pre}<div class="prose">{txt}</div></div></section>{extra}')

def metodologia():
    camb = f'<section class="band" id="cambios"><div class="wrap"><span class="eyebrow">Cambios de método</span><h2>Lo que he cambiado, con fecha</h2><p class="sub">Cuando toco una regla, lo anoto aquí: qué cambia, por qué y qué dice eso de las cifras anteriores. Lo más reciente, arriba.</p>{"".join(f"<div class=\"log\"><time>{c["fecha"]} · {c["k"]}</time><h3>{c["t"]}</h3>" + "".join(f"<p>{x}</p>" for x in c["p"]) + "</div>" for c in CAMBIOS)}</div></section>'
    nombres = {'HORIZONTE': 'HORIZONTE plan de pensiones', 'GEN-Z': 'GEN-Z (versión anterior, hasta octubre de 2026)', 'CRYPTO': 'CRYPTO (versión con altcoins, hasta noviembre de 2026)'}
    tabla = ''.join(f'<tr><th scope="row">{nombres.get(k, k)}</th><td>{E[k]["riesgo"]} / 5</td><td>{pct(ST[k]["vol"], 1, False)}</td><td>{pct(ST[k]["worst"])}</td></tr>' for k in E)
    h, g = ST['HORIZONTE'], ST['GEDA']
    ejemplo = f'HORIZONTE tiene un 2 y GEDA un 4, aunque la peor caída de HORIZONTE ({pct(h["worst"])}) ha sido mayor que la de GEDA ({pct(g["worst"])}): la volatilidad de GEDA ({pct(g["vol"], 1, False)}) es mucho más alta que la de HORIZONTE ({pct(h["vol"], 1, False)})' if h['worst'] < g['worst'] and g['vol'] > h['vol'] else 'el nivel mira sobre todo cuánto oscila la cartera mes a mes, no solo su peor caída'
    y, m = ST['GEDA']['last_ym']
    periodo = f'datos mensuales hasta el {FECHA_CORTA}' + (f' ({y} incluye solo enero–{MES[m-1]})' if m < 12 else '')
    prosa('/metodologia/', 'metodologia.html', 'Metodología y cambios de método | Tu Amigo Inversor', 'Cómo calculo cada cifra, qué riesgos tiene cada cartera y todos los cambios de método, con fecha.', camb + suscripcion(), rep={'{{PERIODO}}': periodo, '{{TABLA_RIESGO}}': tabla, '{{EJEMPLO_RIESGO}}': ejemplo})

def informes():
    items = ''
    for key in sorted((k for k, v in INF.items() if v), reverse=True):
        y, m = map(int, key.split('-')); img = f'/assets/img/informes/informe-{key}.webp'
        items += f'<div class="item">{f"<a href=\"{INF[key]}\"><img src=\"{img}\" alt=\"Portada del informe de {mes_txt(y,m)}\" loading=\"lazy\" style=\"border:2px solid var(--ink);margin-bottom:10px\"></a>" if os.path.exists(img[1:]) else ""}<h3><a href="{INF[key]}">Informe de {mes_txt(y,m)}</a></h3><p>Enviado el día 1. Posiciones de {MES[m-1]} y resultados hasta el mes anterior.</p></div>'
    pend = sum(1 for v in INF.values() if not v)
    body = f'''<section class="hero"><div class="wrap"><span class="eyebrow">Informes publicados</span><h1>Así es lo que llega al correo</h1><p class="lead">Los informes ya enviados, tal cual salieron. Sirven para ver el formato y para comprobar que lo que cuenta el registro se dijo en su día.</p>
<div class="g3" style="margin-top:30px">{items}</div>
<p class="note">{f"Quedan {pend} informes anteriores por subir (desde julio de 2025). " if pend else ""}El de cada mes llega a los suscriptores el día 1; aquí lo subo a mediados de mes.</p></div></section>{suscripcion()}'''
    page('/informes/', 'Informes mensuales publicados | Tu Amigo Inversor', 'Los informes mensuales ya enviados, en PDF, para ver el formato y comprobar el registro.', body)

# ---------- blog ----------
ARTS = []
def cargar_articulos():
    for f in sorted(glob.glob('articulos/2*.md'), reverse=True):
        raw = open(f).read(); _, fm, md = raw.split('---', 2); meta = yaml.safe_load(fm)
        slug = re.sub(r'^\d{4}-\d{2}-\d{2}-', '', os.path.basename(f)[:-3])
        fecha = meta['fecha'] if isinstance(meta['fecha'], datetime.date) else datetime.date.fromisoformat(str(meta['fecha']))
        ARTS.append(dict(slug=slug, url=f'/aprende/{slug}/', title=meta['title'], fecha=fecha, cat=meta.get('categoria', ''), resumen=meta.get('resumen', ''), img='/' + meta['imagen'].lstrip('/') if meta.get('imagen') else None, md=md, sig=(meta.get('siguiente_texto'), meta.get('siguiente_url'))))
MUERTAS = {'/combinar-estrategias/': '/aprende/combinar-estrategias-inversion/', '/ejemplo-practico/': '/como-seguirlo/', '/test/': '/comparador/', '/simulador/': '/comparador/', '/empieza-aqui/': '/', '/glosario/': '/blog/'}
def blog():
    for a in ARTS:
        h = markdown.markdown(a['md'], extensions=['tables', 'fenced_code', 'sane_lists', 'attr_list'])
        for old, new in MUERTAS.items(): h = h.replace(f'href="{old}"', f'href="{new}"')
        h = re.sub(r'(src|href)="(?:\.\./)*assets/', r'\1="/assets/', h).replace('<table>', '<div class="tw" style="margin:14px 0"><table>').replace('</table>', '</table></div>')
        sig = f'<p class="cta"><a class="btn g" href="{MUERTAS.get(a["sig"][1], a["sig"][1])}">{esc(a["sig"][0])}</a></p>' if a['sig'][0] and a['sig'][1] else ''
        img = f'<img src="{a["img"]}" alt="" width="1200" height="630">' if a['img'] and os.path.exists(a['img'][1:]) else ''
        body = f'<section class="hero"><div class="wrap"><article class="prose"><span class="eyebrow">{esc(a["cat"])} · {a["fecha"].day} de {mes_txt(a["fecha"].year, a["fecha"].month)}</span><h1>{esc(a["title"])}</h1>{img}{h}{sig}<p class="note">Esto es divulgación: cuento lo que hago yo. No es asesoramiento ni una recomendación para tu caso.</p></article></div></section>{suscripcion()}'
        page(a['url'], f'{a["title"]} | Tu Amigo Inversor', a['resumen'], body, og=a['img'] or '/assets/img/og-tuamigoinversor.jpg', kind='article')
    lis = ''.join(f'<li><time datetime="{a["fecha"]}">{a["fecha"].strftime("%d.%m.%Y")}<br>{esc(a["cat"])}</time><div><a href="{a["url"]}">{esc(a["title"])}</a><p>{esc(a["resumen"])}</p></div></li>' for a in ARTS)
    page('/blog/', 'Blog | Tu Amigo Inversor', 'Artículos sobre momentum, caídas, brókers, planes de pensiones y cómo aplico el informe mensual.', f'<section class="hero"><div class="wrap"><span class="eyebrow">Blog</span><h1>Para entender lo que lees en el informe</h1><ul class="posts" style="margin-top:30px">{lis}</ul></div></section>{suscripcion()}')
    items = ''.join(f'<item><title>{esc(a["title"])}</title><link>{BASE}{a["url"]}</link><guid>{BASE}{a["url"]}</guid><pubDate>{a["fecha"].strftime("%a, %d %b %Y")} 08:00:00 +0000</pubDate><description>{esc(a["resumen"])}</description></item>' for a in ARTS)
    open('feed.xml', 'w').write(f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>Tu Amigo Inversor</title><link>{BASE}/</link><description>Mis carteras, contadas cada día 1</description><language>es</language>{items}</channel></rss>')

# ---------- construir ----------
cargar_articulos()
home()
for k in E: ficha(k)
laboratorio(); registro(); comparador(); como_seguirlo(); metodologia(); informes(); blog()
retrato = '<img src="/assets/img/jose-wide.jpg" alt="Retrato de José Manuel García" style="border:2px solid var(--ink);max-width:46rem;width:100%;margin-bottom:26px">'
prosa('/sobre-mi/', 'sobre-mi.html', 'Sobre mí | Tu Amigo Inversor', 'José Manuel García: ingeniero, profesor de matemáticas e inversor particular desde 2006.', suscripcion(), pre=retrato)
prosa('/recomendaciones/', 'recomendaciones.html', 'Cómo elaboro los informes y conflictos de interés | Tu Amigo Inversor', 'Quién elabora los informes, cómo, qué intereses tengo y qué no es este proyecto.')
prosa('/aviso-legal/', 'aviso-legal.html', 'Aviso legal | Tu Amigo Inversor', 'Titular de la web y condiciones de uso de tuamigoinversor.com.')
prosa('/privacidad/', 'privacidad.html', 'Privacidad y cookies | Tu Amigo Inversor', 'Qué datos recojo, para qué y qué derechos tienes.')
for old, new in {**MUERTAS, '/aprende/': '/blog/', '/aprende/brokers/': '/blog/', '/aprende/brokers/cuenta-financia-europa/': '/aprende/cuenta-financia-europa/', '/informe-ejemplo/': '/informes/', '/seguimiento/': '/registro/'}.items(): redirect(old, new)
open('404.html', 'w').write('<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>No encontrada | Tu Amigo Inversor</title><meta name="robots" content="noindex"><link rel="stylesheet" href="' + BASE + '/assets/css/site.css"></head><body><main><section class="hero"><div class="wrap"><span class="eyebrow">Error 404</span><h1>Esta página no existe</h1><p class="lead">Puede que la haya movido al rehacer la web.</p><div class="cta"><a class="btn" href="' + BASE + '/">Ir al inicio</a><a class="btn g" href="' + BASE + '/registro/">Ver el registro</a></div></div></section></main></body></html>')
hoy = datetime.date.today().isoformat()
open('sitemap.xml', 'w').write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + ''.join(f'<url><loc>{BASE}{p}</loc><lastmod>{hoy}</lastmod></url>\n' for p in SITEMAP) + '</urlset>\n')
print('Páginas:', len(SITEMAP), '· artículos:', len(ARTS))
for k in E: s = ST[k]; print(f'{k:10} ytd {s["ytd"]:7.2f}  cagr {s["cagr"]:6.2f}  total {s["total"]:7.1f}  peor {s["worst"]:6.2f}  ahora {s["now"]:6.2f}  vol {s["vol"]:5.1f}')
