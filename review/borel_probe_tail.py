import math, csv
N=8000
def tails(a):
    B=[0.0]*(N+2)
    for n in range(1,N+1): B[n]=math.exp(-a*n+(n-1)*math.log(a*n)-math.lgamma(n+1))
    S0=[0.0]*(N+2); S1=[0.0]*(N+2)
    for n in range(N,0,-1):
        S0[n-1]=S0[n]+B[n]; S1[n-1]=S1[n]+n*B[n]
    return S0,S1
T={a:tails(a) for a in (.375,.5,.625,.75)}
def pref(L,a):
    S0,S1=T[a]; return (1-a)*(S1[L]-L*S0[L])
def rho_bound(L,a):
    r=a*math.exp(1-a); return r**L/(1-r)
print("sanity: mean probes = 1+sum_L P(all L slots occupied)  vs Knuth")
for a in (.375,.5,.625,.75):
    print(a, round(1+sum(pref(L,a) for L in range(1,N-1)),3), round(.5*(1+1/(1-a)**2),3))
rows=list(csv.DictReader(open('../results/hardening/probes.csv')))
print("\nm=65536, murmur3: load  L   measured(1e7 samples)  exact-limit(Borel)  paper-bound  bound/exact")
for r in rows:
    if r['hash']!='murmur3' or r['index_slots']!='65536': continue
    a=float(r['load'])
    for L in (32,64,128,256,512):
        meas=float(r['measured_gt_%d'%L]); ex=pref(L,a); b=float(r['bound_gt_%d'%L])
        print(f"  {a:5.3f} {L:4d}  {meas:9.2e}  {ex:11.3e}  {b:11.3e}  {b/ex if ex>0 else float('nan'):8.1f}")
print("\nsmallest L with per-declaration refusal prob <= eps:")
for a in (.375,.5,.75):
    for eps in (1e-6,1e-9):
        Lb=next(L for L in range(1,5000) if rho_bound(L,a)<=eps)
        Le=next(L for L in range(1,N-2) if pref(L,a)<=eps)
        print(f"  load {a}: eps={eps:g}  paper bound -> L={Lb}   exact -> L={Le}")
