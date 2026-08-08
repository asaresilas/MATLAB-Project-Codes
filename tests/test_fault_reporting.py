"""Regression suite for the two reported defects.

1. Multi-fault naming: every active fault must be named and explained.
2. Severity: the FAULT parameter set must report WARNING, not CRITICAL —
   including when the thermal frame carries a housing hotspot, which used to
   overwrite the winding temperature and escalate WARNING -> CRITICAL.
"""
import os, sys, asyncio
import numpy as np

ROOT = r"D:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes"
os.chdir(ROOT); sys.path.insert(0, os.path.join(ROOT, "backend"))
sys.stdout.reconfigure(encoding="utf-8")

FS, N = 12000.0, 2048
P = {
 "NORMAL":   dict(A=0.0,    rpm=1480, I=85.0,  Tk=333.15, Ta=313.15),
 "FAULT":    dict(A=4000.0, rpm=1465, I=110.0, Tk=351.15, Ta=298.15),
 "CRITICAL": dict(A=8000.0, rpm=1440, I=138.0, Tk=408.15, Ta=298.15),
}

def build(p, thermal=None):
    t = np.arange(N)/FS
    om = p["rpm"]*2*np.pi/60; fr = om/(2*np.pi)
    bpfo = (9/2)*fr*(1-(25.4e-3/120.65e-3))
    v = (0.50*np.sin(2*np.pi*fr*t)+0.15*np.sin(2*np.pi*2*fr*t+1.2)
         +0.08*np.sin(2*np.pi*317*t+0.3)+0.08*np.sin(2*np.pi*853*t+2.1))
    if p["A"] > 0:
        ph = np.mod(t, 1.0/bpfo)
        v += (p["A"]/300.0)*np.exp(-400.0*ph)*np.sin(2*np.pi*2500.0*ph)
    amp = p["I"]*np.sqrt(2)
    c = np.stack([amp*np.sin(2*np.pi*50*t), amp*np.sin(2*np.pi*50*t-2.094),
                  amp*np.sin(2*np.pi*50*t+2.094)], axis=1)
    d = {"vibration": (v/9.81).tolist(), "current": c.tolist(),
         "scalars": [p["rpm"], 484.0, p["Tk"], p["Ta"]]}
    if thermal is not None:
        d["thermal_image"] = thermal
    return d

async def main():
    from app.services.model_registry import ModelRegistry
    ModelRegistry().load_models()
    from app.api.websocket_handler import prediction_engine

    # 3x3 frame whose hottest cell (110 C) sits above the 78 C winding.
    # Old code copied 110 C onto motor_temp -> dT = 85 K > 70 K -> false CRITICAL.
    hotspot = [[80.0+273.15, 92.0+273.15, 78.0+273.15],
               [88.0+273.15, 110.0+273.15, 84.0+273.15],
               [76.0+273.15, 90.0+273.15, 79.0+273.15]]

    cases = [
        ("NORMAL",   None,                                    "NORMAL",   0),
        ("FAULT",    None,                                    "WARNING",  2),
        ("FAULT",    (np.ones((3,3))*P["FAULT"]["Tk"]).tolist(), "WARNING", 2),
        ("FAULT",    hotspot,                                 "WARNING",  2),   # regression
        ("CRITICAL", None,                                    "CRITICAL", 2),
        ("CRITICAL", (np.ones((3,3))*P["CRITICAL"]["Tk"]).tolist(), "CRITICAL", 2),
    ]

    print("="*76); print("REGRESSION SUITE"); print("="*76)
    failures = 0
    for i, (scen, therm, want_alert, want_nfaults) in enumerate(cases, 1):
        r = await prediction_engine.predict(build(P[scen], therm))
        got   = r.get("alert_level")
        fl    = r.get("faults") or []
        name  = r.get("fault_type_name")
        tag   = ("hotspot frame" if therm is hotspot
                 else "uniform frame" if therm else "no frame")
        ok_a  = (got == want_alert)
        ok_n  = (len(fl) == want_nfaults)
        # every listed fault must be fully described
        ok_d  = all(f.get("name") and f.get("description") and f.get("action")
                    and f.get("component") for f in fl)
        # name must enumerate the faults, never the old opaque label
        ok_l  = (name != "Multiple Faults") and (len(fl) < 2 or "+" in (name or ""))
        ok = ok_a and ok_n and ok_d and ok_l
        failures += (not ok)
        print(f"\n{i}. {scen} / {tag}")
        print(f"   alert     {'OK ' if ok_a else 'FAIL'}  want={want_alert:8s} got={got}")
        print(f"   faults    {'OK ' if ok_n else 'FAIL'}  want={want_nfaults} got={len(fl)}  name={name!r}")
        print(f"   described {'OK ' if ok_d else 'FAIL'}  every fault has name/component/description/action")
        print(f"   listed    {'OK ' if ok_l else 'FAIL'}  no opaque 'Multiple Faults' label")
        for f in fl:
            print(f"      • {f['name']} — {', '.join(f.get('evidence', []))}")

    print("\n" + "="*76)
    print(f"RESULT: {len(cases)-failures}/{len(cases)} passed")
    print("="*76)
    return failures

sys.exit(asyncio.run(main()))
