import math

# Serie E24 standard per componenti commerciali
E24_SERIES = [1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0, 
              3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1]

def get_commercial_value(value):
    """Trova il valore commerciale più vicino basato sulla Serie E24."""
    if value == 0:
        return 0
    exp = math.floor(math.log10(abs(value)))
    mantissa = abs(value) / (10 ** exp)
    closest_mantissa = min(E24_SERIES, key=lambda x: abs(x - mantissa))
    return math.copysign(closest_mantissa * (10 ** exp), value)

def format_eng(value, unit=""):
    """Converte un float in notazione ingegneristica elegante (es. 5e-6 -> 5 µF)"""
    if value == 0:
        return f"0 {unit}"
    
    exponent = int(math.floor(math.log10(abs(value)) / 3.0) * 3)
    mantissa = value / (10 ** exponent)
    
    prefixes = {-12: 'p', -9: 'n', -6: 'µ', -3: 'm', 0: '', 3: 'k', 6: 'M', 9: 'G'}
    prefix = prefixes.get(exponent, f"e{exponent}")
    
    return f"{mantissa:.4g} {prefix}{unit}".strip()

def math_html(text):
    """Formatta una stringa matematica lineare con HTML pulito e leggibile."""
    return f"<span style='font-family: \"Cambria Math\", \"Times New Roman\", serif; font-size: 1.1em; color: #0071e3;'>{text}</span>"

def denormalize_component(comp_type, val_n, filter_type, w0, R1, B=None):
    """Calcola la denormalizzazione e restituisce i valori con le formule lineari in HTML nativo."""
    result = {}
    
    if filter_type == 'LP':
        if comp_type == 'L':
            result['type'] = 'Induttore (L)'
            result['desc'] = 'Mantiene la natura di Induttore.'
            result['value'] = (R1 * val_n) / w0
            result['formula'] = math_html("<i>L</i> = (<i>R</i><sub>1</sub> &middot; <i>L<sub>n</sub></i>) / <i>&omega;</i><sub>0</sub>")
        elif comp_type == 'C':
            result['type'] = 'Condensatore (C)'
            result['desc'] = 'Mantiene la natura di Condensatore.'
            result['value'] = val_n / (R1 * w0)
            result['formula'] = math_html("<i>C</i> = <i>C<sub>n</sub></i> / (<i>R</i><sub>1</sub> &middot; <i>&omega;</i><sub>0</sub>)")

    elif filter_type == 'HP':
        if comp_type == 'L':
            result['type'] = 'Condensatore (C)'
            result['desc'] = 'Duale: un Induttore normalizzato diventa un Condensatore.'
            result['value'] = 1 / (R1 * w0 * val_n)
            result['formula'] = math_html("<i>C</i> = 1 / (<i>R</i><sub>1</sub> &middot; <i>&omega;</i><sub>0</sub> &middot; <i>L<sub>n</sub></i>)")
        elif comp_type == 'C':
            result['type'] = 'Induttore (L)'
            result['desc'] = 'Duale: un Condensatore normalizzato diventa un Induttore.'
            result['value'] = R1 / (w0 * val_n)
            result['formula'] = math_html("<i>L</i> = <i>R</i><sub>1</sub> / (<i>&omega;</i><sub>0</sub> &middot; <i>C<sub>n</sub></i>)")

    elif filter_type == 'BP':
        if comp_type == 'L':
            result['type'] = 'Risonatore LC Serie'
            result['desc'] = 'L\'Induttore diventa una serie tra Induttore e Condensatore.'
            result['L_val'] = (R1 * val_n) / B
            result['C_val'] = B / (R1 * (w0**2) * val_n)
            result['formula_L'] = math_html("<i>L<sub>serie</sub></i> = (<i>R</i><sub>1</sub> &middot; <i>L<sub>n</sub></i>) / <i>B</i>")
            result['formula_C'] = math_html("<i>C<sub>serie</sub></i> = <i>B</i> / (<i>R</i><sub>1</sub> &middot; <i>&omega;</i><sub>0</sub><sup>2</sup> &middot; <i>L<sub>n</sub></i>)")
        elif comp_type == 'C':
            result['type'] = 'Risonatore LC Parallelo'
            result['desc'] = 'Il Condensatore diventa un parallelo tra Induttore e Condensatore.'
            result['C_val'] = val_n / (R1 * B)
            result['L_val'] = (R1 * B) / ((w0**2) * val_n)
            result['formula_C'] = math_html("<i>C<sub>par</sub></i> = <i>C<sub>n</sub></i> / (<i>R</i><sub>1</sub> &middot; <i>B</i>)")
            result['formula_L'] = math_html("<i>L<sub>par</sub></i> = (<i>R</i><sub>1</sub> &middot; <i>B</i>) / (<i>&omega;</i><sub>0</sub><sup>2</sup> &middot; <i>C<sub>n</sub></i>)")

    elif filter_type == 'SB':
        if comp_type == 'L':
            result['type'] = 'Risonatore LC Parallelo'
            result['desc'] = 'L\'Induttore diventa un parallelo tra Induttore e Condensatore.'
            result['L_val'] = (R1 * B * val_n) / (w0**2)
            result['C_val'] = 1 / (R1 * B * val_n)
            result['formula_L'] = math_html("<i>L<sub>par</sub></i> = (<i>R</i><sub>1</sub> &middot; <i>B</i> &middot; <i>L<sub>n</sub></i>) / <i>&omega;</i><sub>0</sub><sup>2</sup>")
            result['formula_C'] = math_html("<i>C<sub>par</sub></i> = 1 / (<i>R</i><sub>1</sub> &middot; <i>B</i> &middot; <i>L<sub>n</sub></i>)")
        elif comp_type == 'C':
            result['type'] = 'Risonatore LC Serie'
            result['desc'] = 'Il Condensatore diventa una serie tra Induttore e Condensatore.'
            result['C_val'] = (B * val_n) / (R1 * (w0**2))
            result['L_val'] = R1 / (B * val_n)
            result['formula_C'] = math_html("<i>C<sub>serie</sub></i> = (<i>B</i> &middot; <i>C<sub>n</sub></i>) / (<i>R</i><sub>1</sub> &middot; <i>&omega;</i><sub>0</sub><sup>2</sup>)")
            result['formula_L'] = math_html("<i>L<sub>serie</sub></i> = <i>R</i><sub>1</sub> / (<i>B</i> &middot; <i>C<sub>n</sub></i>)")

    return result