"""Automatisk retting av R1-03-funksjonsdrofting.

Hver sjekk i SJEKKER er én deltest, og poengene fordeles likt på dem.
De samme sjekkene ligger i "Test løsningen din"-cellen nederst i notebooken.
"""
import pytest

from notebook_loader import last_notebook

def naer(a, b, rel=1e-3):
    """Sant hvis tallet a er innenfor rel (relativt) av b."""
    try:
        a, b = float(a), float(b)
    except (TypeError, ValueError):
        return False
    if b == 0:
        return abs(a) < 1e-9
    return abs(a - b) <= rel * abs(b)


def S(tekst):
    """Gjør tekst om til et sympy-uttrykk, f.eks. S("x**2 - 1")."""
    import sympy
    return sympy.sympify(tekst, locals={n: sympy.Symbol(n) for n in ("N", "O", "Q", "S")})


def lik(a, b):
    """Sant hvis a og b er matematisk like.

    Lister og mengder sammenlignes uten hensyn til rekkefølge, tupler (koordinater) i rekkefølge.
    """
    import sympy
    if a is None:
        return False
    if isinstance(b, tuple):
        if not isinstance(a, (tuple, list, sympy.Tuple)) or len(a) != len(b):
            return False
        return all(lik(x, y) for x, y in zip(a, b))
    if isinstance(b, (list, set)):
        if isinstance(a, sympy.FiniteSet):
            a = list(a)
        if not isinstance(a, (list, tuple, set)) or len(a) != len(b):
            return False
        rest = list(a)
        for y in b:
            for i, x in enumerate(rest):
                if lik(x, y):
                    del rest[i]
                    break
            else:
                return False
        return True
    if isinstance(b, dict):
        if not isinstance(a, dict) or len(a) != len(b):
            return False
        a = {str(k): v for k, v in a.items()}
        return all(str(k) in a and lik(a[str(k)], v) for k, v in b.items())
    try:
        a, b = sympy.sympify(a), sympy.sympify(b)
    except (sympy.SympifyError, TypeError):
        return False
    vanlige = lambda u: u.subs({s: sympy.Symbol(s.name) for s in u.free_symbols})
    a, b = vanlige(a), vanlige(b)
    if isinstance(a, sympy.Set) or isinstance(b, sympy.Set):
        return a == b
    if getattr(b, "is_Relational", False):
        return a == b
    try:
        return sympy.simplify(a - b) == 0
    except TypeError:
        return a == b

oppgave = last_notebook("oppgave")

SJEKKER = [
    ('1a', "fd og fdd skal være f'(x) og f''(x)", "lik(fd, S('3*x**2 - 12*x + 9')) and lik(fdd, S('6*x - 12'))"),
    ('1b', 'ekstremal_x skal være [1, 3]', 'lik(ekstremal_x, [1, 3])'),
    ('1c', 'vendepunkt skal være (2, 2)', 'lik(vendepunkt, (2, 2))'),
    ('2_voksende', 'voksende skal være x ≤ 1 eller x ≥ 3', "lik(voksende, S('Union(Interval(-oo, 1), Interval(3, oo))')) or lik(voksende, S('Union(Interval.open(-oo, 1), Interval.open(3, oo))'))"),
    ('2_avtagende', 'avtagende skal være 1 ≤ x ≤ 3', "lik(avtagende, S('Interval(1, 3)')) or lik(avtagende, S('Interval.open(1, 3)'))"),
    ('3', 'vertikal skal være [2] og horisontal 2', 'lik(vertikal, [2]) and lik(horisontal, 2)'),
    ('4_null', 'drofting(x³ - 6x² + 9x) skal gi nullpunktene 0 og 3', "lik(drofting(S('x**3 - 6*x**2 + 9*x'))['nullpunkter'], [0, 3])"),
    ('4_ekstremal', 'drofting(x³ - 6x² + 9x) skal gi toppunkt (1, 4) og bunnpunkt (3, 0)', "lik(drofting(S('x**3 - 6*x**2 + 9*x'))['ekstremal'], [(1, 4, 'topp'), (3, 0, 'bunn')])"),
    ('4_vende', 'drofting(x³ - 6x² + 9x) skal gi vendepunktet (2, 2)', "lik(drofting(S('x**3 - 6*x**2 + 9*x'))['vendepunkter'], [(2, 2)])"),
    ('4_fjerdegrad', 'drofting(x⁴ - 2x²) skal gi riktige ekstremalpunkter og to vendepunkter', "lik(drofting(S('x**4 - 2*x**2'))['ekstremal'], [(-1, -1, 'bunn'), (0, 0, 'topp'), (1, -1, 'bunn')]) and lik(drofting(S('x**4 - 2*x**2'))['vendepunkter'], [(-1/S('sqrt(3)'), S('-5/9')), (1/S('sqrt(3)'), S('-5/9'))])"),
    ('4_ingen_vende', "drofting(x⁴) skal ikke gi vendepunkt i x = 0 (f'' skifter ikke fortegn)", "drofting(S('x**4'))['vendepunkter'] == []"),
]


@pytest.mark.parametrize(
    "beskrivelse,uttrykk", [s[1:] for s in SJEKKER], ids=[s[0] for s in SJEKKER]
)
def test_sjekk(beskrivelse, uttrykk):
    navnerom = {**vars(oppgave), "naer": naer, "lik": lik, "S": S}
    assert eval(uttrykk, navnerom), beskrivelse
