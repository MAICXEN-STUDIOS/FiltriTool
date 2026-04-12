import numpy as np
import scipy.signal as signal
import math
import io
import base64
from matplotlib.figure import Figure

def render_latex(formula, fontsize=16, color="#0071e3"):
    """Renderizza una stringa LaTeX in un'immagine PNG base64 per inserirla in QTextEdit."""
    fig = Figure(figsize=(6, 0.8), dpi=120)
    fig.patch.set_alpha(0) 
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis('off')
    
    ax.text(0.5, 0.5, f"${formula}$", size=fontsize, color=color, 
            ha='center', va='center', usetex=False)
    
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', transparent=True, pad_inches=0.05)
    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode('utf-8')
    return f'<div style="text-align:center;"><img src="data:image/png;base64,{img_b64}"></div>'

def get_filter_info(approx):
    info = ""
    if approx == "Butterworth":
        eq = r"|H(j\omega)|^2 = \frac{1}{1 + \left(\frac{\omega}{\omega_c}\right)^{2N}}"
        info = (
            "<h3>Filtro di Butterworth</h3>"
            "<p><b>Funzione di Trasferimento:</b></p>" + render_latex(eq) +
            "<ul>"
            "<li><b>Ampiezza:</b> Massimamente piatta in banda passante (nessun ripple).</li>"
            "<li><b>Transizione:</b> Decadimento asintotico di 20·N dB/decade.</li>"
            "</ul>"
        )
    elif approx == "Chebyshev I":
        eq = r"|H(j\omega)|^2 = \frac{1}{1 + \epsilon^2 T_N^2\left(\frac{\omega}{\omega_p}\right)}"
        info = (
            "<h3>Filtro di Chebyshev (Tipo I)</h3>"
            "<p><b>Funzione di Trasferimento:</b></p>" + render_latex(eq) +
            "<ul>"
            "<li><b>Ampiezza:</b> Ripple costante in banda passante.</li>"
            "<li><b>Transizione:</b> Ripida, poli disposti su un'ellisse.</li>"
            "</ul>"
        )
    elif approx == "Chebyshev II":
        eq = r"|H(j\omega)|^2 = \frac{1}{1 + \epsilon^2 \left[ T_N\left(\frac{\omega_s}{\omega}\right) \right]^{-2}}"
        info = (
            "<h3>Filtro di Chebyshev Inverso (Tipo II)</h3>"
            "<p><b>Funzione di Trasferimento:</b></p>" + render_latex(eq) +
            "<ul>"
            "<li><b>Ampiezza:</b> Piatta in banda passante, ripple in banda oscura.</li>"
            "</ul>"
        )
    elif approx == "Ellittico (Cauer)":
        eq = r"|H(j\omega)|^2 = \frac{1}{1 + \epsilon^2 R_N^2\left(\xi, \frac{\omega}{\omega_p}\right)}"
        info = (
            "<h3>Filtro Ellittico (di Cauer)</h3>"
            "<p><b>Funzione di Trasferimento:</b></p>" + render_latex(eq) +
            "<ul>"
            "<li><b>Ampiezza:</b> Ripple sia in banda passante che oscura. Transizione massimamente ripida.</li>"
            "</ul>"
        )
    elif approx == "Bessel":
        eq = r"H(s) = \frac{\theta_N(0)}{\theta_N(s/\omega_0)}"
        info = (
            "<h3>Filtro di Bessel (Bessel-Thomson)</h3>"
            "<p><b>Funzione di Trasferimento:</b></p>" + render_latex(eq) +
            "<ul>"
            "<li><b>Fase:</b> Ritardo di gruppo massimamente piatto (minima distorsione).</li>"
            "</ul>"
        )
    return info

def calc_filter_parameters(fp, fs, Ap, As):
    k = fp / fs 
    eps = math.sqrt(10**(Ap/10) - 1) 
    D_req = math.sqrt(10**(As/10) - 1) 
    d = eps / D_req 
    return k, eps, d

def design_filter_transfer_function(approx, fp, fs, Ap, As):
    wp = 2 * np.pi * fp
    ws = 2 * np.pi * fs
    b, a = None, None
    N, Wn = 0, 0
    
    try:
        if approx == "Butterworth":
            N, Wn = signal.buttord(wp, ws, Ap, As, analog=True)
            b, a = signal.butter(N, Wn, btype='low', analog=True)
        elif approx == "Chebyshev I":
            N, Wn = signal.cheb1ord(wp, ws, Ap, As, analog=True)
            if N % 2 == 0: N += 1 
            b, a = signal.cheby1(N, Ap, Wn, btype='low', analog=True)
        elif approx == "Chebyshev II":
            N, Wn = signal.cheb2ord(wp, ws, Ap, As, analog=True)
            b, a = signal.cheby2(N, As, Wn, btype='low', analog=True)
        elif approx == "Ellittico (Cauer)":
            N, Wn = signal.ellipord(wp, ws, Ap, As, analog=True)
            b, a = signal.ellip(N, Ap, As, Wn, btype='low', analog=True)
        elif approx == "Bessel":
            N, _ = signal.buttord(wp, ws, Ap, As, analog=True)
            N = min(N + 2, 8) 
            Wn = wp
            b, a = signal.bessel(N, Wn, btype='low', analog=True, norm='mag')
            
        # FIX: Applichiamo l'attenuazione di partizione dovuta a R1 = R2 (-6dB)
        if b is not None:
            b = b * 0.5
            
        return N, Wn, b, a
    except Exception as e:
        return None, None, None, None

def calc_bode_data(b, a, fp, fs):
    f_min = fp / 10
    f_max = fs * 10
    w = np.logspace(np.log10(2*np.pi*f_min), np.log10(2*np.pi*f_max), 1000)
    w, h = signal.freqs(b, a, worN=w)
    
    f_hz = w / (2 * np.pi)
    mag_linear = np.abs(h)
    phase_rad = np.unwrap(np.angle(h))
    phase_deg = np.degrees(phase_rad)
    group_delay = -np.gradient(phase_rad, w)
    
    return f_hz, mag_linear, phase_deg, group_delay

def synthesize_lc_ladder(approx, N, fp, Ap, R1):
    components = []
    wp = 2 * np.pi * fp
    
    if approx == "Butterworth":
        for k in range(1, N + 1):
            gk = 2 * math.sin(((2 * k - 1) * math.pi) / (2 * N))
            if k % 2 != 0:
                components.append(('L', (gk * R1) / wp))
            else:
                components.append(('C', gk / (R1 * wp)))
                
    elif approx == "Chebyshev I":
        eps = math.sqrt(10**(Ap/10) - 1)
        gamma = math.sinh((1/N) * math.asinh(1/eps))
        a = [math.sin(((2*k - 1)*math.pi) / (2*N)) for k in range(1, N+1)]
        b = [gamma**2 + (math.sin((k*math.pi)/N))**2 for k in range(1, N+1)]
        g = [0] * N
        g[0] = (2 * a[0]) / gamma
        for k in range(1, N):
            g[k] = (4 * a[k-1] * a[k]) / (b[k-1] * g[k-1])
        for k in range(N):
            if (k+1) % 2 != 0:
                components.append(('L', (g[k] * R1) / wp))
            else:
                components.append(('C', g[k] / (R1 * wp)))
    else:
        return None 
    return components