import os
from scipy.special import comb
from decimal import Decimal, getcontext

def aep(p, n, eps):
    p = Decimal(str(p))
    q = 1-p
    eps = Decimal(str(eps))
    two = Decimal('2')
    entropy = -p*p.ln()/two.ln()-q*q.ln()/two.ln()
    lp = 2**(-n*(entropy+eps))
    hp = 2**(-n*(entropy-eps))
    typ_num = Decimal(0)
    total_num = Decimal(0)
    total_ratio = Decimal(0)
    res = list()
    for k in range(n+1):
        count = Decimal(int(comb(n, k)))
        prob = p**k * q**(n-k)
        ratio = count * prob
        total_num += count
        if lp <= prob and prob <= hp:
            res.append((k, count, prob, ratio))
            typ_num += count
            total_ratio += ratio
    if not os.path.exists('aep_out'):
        os.mkdir('aep_out')
    with open('aep_out\output_{:d}.txt'.format(n), 'w') as f:
        f.write('n = {:s}, eps = {:s}\n'.format(str(n), str(eps)))
        f.write('The typical set:\n')
        f.write('probability:\t{:g}\n'.format(float(str(total_ratio))))
        f.write('count:\t{:g}\n'.format(int(str(typ_num))))
        f.write('ratio:\t{:g}\n'.format(float(str(typ_num/total_num))))
        f.write('Detail:\n')
        for r in res:
            f.write('{:d}\t{:g}\t{:g}\t{:g}\n'.format(r[0], float(str(r[1])), float(str(r[2])), float(str(r[3]))))

if __name__ == '__main__':
    d_context = getcontext()
    d_context.prec = 1000
    for n in [25, 50, 100, 200, 500, 1000]:
        print('n = {:d}'.format(n))
        aep(0.6, n, 0.05)
