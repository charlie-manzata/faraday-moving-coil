import json, math
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Spira in campo magnetico", page_icon="🧲", layout="wide")
st.title("Spira quadrata in moto in un campo magnetico")
st.caption("Animazione eseguita nel browser per una maggiore fluidità.")

st.sidebar.header("Parametri")
L=st.sidebar.number_input("Lato della spira L (m)",0.10,10.0,1.0,0.10)
B=st.sidebar.number_input("Modulo del campo B (T)",0.0,20.0,1.0,0.10)
Bdir=st.sidebar.selectbox("Verso del campo",["Uscente dal piano","Entrante nel piano"])
motion=st.sidebar.radio("Legge del moto",["Moto uniforme","Moto uniformemente accelerato"])
if motion=="Moto uniforme":
    v0=st.sidebar.number_input("Velocità v (m/s)",0.01,20.0,0.50,0.05); a=0.0
else:
    v0=st.sidebar.number_input("Velocità iniziale v₀ (m/s)",0.0,20.0,0.20,0.05)
    a=st.sidebar.number_input("Accelerazione a (m/s²)",0.0,10.0,0.20,0.05)
gapm=st.sidebar.slider("Distanza iniziale dal campo (multipli di L)",0.10,1.50,0.50,0.10)
after=st.sidebar.slider("Tempo dopo l'ingresso completo (s)",0.5,4.0,1.5,0.1)
speed=st.sidebar.slider("Velocità animazione",0.25,3.0,1.0,0.25)
gap=gapm*L

def hit(target):
    d=target+gap
    if abs(a)<1e-14: return d/v0 if v0>0 else None
    disc=v0*v0+2*a*d
    return (-v0+math.sqrt(disc))/a if disc>=0 else None

tc,tf=hit(0),hit(L)
if tc is None or tf is None:
    st.error("La spira non raggiunge completamente la regione magnetica."); st.stop()
te=tf+after
cfg=json.dumps(dict(L=L,B=B,bs=1 if Bdir=="Uscente dal piano" else -1,v0=v0,a=a,gap=gap,tc=tc,tf=tf,te=te,speed=speed))

html=r'''<div id="fa">
<style>
#fa{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:#262730}
#fa .ctl{display:flex;gap:9px;align-items:center;flex-wrap:wrap;margin-bottom:10px}
#fa button{border:1px solid #bbb;border-radius:8px;background:white;padding:8px 15px;font-size:14px;cursor:pointer}
#fa .status{font-size:13px;color:#555}
#fa .grid{display:grid;grid-template-columns:minmax(0,3fr) minmax(280px,2fr);gap:12px}
#fa .panel{border:1px solid #ddd;border-radius:9px;padding:7px;background:white;min-width:0}
#fa canvas{width:100%;display:block} #scene{aspect-ratio:1.45/1} #graph{aspect-ratio:1.2/1}
#fa .legend{font-size:12px;color:#666;margin-top:5px}.blue{color:#1f77b4;font-weight:600}.red{color:#d62728;font-weight:600}
#fa .metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:7px;margin-top:10px}
#fa .m{border:1px solid #ddd;border-radius:8px;padding:8px}.lab{font-size:11px;color:#666}.val{font-size:17px;font-weight:600;margin-top:2px}
@media(max-width:760px){#fa .grid{grid-template-columns:1fr}#fa .metrics{grid-template-columns:repeat(2,1fr)}}
</style>
<div class="ctl"><button id="play">▶ Avvia / riprendi</button><button id="pause">⏸ Ferma</button><button id="reset">↺ Ricomincia</button><span id="status" class="status"></span></div>
<div class="grid"><div class="panel"><canvas id="scene"></canvas><div class="legend"><span class="blue">Blu</span>: B indotto · <span class="red">Rosso</span>: forza magnetica sul filo</div></div><div class="panel"><canvas id="graph"></canvas></div></div>
<div class="metrics"><div class="m"><div class="lab">Tempo</div><div class="val" id="mt"></div></div><div class="m"><div class="lab">Flusso</div><div class="val" id="mf"></div></div><div class="m"><div class="lab">Modulo f.e.m.</div><div class="val" id="me"></div></div><div class="m"><div class="lab">Corrente</div><div class="val" id="mi"></div></div></div>
<script>
(()=>{
const c=__CFG__,sc=document.getElementById("scene"),gc=document.getElementById("graph"),sx=sc.getContext("2d"),gx=gc.getContext("2d");
let t=0,run=false,last=null,raf=null; const dpr=Math.min(devicePixelRatio||1,2);
function size(cv){let r=cv.getBoundingClientRect(),w=Math.max(280,Math.round(r.width)),h=Math.max(220,Math.round(r.height));if(cv.width!==Math.round(w*dpr)||cv.height!==Math.round(h*dpr)){cv.width=Math.round(w*dpr);cv.height=Math.round(h*dpr)}cv.getContext("2d").setTransform(dpr,0,0,dpr,0,0);return[w,h]}
const xr=z=>-c.gap+c.v0*z+.5*c.a*z*z,vel=z=>c.v0+c.a*z,iw=z=>Math.max(0,Math.min(c.L,xr(z))),flux=z=>c.bs*c.B*c.L*iw(z);
const emf=z=>(xr(z)>0&&xr(z)<c.L)?c.B*c.L*Math.abs(vel(z)):0;
const cur=z=>!(xr(z)>0&&xr(z)<c.L)||c.B===0?"nessuna":c.bs>0?"oraria":"antioraria";
function arrow(x,x1,y1,x2,y2,col,w=2.2,h=9){let a=Math.atan2(y2-y1,x2-x1);x.save();x.strokeStyle=col;x.fillStyle=col;x.lineWidth=w;x.beginPath();x.moveTo(x1,y1);x.lineTo(x2,y2);x.stroke();x.beginPath();x.moveTo(x2,y2);x.lineTo(x2-h*Math.cos(a-Math.PI/6),y2-h*Math.sin(a-Math.PI/6));x.lineTo(x2-h*Math.cos(a+Math.PI/6),y2-h*Math.sin(a+Math.PI/6));x.closePath();x.fill();x.restore()}
function sym(x,cx,cy,dir,r,col,al=1){x.save();x.globalAlpha=al;x.strokeStyle=col;x.fillStyle=col;x.lineWidth=1.5;x.beginPath();x.arc(cx,cy,r,0,2*Math.PI);x.stroke();if(dir==="out"){x.beginPath();x.arc(cx,cy,r*.22,0,2*Math.PI);x.fill()}else{let d=r*.58;x.beginPath();x.moveTo(cx-d,cy-d);x.lineTo(cx+d,cy+d);x.moveTo(cx-d,cy+d);x.lineTo(cx+d,cy-d);x.stroke()}x.restore()}
function current(x,l,top,s,d){let k="#333",p=.055*s,q=.30*s;if(d==="antioraria"){arrow(x,l+q,top+s-p,l+s-q,top+s-p,k,2,8);arrow(x,l+s-p,top+s-q,l+s-p,top+q,k,2,8);arrow(x,l+s-q,top+p,l+q,top+p,k,2,8);arrow(x,l+p,top+q,l+p,top+s-q,k,2,8)}else{arrow(x,l+s-q,top+s-p,l+q,top+s-p,k,2,8);arrow(x,l+s-p,top+q,l+s-p,top+s-q,k,2,8);arrow(x,l+q,top+p,l+s-q,top+p,k,2,8);arrow(x,l+p,top+s-q,l+p,top+q,k,2,8)}}
function scene(){let [w,h]=size(sc);sx.clearRect(0,0,w,h);
let mn=-(1.2+c.gap/c.L)*c.L,mx=2.35*c.L;
let worldW=mx-mn, worldH=1.9*c.L;
let pad=10;
let scale=Math.min((w-2*pad)/worldW,(h-2*pad)/worldH);
let usedW=worldW*scale, usedH=worldH*scale;
let ox=(w-usedW)/2, oy=(h-usedH)/2;
let X=z=>ox+(z-mn)*scale;
let Y=z=>oy+usedH/2-z*scale;
let r=xr(t),l=r-c.L,left=X(l),right=X(r),top=Y(c.L/2),bot=Y(-c.L/2),side=c.L*scale,cx=(left+right)/2,cy=(top+bot)/2;sx.fillStyle="rgba(100,100,100,.08)";sx.fillRect(X(0),0,w-X(0),h);sx.strokeStyle="#555";sx.lineWidth=2;sx.beginPath();sx.moveTo(X(0),0);sx.lineTo(X(0),h);sx.stroke();sx.fillStyle="#333";sx.font="14px sans-serif";sx.fillText("B uniforme",X(0)+9,21);for(let i=0;i<5;i++)for(let j=0;j<4;j++)sym(sx,X(.25*c.L+i*1.75*c.L/4),Y(-.58*c.L+j*1.16*c.L/3),c.bs>0?"out":"in",Math.max(5,side*.035),"#555",.62);sx.strokeStyle="#222";sx.lineWidth=3;sx.strokeRect(left,top,side,bot-top);sym(sx,cx,top+.16*side,"out",Math.max(7,side*.042),"#222");sx.fillStyle="#222";sx.font="12px sans-serif";sx.textAlign="center";sx.fillText("n",cx,top+.085*side);sx.textAlign="left";let d=cur(t);if(d!=="nessuna"){current(sx,left,top,side,d);let biy=cy+.16*side;sym(sx,cx,biy,c.bs>0?"in":"out",Math.max(9,side*.055),"#1f77b4");sx.fillStyle="#1f77b4";sx.textAlign="center";sx.font="italic bold 15px serif";sx.fillText("B",cx,biy+.14*side);sx.font="10px serif";sx.fillText("ind",cx+.10*side,biy+.17*side);sx.textAlign="left";let vd=vel(t)>0?-1:1,fy=cy-.12*side,fstart=right-.015*side*vd,fx=right+vd*.34*side;arrow(sx,fstart,fy,fx,fy,"#d62728",3,11);let flx=(fstart+fx)/2;sx.fillStyle="#d62728";sx.textAlign="center";sx.font="italic bold 15px serif";sx.fillText("F",flx,fy-.075*side);sx.font="10px serif";sx.fillText("L",flx+.065*side,fy-.055*side);sx.textAlign="left"}sx.fillStyle="#333";sx.font="13px sans-serif";sx.fillText("t = "+t.toFixed(2)+" s",12,h-12)}
function graph(){let [w,h]=size(gc);gx.clearRect(0,0,w,h);let ml=50,mr=12,mt=30,mb=40,W=w-ml-mr,H=h-mt-mb,vm=Math.max(Math.abs(c.v0),Math.abs(vel(c.te))),em=Math.max(c.B*c.L*vm,1e-9),X=z=>ml+z/c.te*W,Y=z=>mt+H-z/(em*1.15)*H;gx.strokeStyle="#555";gx.lineWidth=1;gx.beginPath();gx.moveTo(ml,mt);gx.lineTo(ml,mt+H);gx.lineTo(ml+W,mt+H);gx.stroke();gx.setLineDash([5,5]);gx.strokeStyle="rgba(80,80,80,.35)";[c.tc,c.tf].forEach(z=>{gx.beginPath();gx.moveTo(X(z),mt);gx.lineTo(X(z),mt+H);gx.stroke()});gx.setLineDash([]);gx.strokeStyle="#1f77b4";gx.lineWidth=2.5;gx.beginPath();let n=Math.max(2,Math.ceil(240*t/c.te));for(let j=0;j<=n;j++){let z=t*j/n;j?gx.lineTo(X(z),Y(emf(z))):gx.moveTo(X(z),Y(emf(z)))}gx.stroke();gx.fillStyle="#1f77b4";gx.beginPath();gx.arc(X(t),Y(emf(t)),4.5,0,2*Math.PI);gx.fill();gx.fillStyle="#333";gx.font="bold 15px sans-serif";gx.textAlign="center";gx.fillText("Modulo della f.e.m. indotta",ml+W/2,17);gx.font="13px sans-serif";gx.fillText("t (s)",ml+W/2,h-9);gx.save();gx.translate(14,mt+H/2);gx.rotate(-Math.PI/2);gx.fillText("modulo f.e.m. (V)",0,0);gx.restore();gx.font="10px sans-serif";gx.fillStyle="#666";gx.fillText("inizio ingresso",X(c.tc),mt+12);gx.fillText("ingresso completo",X(c.tf),mt+24);gx.textAlign="left"}
function render(){scene();graph();document.getElementById("mt").textContent=t.toFixed(2)+" s";document.getElementById("mf").textContent=flux(t).toPrecision(4)+" Wb";document.getElementById("me").textContent=emf(t).toPrecision(4)+" V";document.getElementById("mi").textContent=cur(t);document.getElementById("status").textContent=t<c.tc?"Avvicinamento al campo":t<c.tf?"Ingresso nel campo":t<c.te?"Spira completamente immersa: f.e.m. nulla":"Simulazione terminata"}
function tick(ts){if(!run)return;if(last===null)last=ts;let d=Math.min((ts-last)/1000,.08);last=ts;t+=d*c.speed;if(t>=c.te){t=c.te;run=false;last=null;render();return}render();raf=requestAnimationFrame(tick)}
document.getElementById("play").addEventListener("click",()=>{if(t>=c.te)t=0;if(!run){run=true;last=null;raf=requestAnimationFrame(tick)}});document.getElementById("pause").addEventListener("click",()=>{run=false;last=null;if(raf)cancelAnimationFrame(raf);render()});document.getElementById("reset").addEventListener("click",()=>{run=false;last=null;if(raf)cancelAnimationFrame(raf);t=0;render()});new ResizeObserver(render).observe(document.getElementById("fa"));render();
})();
</script></div>'''.replace("__CFG__",cfg)

components.html(html,height=690,scrolling=False)
st.markdown("---"); st.subheader("Spiegazione")
st.write("Prima del contatto il flusso non varia e il modulo della f.e.m. è nullo. Durante l'ingresso cresce l'area immersa:")
st.latex(r"A_{\mathrm{imm}}=Lx")
st.write("Per il moto uniforme:"); st.latex(r"|\mathcal{E}|=|B|Lv")
st.write("Nel moto uniformemente accelerato:"); st.latex(r"|\mathcal{E}|=|B|L|v(t)|")
st.write("Quando la spira è completamente immersa nel campo uniforme:"); st.latex(r"\Phi=BL^2=\mathrm{costante}"); st.latex(r"|\mathcal{E}|=0")
st.write("La freccia rossa rappresenta la forza magnetica sul lato percorso dalla corrente indotta:"); st.latex(r"\vec F_L=I\,\vec L\times\vec B")
st.write("Durante l'ingresso questa forza è opposta al moto, in accordo con la legge di Lenz.")
