from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[2]
s=(R/'docs/qa/module08-2026-10-10-r1/verify.py').read_text(encoding='utf-8').replace('module08','module09').replace('8821','8822').replace('42060','32520').replace('| 08 |','| 09 |').replace('row08','row09')
s=s.replace('12335b40e9d6f0eefc923b8d2c27532ee77cf2c7e03f143aef85c7b296662485','7c0a77891bf7446cd54ab31b798868912e2f5f2ad4d7721edddc17c92481ea37').replace('dad996a1f6374fbc115c363ad3035313c7dcaefab13833c52034ef7dfa3338f9','1b432792876a4e921aed8bd0085fd6eae420adcc2579696f67b94dfcc0c8f5b3')
(P/'verify.py').write_text(s,encoding='utf-8')
