"""Author local demo documents. Screenshots are captured separately in the browser."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.runtime'))
import fitz
OUT=ROOT/'evaluation'/'sources'
OUT.mkdir(parents=True,exist_ok=True)
style='''<style>body{font-family:Arial,sans-serif;background:#f5f7f1;color:#294533;margin:0;padding:30px}main{max-width:760px;margin:auto;background:white;padding:30px;border-radius:14px}h1{font-size:28px;line-height:1.2}p{font-size:16px;line-height:1.7;color:#65755d}table{border-collapse:collapse;width:100%;font-size:18px}td,th{padding:16px 8px;border-bottom:1px solid #dce5d5;text-align:left}small{color:#77866d}pre{font-size:15px;line-height:1.9;white-space:pre-wrap;background:#eef3e8;padding:18px}footer{font-size:12px;margin-top:24px;color:#8c967f}</style>'''
pages={
'pricing.html':'''<small>ACME CLOUD · PRODUCT REVIEW</small><h1>Simple plans. Clear pricing.</h1><p>Monthly subscription pricing for the product team.</p><table><tr><th>Plan</th><th>Price / month</th><th>Projects</th></tr><tr><td>Starter</td><td>$19</td><td>3</td></tr><tr><td>Pro</td><td>$49</td><td>Unlimited</td></tr><tr><td>Enterprise</td><td>Custom</td><td>Unlimited</td></tr></table><p>Pro includes advanced analytics and priority support.</p>''',
'other-pricing.html':'''<small>ORBIT STORAGE · VENDOR REVIEW</small><h1>Storage plans for your team</h1><table><tr><th>Plan</th><th>Price / month</th></tr><tr><td>Basic</td><td>$12</td></tr><tr><td>Pro</td><td>$79</td></tr><tr><td>Business</td><td>$149</td></tr></table><p>Pro includes 2 TB of storage and version history.</p>''',
'code.html':'''<small>ENGINEERING NOTES</small><h1>React debounce hook</h1><p>Delay search requests until typing pauses.</p><pre>function useDebounce(value, delay = 300) {\n  const [result, setResult] = useState(value);\n  useEffect(() =&gt; {\n    const timer = setTimeout(() =&gt; {\n      setResult(value);\n    }, delay);\n    return () =&gt; clearTimeout(timer);\n  }, [value, delay]);\n  return result;\n}</pre>''',
'growth.html':'''<small>PRODUCT ANALYTICS</small><h1>Weekly active users</h1><p>24,892 active users · growth of 18.6%</p><svg viewBox="0 0 500 160" width="100%" role="img" aria-label="Weekly user growth"><path d="M20 135H480M20 85H480M20 35H480" stroke="#e2e9d9"/><path d="M20 130L100 110L180 120L260 60L340 70L420 20L480 10" fill="none" stroke="#71924f" stroke-width="4"/></svg><table><tr><th>Week</th><th>Active users</th></tr><tr><td>Week 1</td><td>14,200</td></tr><tr><td>Week 6</td><td>24,892</td></tr></table>'''
}
for name,body in pages.items():
    (OUT/name).write_text('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+name+'</title>'+style+'</head><body><main>'+body+'<footer>ContextOS evaluation source · authored fixture, not a customer document.</footer></main></body></html>',encoding='utf-8')
doc=fitz.open();page=doc.new_page(width=600,height=700)
for point,text,size in [((45,65),'ACME CLOUD | PRODUCT REVIEW',12),((45,110),'Simple plans. Clear pricing.',26),((45,155),'Monthly subscription pricing',15),((45,220),'Plan                  Price / month          Projects',16),((45,265),'Starter               $19                    3',17),((45,310),'Pro                   $49                    Unlimited',17),((45,355),'Enterprise            Custom                 Unlimited',17),((45,415),'Pro includes advanced analytics and priority support.',14),((45,640),'ContextOS evaluation source - authored fixture.',11)]:
    page.insert_text(point,text,fontsize=size,fontname='cour' if 200<point[1]<400 else 'helv',color=(.15,.25,.18))
doc.save(OUT/'pricing.pdf');doc.close()
print('Created four HTML sources and one PDF in',OUT)
